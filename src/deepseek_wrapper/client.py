from typing import AsyncGenerator, Dict, List, Optional, Union, Any, Callable, Tuple
from .config import DeepSeekConfig
from .errors import DeepSeekAPIError, DeepSeekAuthError
from .utils import retry
from .tools import Tool, ToolRegistry
import httpx
import json
import logging
import re

logger = logging.getLogger(__name__)

class DeepSeekClient:
    """Client for interacting with DeepSeek LLM API."""
    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or DeepSeekConfig()
        self._client = httpx.Client(timeout=self.config.timeout)
        self._async_client = httpx.AsyncClient(timeout=self.config.timeout)
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        self._tool_registry = ToolRegistry()
        
    def __del__(self):
        """Cleanup resources when the client is garbage collected."""
        self.close()

    def close(self):
        """Close the synchronous client."""
        if hasattr(self, '_client') and self._client:
            self._client.close()

    async def aclose(self):
        """Close the asynchronous client."""
        if hasattr(self, '_async_client') and self._async_client:
            await self._async_client.aclose()

    def _update_headers(self):
        """Update headers if API key changes."""
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool with this client.
        
        Args:
            tool: The tool instance to register
        """
        self._tool_registry.register(tool)
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool by name.
        
        Args:
            tool_name: The name of the tool to unregister
        """
        self._tool_registry.unregister(tool_name)
        logger.info(f"Unregistered tool: {tool_name}")
    
    def list_tools(self) -> List[str]:
        """List all registered tool names.
        
        Returns:
            List of tool names
        """
        return self._tool_registry.list_tools()
    
    def _get_tools_as_functions(self) -> List[Dict[str, Any]]:
        """Get registered tools as DeepSeek function schemas.
        
        Returns:
            List of function definition dictionaries
        """
        return self._tool_registry.get_schemas()
    
    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Parse DeepSeek model responses for tool calls.
        
        This is a workaround until DeepSeek's API has native function calling.
        It handles common formats of tool/function calling in the AI's response.
        
        Args:
            content: The raw text response from the model
            
        Returns:
            List of parsed tool calls with name and arguments
        """
        tool_calls = []
        
        # Pattern 1: JSON format - {"name": "tool_name", "arguments": {...}}
        json_pattern = r'```json\s*({[^`]*})\s*```'
        json_matches = re.findall(json_pattern, content, re.DOTALL)
        
        for match in json_matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and "name" in data and "arguments" in data:
                    tool_calls.append({
                        "name": data["name"],
                        "arguments": data["arguments"]
                    })
            except Exception as e:
                logger.warning(f"Failed to parse JSON tool call: {e}")
        
        # Pattern 2: Function-like syntax - tool_name(arg1="value1", arg2="value2")
        func_pattern = r'(\w+)\s*\(\s*((?:[^,\)]+(?:,\s*)?)+)\)'
        func_matches = re.findall(func_pattern, content)
        
        for name, args_str in func_matches:
            # Skip if it's likely a regular function in code example
            if "```" in content:
                code_blocks = re.findall(r'```(?:\w+)?\s*([^`]+)\s*```', content, re.DOTALL)
                if any(name in block for block in code_blocks):
                    continue
            
            try:
                # Parse arguments
                args = {}
                for arg in re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\d+(?:\.\d+)?))', args_str):
                    arg_name = arg[0]
                    # Use the first non-empty value (out of the string or number matches)
                    arg_value = next((val for val in arg[1:] if val), "")
                    args[arg_name] = arg_value
                
                tool_calls.append({
                    "name": name,
                    "arguments": args
                })
            except Exception as e:
                logger.warning(f"Failed to parse function-like tool call: {e}")
        
        return tool_calls
    
    def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls and return the results.
        
        Args:
            tool_calls: List of tool calls with name and arguments
            
        Returns:
            List of tool call results
        """
        results = []
        
        for call in tool_calls:
            tool_name = call.get("name")
            args = call.get("arguments", {})
            
            logger.info(f"Executing tool call: {tool_name} with args: {args}")
            
            try:
                result = self._tool_registry.run_tool(tool_name, **args)
                results.append({
                    "tool_name": tool_name,
                    "success": result.success,
                    "result": result.content if result.success else None,
                    "error": result.error if not result.success else None
                })
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
                results.append({
                    "tool_name": tool_name,
                    "success": False,
                    "result": None,
                    "error": str(e)
                })
        
        return results
    
    def _format_tool_results_as_message(self, results: List[Dict[str, Any]]) -> Dict[str, str]:
        """Format tool results as a user message to send back to the AI.
        
        Args:
            results: List of tool call results
            
        Returns:
            Message dictionary with role and content
        """
        content_parts = ["I've executed the tools you requested. Here are the results:"]
        
        for i, result in enumerate(results):
            tool_name = result.get("tool_name", "unknown_tool")
            success = result.get("success", False)
            
            content_parts.append(f"\n\nTool: {tool_name}")
            
            if success:
                result_data = result.get("result")
                if isinstance(result_data, dict) or isinstance(result_data, list):
                    # Format JSON data nicely
                    formatted_result = json.dumps(result_data, indent=2)
                    content_parts.append(f"Status: Success\nResult:\n```json\n{formatted_result}\n```")
                else:
                    content_parts.append(f"Status: Success\nResult: {result_data}")
            else:
                error = result.get("error", "Unknown error")
                content_parts.append(f"Status: Failed\nError: {error}")
        
        return {
            "role": "user",
            "content": "\n".join(content_parts)
        }

    @retry()
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Synchronously generate text from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/completions"
        try:
            resp = self._client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["text"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e

    @retry()
    async def async_generate_text(self, prompt: str, **kwargs) -> str:
        """Asynchronously generate text from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/completions"
        try:
            resp = await self._async_client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["text"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e

    @retry()
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Synchronously get chat completion from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/chat/completions"
        try:
            resp = self._client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e

    @retry()
    async def async_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Asynchronously get chat completion from DeepSeek."""
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 256),
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens")},
        }
        url = f"{self.config.base_url}/chat/completions"
        try:
            resp = await self._async_client.post(url, json=payload, headers=self._headers)
            if resp.status_code == 401:
                raise DeepSeekAuthError("Invalid or missing API key.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] if "choices" in data else data
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e
    
    def chat_completion_with_tools(self, messages: List[Dict[str, str]], 
                               tools: Optional[List[Tool]] = None, 
                               tool_choice: str = "auto", 
                               max_tools_to_use: int = 3,
                               **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        """Synchronously get chat completion with tool use capability.
        
        This method will:
        1. Send the conversation to the model with available tools
        2. Parse any tool calls in the response
        3. Execute the requested tools
        4. Send the results back to the model
        5. Return the final response and tool usage details
        
        Args:
            messages: The conversation history
            tools: Optional list of Tool instances to register for this conversation
            tool_choice: How to use tools - "auto" (model decides), "required", "none"
            max_tools_to_use: Maximum number of tools to use in a single conversation turn
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Tuple containing (final_response, tool_usage_details)
        """
        # Register any provided tools for this conversation
        temp_tools = []
        if tools:
            for tool in tools:
                if tool.name not in self.list_tools():
                    self.register_tool(tool)
                    temp_tools.append(tool.name)
        
        try:
            # Make a copy of messages to avoid modifying the original
            conversation = messages.copy()
            
            # Check if we should expose tools to the model
            use_tools = tool_choice.lower() != "none" and len(self.list_tools()) > 0
            tool_usage = []
            
            if use_tools:
                # Add special system message about available tools if not already present
                has_tool_instructions = False
                for msg in conversation:
                    if msg.get("role") == "system" and "available tools" in msg.get("content", "").lower():
                        has_tool_instructions = True
                        break
                
                if not has_tool_instructions:
                    # Find existing system message or create a new one
                    system_idx = next((i for i, m in enumerate(conversation) 
                                     if m.get("role") == "system"), None)
                    
                    tool_schemas = self._get_tools_as_functions()
                    tools_instruction = (
                        "\n\nYou have access to the following tools:\n" + 
                        json.dumps(tool_schemas, indent=2) + 
                        "\n\nTo use a tool, respond with a message that includes either:"
                        "\n1. JSON with the tool name and arguments: ```json\n{\"name\": \"tool_name\", \"arguments\": {\"arg1\": \"value1\"}}\n```"
                        "\n2. A function-like syntax: tool_name(arg1=\"value1\", arg2=\"value2\")"
                        "\n\nIf you need to use multiple tools, specify them clearly one after another."
                    )
                    
                    if system_idx is not None:
                        # Append to existing system message
                        conversation[system_idx]["content"] += tools_instruction
                    else:
                        # Add new system message at the beginning
                        conversation.insert(0, {
                            "role": "system",
                            "content": "You are a helpful assistant with access to tools." + tools_instruction
                        })
            
            # Maximum conversation turns for tool usage
            max_turns = 3
            turn = 0
            
            while turn < max_turns:
                turn += 1
                
                # Get response from model
                logger.info(f"Getting model response (turn {turn}/{max_turns})")
                response = self.chat_completion(conversation, **kwargs)
                
                # Check if tool usage is requested in the response
                if use_tools:
                    tool_calls = self._parse_tool_calls(response)
                    
                    if not tool_calls:
                        # No tools requested, return the response
                        logger.info("No tool calls found, returning response")
                        return response, tool_usage
                    
                    # Limit the number of tools to use
                    limited_calls = tool_calls[:max_tools_to_use]
                    
                    # Track tool usage
                    tool_usage.extend([{
                        "turn": turn, 
                        "tool": call["name"], 
                        "arguments": call["arguments"]
                    } for call in limited_calls])
                    
                    # Add assistant's response to conversation
                    conversation.append({"role": "assistant", "content": response})
                    
                    # Execute tools
                    logger.info(f"Executing {len(limited_calls)} tool calls")
                    tool_results = self._execute_tool_calls(limited_calls)
                    
                    # Format results and add to conversation
                    tool_response = self._format_tool_results_as_message(tool_results)
                    conversation.append(tool_response)
                    
                    # If this is the last turn, make one final call to get the model's response
                    if turn == max_turns:
                        logger.info("Final turn reached, getting final response")
                        final_response = self.chat_completion(conversation, **kwargs)
                        return final_response, tool_usage
                else:
                    # Tools not enabled, return the response
                    return response, []
            
            # Should not reach here, but just in case
            return response, tool_usage
            
        finally:
            # Clean up temporarily registered tools
            for tool_name in temp_tools:
                self.unregister_tool(tool_name)
    
    async def async_chat_completion_with_tools(self, messages: List[Dict[str, str]], 
                                          tools: Optional[List[Tool]] = None, 
                                          tool_choice: str = "auto", 
                                          max_tools_to_use: int = 3,
                                          **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        """Asynchronously get chat completion with tool use capability.
        
        This method will:
        1. Send the conversation to the model with available tools
        2. Parse any tool calls in the response
        3. Execute the requested tools
        4. Send the results back to the model
        5. Return the final response and tool usage details
        
        Args:
            messages: The conversation history
            tools: Optional list of Tool instances to register for this conversation
            tool_choice: How to use tools - "auto" (model decides), "required", "none"
            max_tools_to_use: Maximum number of tools to use in a single conversation turn
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Tuple containing (final_response, tool_usage_details)
        """
        # Register any provided tools for this conversation
        temp_tools = []
        if tools:
            for tool in tools:
                if tool.name not in self.list_tools():
                    self.register_tool(tool)
                    temp_tools.append(tool.name)
        
        try:
            # Make a copy of messages to avoid modifying the original
            conversation = messages.copy()
            
            # Check if we should expose tools to the model
            use_tools = tool_choice.lower() != "none" and len(self.list_tools()) > 0
            tool_usage = []
            
            if use_tools:
                # Add special system message about available tools if not already present
                has_tool_instructions = False
                for msg in conversation:
                    if msg.get("role") == "system" and "available tools" in msg.get("content", "").lower():
                        has_tool_instructions = True
                        break
                
                if not has_tool_instructions:
                    # Find existing system message or create a new one
                    system_idx = next((i for i, m in enumerate(conversation) 
                                     if m.get("role") == "system"), None)
                    
                    tool_schemas = self._get_tools_as_functions()
                    tools_instruction = (
                        "\n\nYou have access to the following tools:\n" + 
                        json.dumps(tool_schemas, indent=2) + 
                        "\n\nTo use a tool, respond with a message that includes either:"
                        "\n1. JSON with the tool name and arguments: ```json\n{\"name\": \"tool_name\", \"arguments\": {\"arg1\": \"value1\"}}\n```"
                        "\n2. A function-like syntax: tool_name(arg1=\"value1\", arg2=\"value2\")"
                        "\n\nIf you need to use multiple tools, specify them clearly one after another."
                    )
                    
                    if system_idx is not None:
                        # Append to existing system message
                        conversation[system_idx]["content"] += tools_instruction
                    else:
                        # Add new system message at the beginning
                        conversation.insert(0, {
                            "role": "system",
                            "content": "You are a helpful assistant with access to tools." + tools_instruction
                        })
            
            # Maximum conversation turns for tool usage
            max_turns = 3
            turn = 0
            
            while turn < max_turns:
                turn += 1
                
                # Get response from model
                logger.info(f"Getting model response (turn {turn}/{max_turns})")
                response = await self.async_chat_completion(conversation, **kwargs)
                
                # Check if tool usage is requested in the response
                if use_tools:
                    tool_calls = self._parse_tool_calls(response)
                    
                    if not tool_calls:
                        # No tools requested, return the response
                        logger.info("No tool calls found, returning response")
                        return response, tool_usage
                    
                    # Limit the number of tools to use
                    limited_calls = tool_calls[:max_tools_to_use]
                    
                    # Track tool usage
                    tool_usage.extend([{
                        "turn": turn, 
                        "tool": call["name"], 
                        "arguments": call["arguments"]
                    } for call in limited_calls])
                    
                    # Add assistant's response to conversation
                    conversation.append({"role": "assistant", "content": response})
                    
                    # Execute tools
                    logger.info(f"Executing {len(limited_calls)} tool calls")
                    tool_results = self._execute_tool_calls(limited_calls)
                    
                    # Format results and add to conversation
                    tool_response = self._format_tool_results_as_message(tool_results)
                    conversation.append(tool_response)
                    
                    # If this is the last turn, make one final call to get the model's response
                    if turn == max_turns:
                        logger.info("Final turn reached, getting final response")
                        final_response = await self.async_chat_completion(conversation, **kwargs)
                        return final_response, tool_usage
                else:
                    # Tools not enabled, return the response
                    return response, []
            
            # Should not reach here, but just in case
            return response, tool_usage
            
        finally:
            # Clean up temporarily registered tools
            for tool_name in temp_tools:
                self.unregister_tool(tool_name)

    @retry()
    async def async_chat_completion_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion from DeepSeek.
        
        Returns:
            AsyncGenerator that yields content chunks as they arrive.
        """
        payload = {
            "model": kwargs.get("model", "deepseek-chat"),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 256),
            "stream": True,  # Enable streaming
            **{k: v for k, v in kwargs.items() if k not in ("model", "max_tokens", "stream")},
        }
        url = f"{self.config.base_url}/chat/completions"
        logger.debug(f"Streaming request to DeepSeek API: URL={url}, payload={json.dumps(payload, indent=2)}")
        try:
            async with self._async_client.stream('POST', url, json=payload, headers=self._headers) as resp:
                if resp.status_code == 401:
                    raise DeepSeekAuthError("Invalid or missing API key.")
                logger.debug(f"DeepSeek API response status: {resp.status_code}")
                logger.debug(f"DeepSeek API response headers: {resp.headers}")
                resp.raise_for_status()
                buffer = ""
                async for chunk in resp.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            return
                        try:
                            chunk_data = json.loads(data)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content')
                                if content:
                                    yield content
                        except Exception as e:
                            logger.error(f"Error processing chunk: {e}")
                            continue
        except httpx.HTTPStatusError as e:
            raise DeepSeekAPIError(f"HTTP error: {e.response.status_code} {e.response.text}") from e
        except DeepSeekAuthError:
            raise
        except Exception as e:
            raise DeepSeekAPIError(str(e)) from e 