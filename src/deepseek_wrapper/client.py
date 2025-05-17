from typing import AsyncGenerator, Dict, List, Optional, Union, Any, Callable, Tuple
from .config import DeepSeekConfig
from .errors import DeepSeekAPIError, DeepSeekAuthError
from .utils import retry
from .tools import Tool, ToolRegistry
import httpx
import json
import logging
import re
import asyncio

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
    
    def clear_tool_caches(self) -> None:
        """Clear the caches for all registered tools.
        
        This is useful when you want to ensure fresh results from tool calls.
        """
        self._tool_registry.clear_all_caches()
        logger.info("Cleared all tool caches")
    
    def clear_tool_cache(self, tool_name: str) -> bool:
        """Clear the cache for a specific tool.
        
        Args:
            tool_name: The name of the tool whose cache to clear
            
        Returns:
            True if the tool was found and cache cleared, False otherwise
        """
        tool = self._tool_registry.get_tool(tool_name)
        if tool:
            tool.clear_cache()
            logger.info(f"Cleared cache for tool: {tool_name}")
            return True
        else:
            logger.warning(f"Tool not found: {tool_name}")
            return False
    
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
            "model": kwargs.get("model", self.config.default_model),
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
            error_data = e.response.json() if e.response.headers.get("content-type") == "application/json" else {"error": str(e)}
            raise DeepSeekAPIError(f"API request failed: {error_data}")
        except Exception as e:
            raise DeepSeekAPIError(f"Unknown error: {str(e)}")

    @retry()
    async def async_generate_text(self, prompt: str, **kwargs) -> str:
        """Asynchronously generate text from DeepSeek."""
        payload = {
            "model": kwargs.get("model", self.config.default_model),
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
            error_data = e.response.json() if e.response.headers.get("content-type") == "application/json" else {"error": str(e)}
            raise DeepSeekAPIError(f"API request failed: {error_data}")
        except Exception as e:
            raise DeepSeekAPIError(f"Unknown error: {str(e)}")

    @retry()
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Synchronously generate chat completion from DeepSeek."""
        payload = {
            "model": kwargs.get("model", self.config.default_model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            **{k: v for k, v in kwargs.items() if k not in ("model", "messages", "max_tokens")},
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
            error_data = e.response.json() if e.response.headers.get("content-type") == "application/json" else {"error": str(e)}
            raise DeepSeekAPIError(f"API request failed: {error_data}")
        except Exception as e:
            raise DeepSeekAPIError(f"Unknown error: {str(e)}")

    @retry()
    async def async_chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Asynchronously generate chat completion from DeepSeek."""
        payload = {
            "model": kwargs.get("model", self.config.default_model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            **{k: v for k, v in kwargs.items() if k not in ("model", "messages", "max_tokens")},
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
            error_data = e.response.json() if e.response.headers.get("content-type") == "application/json" else {"error": str(e)}
            raise DeepSeekAPIError(f"API request failed: {error_data}")
        except Exception as e:
            raise DeepSeekAPIError(f"Unknown error: {str(e)}")
    
    def chat_completion_with_tools(self, messages: List[Dict[str, str]], 
                               tools: Optional[List[Tool]] = None, 
                               tool_choice: str = "auto", 
                               max_tools_to_use: int = 3,
                               **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        """Synchronously generate chat completion with tool usage from DeepSeek.
        
        This is a workaround function that uses a naive approach to tool/function calling
        by adding instructions to the system message. It will be replaced once DeepSeek
        adds native function calling support.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of specific tools to use, otherwise uses registered tools
            tool_choice: "auto" to let AI decide or "none" to disable tool use
            max_tools_to_use: Maximum number of tool calls to process in one turn
            **kwargs: Additional arguments to pass to the completion API
            
        Returns:
            A tuple containing (assistant_message, tool_usage_list)
        """
        if not self._tool_registry.list_tools() and not tools:
            # If no tools registered and none provided, just do a normal chat completion
            return self.chat_completion(messages, **kwargs), []
        
        # Make a copy of the messages to avoid modifying the original
        messages_copy = messages.copy()
        
        # Determine which tools to use
        if tools:
            # Use only specifically provided tools
            available_tools = [
                self._tool_registry.get_tool(t.name) if isinstance(t, str) else t
                for t in tools
            ]
            # Filter out any None values from tools that weren't found
            available_tools = [t for t in available_tools if t]
        else:
            # Use all registered tools
            available_tools = self._tool_registry.get_all_tools()
            
        if not available_tools:
            # No tools available, just do a normal chat completion
            return self.chat_completion(messages, **kwargs), []
        
        # Use the tool schemas
        function_defs = []
        for tool in available_tools:
            schema = tool.get_schema()
            if schema:
                function_defs.append(schema)
                
        # Add tool information to system message
        system_msg = None
        for i, msg in enumerate(messages_copy):
            if msg.get("role") == "system":
                system_msg = msg
                break
                
        if system_msg:
            # Append to existing system message
            tool_instructions = self._format_tool_instructions(function_defs)
            system_msg["content"] += f"\n\n{tool_instructions}"
        else:
            # Create new system message with tool instructions
            tool_instructions = self._format_tool_instructions(function_defs)
            messages_copy.insert(0, {
                "role": "system", 
                "content": tool_instructions
            })
            
        all_tool_calls = []
        response_content = None
        
        if tool_choice == "none":
            # User requested no tool usage
            return self.chat_completion(messages_copy, **kwargs), []
        
        # Make the chat completion call with the modified messages
        response = self.chat_completion(
            messages_copy,
            model=kwargs.get("model", self.config.default_model),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1024),
            **{k: v for k, v in kwargs.items() if k not in ("model", "temperature", "max_tokens")},
        )
        
        response_content = response
        
        # Parse the response for tool calls
        tool_calls = self._parse_tool_calls(response_content)
        
        # Execute tools and get results
        if tool_calls and len(tool_calls) <= max_tools_to_use:
            all_tool_calls.extend(tool_calls)
            
            # Execute the tool calls
            tool_results = self._execute_tool_calls(tool_calls)
            
            # Format the tool results as a new message
            tool_result_msg = self._format_tool_results_as_message(tool_results)
            
            # Add the original assistant response and tool results to the messages
            messages_copy.append({"role": "assistant", "content": response_content})
            messages_copy.append(tool_result_msg)
            
            # Make another call to get the final assistant response
            final_response = self.chat_completion(
                messages_copy,
                model=kwargs.get("model", self.config.default_model),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
                **{k: v for k, v in kwargs.items() if k not in ("model", "temperature", "max_tokens")},
            )
            
            # Update the response content to the final response
            response_content = final_response
            
        return response_content, all_tool_calls

    async def async_chat_completion_with_tools(self, messages: List[Dict[str, str]], 
                                          tools: Optional[List[Tool]] = None, 
                                          tool_choice: str = "auto", 
                                          max_tools_to_use: int = 3,
                                          **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        """Asynchronously generate chat completion with tool usage from DeepSeek.
        
        This is a workaround function that uses a naive approach to tool/function calling
        by adding instructions to the system message. It will be replaced once DeepSeek
        adds native function calling support.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of specific tools to use, otherwise uses registered tools
            tool_choice: "auto" to let AI decide or "none" to disable tool use
            max_tools_to_use: Maximum number of tool calls to process in one turn
            **kwargs: Additional arguments to pass to the completion API
            
        Returns:
            A tuple containing (assistant_message, tool_usage_list)
        """
        if not self._tool_registry.list_tools() and not tools:
            # If no tools registered and none provided, just do a normal chat completion
            return await self.async_chat_completion(messages, **kwargs), []
        
        # Make a copy of the messages to avoid modifying the original
        messages_copy = messages.copy()
        
        # Determine which tools to use
        if tools:
            # Use only specifically provided tools
            available_tools = [
                self._tool_registry.get_tool(t.name) if isinstance(t, str) else t
                for t in tools
            ]
            # Filter out any None values from tools that weren't found
            available_tools = [t for t in available_tools if t]
        else:
            # Use all registered tools
            available_tools = self._tool_registry.get_all_tools()
            
        if not available_tools:
            # No tools available, just do a normal chat completion
            return await self.async_chat_completion(messages, **kwargs), []
        
        # Use the tool schemas
        function_defs = []
        for tool in available_tools:
            schema = tool.get_schema()
            if schema:
                function_defs.append(schema)
                
        # Add tool information to system message
        system_msg = None
        for i, msg in enumerate(messages_copy):
            if msg.get("role") == "system":
                system_msg = msg
                break
                
        if system_msg:
            # Append to existing system message
            tool_instructions = self._format_tool_instructions(function_defs)
            system_msg["content"] += f"\n\n{tool_instructions}"
        else:
            # Create new system message with tool instructions
            tool_instructions = self._format_tool_instructions(function_defs)
            messages_copy.insert(0, {
                "role": "system", 
                "content": tool_instructions
            })
            
        all_tool_calls = []
        response_content = None
        
        if tool_choice == "none":
            # User requested no tool usage
            return await self.async_chat_completion(messages_copy, **kwargs), []
        
        # Make the chat completion call with the modified messages
        response = await self.async_chat_completion(
            messages_copy,
            model=kwargs.get("model", self.config.default_model),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1024),
            **{k: v for k, v in kwargs.items() if k not in ("model", "temperature", "max_tokens")},
        )
        
        response_content = response
        
        # Parse the response for tool calls
        tool_calls = self._parse_tool_calls(response_content)
        
        # Execute tools and get results
        if tool_calls and len(tool_calls) <= max_tools_to_use:
            all_tool_calls.extend(tool_calls)
            
            # Execute the tool calls
            tool_results = self._execute_tool_calls(tool_calls)
            
            # Format the tool results as a new message
            tool_result_msg = self._format_tool_results_as_message(tool_results)
            
            # Add the original assistant response and tool results to the messages
            messages_copy.append({"role": "assistant", "content": response_content})
            messages_copy.append(tool_result_msg)
            
            # Make another call to get the final assistant response
            final_response = await self.async_chat_completion(
                messages_copy,
                model=kwargs.get("model", self.config.default_model),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1024),
                **{k: v for k, v in kwargs.items() if k not in ("model", "temperature", "max_tokens")},
            )
            
            # Update the response content to the final response
            response_content = final_response
            
        return response_content, all_tool_calls

    async def async_chat_completion_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat completion from DeepSeek.
        
        Returns:
            AsyncGenerator that yields content chunks as they arrive.
        """
        # Manual retry implementation for the generator
        attempts = 0
        max_attempts = kwargs.pop("max_retries", self.config.max_retries)
        delay = 1.0
        backoff_factor = 2.0
        
        while attempts < max_attempts:
            try:
                async for chunk in self._async_chat_completion_stream_impl(messages, **kwargs):
                    yield chunk
                return
            except Exception as e:
                attempts += 1
                if attempts >= max_attempts:
                    logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                    raise
                
                logger.warning(f"Attempt {attempts} failed: {str(e)}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
                delay *= backoff_factor
        
        # This should never be reached but adding as a safeguard
        raise RuntimeError(f"Failed after {max_attempts} attempts")
        
    async def _async_chat_completion_stream_impl(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Internal implementation of streaming chat completion."""
        payload = {
            "model": kwargs.get("model", self.config.default_model),
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

    def _format_tool_instructions(self, function_defs: List[Dict[str, Any]]) -> str:
        """Format tool instructions for the system message.
        
        Args:
            function_defs: List of function definitions from tool schemas
            
        Returns:
            String with formatted tool instructions
        """
        if not function_defs:
            return ""
            
        instructions = (
            "\nYou have access to the following tools:\n" + 
            json.dumps(function_defs, indent=2) + 
            "\n\nTo use a tool, respond with a message that includes either:"
            "\n1. JSON with the tool name and arguments: ```json\n{\"name\": \"tool_name\", \"arguments\": {\"arg1\": \"value1\"}}\n```"
            "\n2. A function-like syntax: tool_name(arg1=\"value1\", arg2=\"value2\")"
            "\n\nIf you need to use multiple tools, specify them clearly one after another."
        )
        
        return instructions 

    def set_default_model(self, model_name: str) -> bool:
        """Change the default model to use for requests.
        
        Args:
            model_name: The name of the model to use
            
        Returns:
            True if successful, False if the model is not supported
        """
        if model_name in self.config.get_available_models():
            self.config.set_default_model(model_name)
            return True
        return False
    
    def get_default_model(self) -> str:
        """Get the current default model.
        
        Returns:
            Current default model name
        """
        return self.config.default_model
    
    def get_available_models(self) -> List[str]:
        """Get a list of available models.
        
        Returns:
            List of available model names
        """
        return self.config.get_available_models() 