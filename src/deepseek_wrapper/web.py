from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from deepseek_wrapper import DeepSeekClient, DeepSeekConfig
from deepseek_wrapper.utils import get_realtime_info
import os
from datetime import datetime
import markdown as md
import json
import asyncio
import traceback
import logging
import io
from typing import Optional
try:
    import docx
except ImportError:
    docx = None
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
from deepseek_wrapper.utils.response_processor import extract_final_answer, process_model_response
from deepseek_wrapper.config_manager import get_config_value, update_config, load_config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Determine base directory for resources
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "supersecret"))
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize client with config validation
client = None
try:
    client_config = DeepSeekConfig()
    # Log the API configuration (masked for security)
    api_key = client_config.api_key
    masked_key = api_key[:4] + "****" + api_key[-4:] if api_key and len(api_key) > 8 else "****"
    logger.info(f"DeepSeek API Configuration: URL={client_config.base_url}, API Key={masked_key}")
    client = DeepSeekClient(client_config)
    
    # Register built-in tools
    from deepseek_wrapper.tools import DateTimeTool, CalculatorTool, WebSearchTool, WeatherTool, EmailTool
    
    # Register core tools
    client.register_tool(DateTimeTool())
    client.register_tool(CalculatorTool())
    
    # Register tools that require API keys (if configured)
    if os.getenv("SEARCH_API_KEY"):
        client.register_tool(WebSearchTool())
    if os.getenv("OPENWEATHERMAP_API_KEY"):
        client.register_tool(WeatherTool())
    
    # Register email tool (in dry run mode by default for safety)
    # Set EMAIL_DRY_RUN=false to enable actual email sending
    os.environ.setdefault("EMAIL_DRY_RUN", "true")
    if os.getenv("EMAIL_USERNAME") and os.getenv("EMAIL_PASSWORD"):
        email_tool = EmailTool(
            template_dir=os.path.abspath("./email_templates")
        )
        client.register_tool(email_tool)
        logger.info(f"Email tool registered with template directory: {email_tool.template_dir}")
        logger.info(f"Email tool in dry run mode: {os.getenv('EMAIL_DRY_RUN')=='true'}")
        logger.info(f"Available email templates: {list(email_tool.templates.keys())}")
    else:
        logger.info("Email tool not registered - missing EMAIL_USERNAME or EMAIL_PASSWORD")
    
    # Log registered tools
    logger.info(f"Registered tools: {client.list_tools()}")
except Exception as e:
    logger.error(f"Failed to initialize DeepSeek client: {e}")
    raise

UPLOAD_DIR = os.path.join(BASE_DIR, '../uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

MAX_FILE_CHARS = 4000  # Limit injected text for context

# Function to update .env file with API keys
def update_env_file(api_keys):
    env_path = os.path.join(BASE_DIR, '../.env')
    
    # Read existing .env content
    env_content = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_content[key.strip()] = value.strip()
    
    # Update with new values
    env_content.update(api_keys)
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    return True

@app.post("/save_api_keys")
async def save_api_keys(request: Request):
    try:
        data = await request.json()
        
        # Validate data
        api_keys = {}
        for key, value in data.items():
            if key and value and isinstance(value, str):
                api_keys[key] = value.strip()
        
        # Update .env file
        success = update_env_file(api_keys)
        
        if success:
            # Optionally reload environment variables for current process
            for key, value in api_keys.items():
                os.environ[key] = value
                
            # Register tools based on new API keys
            if "SEARCH_API_KEY" in api_keys and api_keys["SEARCH_API_KEY"]:
                from deepseek_wrapper.tools import WebSearchTool
                client.register_tool(WebSearchTool())
                
            if "OPENWEATHERMAP_API_KEY" in api_keys and api_keys["OPENWEATHERMAP_API_KEY"]:
                from deepseek_wrapper.tools import WeatherTool
                client.register_tool(WeatherTool())
                
            if ("EMAIL_SMTP_SERVER" in api_keys and "EMAIL_USERNAME" in api_keys and 
                "EMAIL_PASSWORD" in api_keys):
                from deepseek_wrapper.tools import EmailTool
                email_tool = EmailTool(template_dir=os.path.abspath("./email_templates"))
                client.register_tool(email_tool)
            
            logger.info(f"Updated API keys and registered tools: {client.list_tools()}")
            return JSONResponse({"success": True, "message": "API keys saved successfully"})
        else:
            return JSONResponse({"success": False, "error": "Failed to update .env file"}, status_code=500)
    except Exception as e:
        logger.error(f"Error saving API keys: {str(e)}", exc_info=True)
        return JSONResponse(
            {"success": False, "error": str(e)}, 
            status_code=500
        )

# Create an alias endpoint for compatibility
@app.post("/api/save-api-keys")
async def save_api_keys_compat(request: Request):
    return await save_api_keys(request)

def now_str():
    return datetime.now().strftime("%H:%M:%S")

def is_image(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))

def render_history(history):
    # Render assistant message content as HTML using markdown
    rendered = []
    for msg in history:
        msg = msg.copy()
        # Ensure all messages have a content field (required by DeepSeek API)
        if "content" not in msg:
            msg["content"] = ""
            
        if msg.get("file"):
            # File upload message
            fname = msg["file"]["filename"]
            ctype = msg["file"]["content_type"]
            if is_image(fname):
                msg["content_html"] = f'<img src="/uploads/{fname}" alt="{fname}" style="max-width:200px;max-height:120px;" />'
            else:
                msg["content_html"] = f'<a href="/uploads/{fname}" download>{fname}</a> <span style="font-size:0.9em;color:#888">({ctype})</span>'
        elif msg["role"] == "assistant":
            msg["content_html"] = md.markdown(msg["content"], extensions=["extra", "sane_lists"])
        else:
            msg["content_html"] = msg["content"]
        rendered.append(msg)
    return rendered

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    history = request.session.get("history", [])
    rendered = render_history(history)
    return templates.TemplateResponse("chat.html", {"request": request, "messages": rendered, "error": None, "loading": False})

@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, user_message: str = Form(...)):
    history = request.session.get("history", [])
    history.append({"role": "user", "content": user_message, "timestamp": now_str()})
    error = None
    loading = True
    try:
        # Add real-time data to the conversation
        formatted_history = []
        
        # Add system message with real-time data
        realtime_data = get_realtime_info()
        default_system_prompt = (
            "You are a helpful AI assistant with real-time awareness. "
            "You can access current date and time information when needed.\n\n"
            f"Current date and time information:\n{realtime_data}"
        )
        formatted_history.append({"role": "system", "content": default_system_prompt})
        
        # Add user messages
        for msg in history:
            if "role" in msg and "content" in msg and "file" not in msg:
                formatted_history.append({"role": msg["role"], "content": msg["content"]})
        
        # Get the extract_answer_only setting
        extract_answer_only = get_config_value("extract_answer_only")
        current_model = client.get_default_model()
        
        # Use tools if available
        if client.list_tools():
            # Use function calling with tools
            logger.info(f"Using chat completion with tools: {client.list_tools()}")
            response, tool_usage = await client.async_chat_completion_with_tools(
                formatted_history,
                max_tools_to_use=3,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1024
            )
            
            # Process the response based on settings
            response = process_model_response(response, current_model, extract_answer_only)
            
            # Log tool usage if any
            if tool_usage:
                logger.info(f"Tools used in conversation: {tool_usage}")
        else:
            # Fall back to regular chat completion
            logger.info("Using regular chat completion (no tools registered)")
            response = await client.async_chat_completion(formatted_history)
            
            # Process the response based on settings
            response = process_model_response(response, current_model, extract_answer_only)
            
        loading = False
    except Exception as e:
        response = f"Error: {e}"
        error = str(e)
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        loading = False
    history.append({"role": "assistant", "content": response, "timestamp": now_str()})
    request.session["history"] = history
    rendered = render_history(history)
    return templates.TemplateResponse("chat.html", {"request": request, "messages": rendered, "error": error, "loading": loading})

@app.post("/completions", response_class=HTMLResponse)
async def completions(request: Request, prompt: str = Form(...)):
    history = request.session.get("history", [])
    error = None
    loading = True
    try:
        # Enhance prompt with real-time information
        realtime_data = get_realtime_info()
        enhanced_prompt = (
            "You have access to current date and time information:\n\n"
            f"{realtime_data}\n\n"
            f"User prompt: {prompt}"
        )
        response = await client.async_generate_text(enhanced_prompt)
        loading = False
    except Exception as e:
        response = f"Error: {e}"
        error = str(e)
        loading = False
    history.append({"role": "user", "content": prompt, "timestamp": now_str()})
    history.append({"role": "assistant", "content": response, "timestamp": now_str()})
    request.session["history"] = history
    rendered = render_history(history)
    return templates.TemplateResponse("chat.html", {"request": request, "messages": rendered, "error": error, "loading": loading})

@app.post("/reset", response_class=HTMLResponse)
async def reset(request: Request):
    request.session["history"] = []
    return RedirectResponse("/", status_code=303)

def extract_text_from_file(file_path, content_type):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == '.pdf' and PyPDF2:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return '\n'.join(page.extract_text() or '' for page in reader.pages)
        elif ext == '.docx' and docx:
            doc = docx.Document(file_path)
            return '\n'.join(p.text for p in doc.paragraphs)
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        return None

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), request: Request = None):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    extracted_text = extract_text_from_file(file_location, file.content_type)
    # Add file message to chat history if session is available
    if request is not None:
        history = request.session.get("history", [])
        history.append({
            "role": "user",
            "content": "",  # Add empty content field for API compatibility
            "file": {"filename": file.filename, "content_type": file.content_type},
            "timestamp": now_str()
        })
        # Inject extracted text as a user message if available
        if extracted_text:
            truncated = extracted_text[:MAX_FILE_CHARS]
            history.append({
                "role": "user",
                "content": f"[File: {file.filename}]\n\n{truncated}",
                "timestamp": now_str()
            })
        request.session["history"] = history
    return JSONResponse({"filename": file.filename, "content_type": file.content_type, "extracted": bool(extracted_text)})

@app.get("/chat/stream")
async def chat_stream(request: Request, user_message: str = None, system_prompt: str = Query(None), user_name: str = Query(None), user_avatar: str = Query(None)):
    """Stream chat responses using Server-Sent Events."""
    try:
        if not user_message:
            history_check = request.session.get("history", [])
            if history_check and history_check[-1]["role"] == "user":
                user_message = history_check[-1]["content"]
            else:
                return JSONResponse({"error": "No message provided in query parameters"}, status_code=400)
        
        history = request.session.get("history", [])
        
        # Make sure history has proper message format for DeepSeek API
        formatted_history = []
        
        # Create a system prompt with real-time information if none provided
        if system_prompt:
            # Append real-time information to user-provided system prompt
            realtime_data = get_realtime_info()
            enhanced_system_prompt = f"{system_prompt}\n\nCurrent date and time information:\n{realtime_data}"
            formatted_history.append({"role": "system", "content": enhanced_system_prompt})
        else:
            # Create a default system prompt with real-time information
            realtime_data = get_realtime_info()
            default_system_prompt = (
                "You are a helpful AI assistant with real-time awareness. "
                "You can access current date and time information when needed.\n\n"
                f"Current date and time information:\n{realtime_data}"
            )
            formatted_history.append({"role": "system", "content": default_system_prompt})
            
        for msg in history:
            if "role" in msg and "content" in msg:
                # Skip file messages for the API call, as DeepSeek doesn't support them natively
                if "file" not in msg:
                    formatted_history.append({"role": msg["role"], "content": msg["content"]})
                else:
                    print(f"DEBUG: chat_stream - Skipping file message in history: {msg}")
        print(f"DEBUG: chat_stream - Formatted history for API: {json.dumps(formatted_history)}")
        # Add the current user message
        user_msg = {"role": "user", "content": user_message, "timestamp": now_str()}
        formatted_history.append({"role": "user", "content": user_message})
        # Add to session history with timestamp
        history.append(user_msg)
        request.session["history"] = history
        async def event_generator():
            print(f"DEBUG: chat_stream - Processing user message: '{user_msg['content']}'")
            yield f"data: {json.dumps({'type': 'user_msg_received', 'message': user_msg})}\n\n"
            await asyncio.sleep(0.1)
            assistant_msg = {"role": "assistant", "content": "", "timestamp": now_str()}
            yield f"data: {json.dumps({'type': 'assistant_msg_start', 'message': assistant_msg})}\n\n"
            try:
                collected_content = []
                
                # Directly iterate over the async generator without awaiting it first
                async for content_chunk in client.async_chat_completion_stream(
                    formatted_history, 
                    model=client.get_default_model(),
                    temperature=0.7,
                    max_tokens=2048
                ):
                    print(f"DEBUG: chat_stream - Received chunk from DeepSeek: '{content_chunk}'") # Critical log
                    collected_content.append(content_chunk)
                    yield f"data: {json.dumps({'type': 'content_chunk', 'chunk': content_chunk})}\n\n"
                
                # Process complete response if needed
                complete_content = ''.join(collected_content)
                
                # Get the extract_answer_only setting
                extract_answer_only = get_config_value("extract_answer_only")
                current_model = client.get_default_model()
                
                # Process the response based on settings
                processed_content = complete_content
                if extract_answer_only:
                    processed_content = process_model_response(complete_content, current_model, extract_answer_only)
                    # If the content was processed/changed, send a special message to replace everything
                    if processed_content != complete_content:
                        yield f"data: {json.dumps({'type': 'replace_content', 'content': processed_content})}\n\n"
                
                complete_msg = {"role": "assistant", "content": processed_content, "timestamp": now_str()}
                print(f"DEBUG: chat_stream - Streaming complete. Full AI content: '{complete_msg['content']}'")
                last_user_msg_idx = -1
                for i in range(len(history) - 1, -1, -1):
                    if history[i]["role"] == "user":
                        last_user_msg_idx = i
                        break
                if last_user_msg_idx != -1 and last_user_msg_idx < len(history) - 1 and history[last_user_msg_idx + 1]["role"] == "assistant":
                    history[last_user_msg_idx + 1] = complete_msg
                else:
                    history.append(complete_msg)
                request.session["history"] = history
                print(f"DEBUG: chat_stream - Session history updated (last 3): {history[-3:]}")
                yield f"data: {json.dumps({'type': 'complete', 'message': complete_msg})}\n\n"
            except Exception as e:
                error_msg = str(e)
                print(f"ERROR: chat_stream - Exception during DeepSeek stream: {error_msg}\nTraceback: {traceback.format_exc()}")
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
                error_response_for_history = {"role": "assistant", "content": f"Error communicating with AI: {error_msg}", "timestamp": now_str()}
                last_user_msg_idx = -1
                for i in range(len(history) - 1, -1, -1):
                    if history[i]["role"] == "user":
                        last_user_msg_idx = i
                        break
                if last_user_msg_idx != -1 and last_user_msg_idx < len(history) - 1 and history[last_user_msg_idx + 1]["role"] == "assistant":
                    history[last_user_msg_idx + 1] = error_response_for_history
                else:
                    history.append(error_response_for_history)
                request.session["history"] = history
                print(f"DEBUG: chat_stream - Session history updated after error (last 3): {history[-3:]}")
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        print(f"ERROR: chat_stream - Outer exception: {str(e)}\nTraceback: {traceback.format_exc()}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/key-status")
async def get_api_key_status():
    """Check which API keys are set in the environment variables."""
    status = {
        # Just check if keys exist, don't return the actual values
        "SEARCH_API_KEY": bool(os.getenv("SEARCH_API_KEY")),
        "OPENWEATHERMAP_API_KEY": bool(os.getenv("OPENWEATHERMAP_API_KEY")),
        "EMAIL_SMTP_SERVER": os.getenv("EMAIL_SMTP_SERVER", ""),
        "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME", ""),
        "EMAIL_PASSWORD": bool(os.getenv("EMAIL_PASSWORD")),
        "WOLFRAM_ALPHA_APP_ID": bool(os.getenv("WOLFRAM_ALPHA_APP_ID"))
    }
    return JSONResponse(status)

@app.get("/api/tool-status")
async def get_tool_status():
    """Get information about available tools and their status.
    
    Returns:
        JSON response with tool information including:
        - Available tools
        - For each tool: cache size, last used, etc.
    """
    if not client:
        return JSONResponse({"success": False, "error": "DeepSeek client not initialized"}, status_code=500)
    
    try:
        # Get detailed status for each tool using the new get_status method
        tool_info = client._tool_registry.get_tools_status()
        
        # Add additional information that might be useful for the UI
        for tool_status in tool_info:
            # Format last_used as relative time (e.g. "5 minutes ago")
            if "last_used_seconds_ago" in tool_status:
                seconds_ago = tool_status["last_used_seconds_ago"]
                if seconds_ago < 60:
                    tool_status["last_used_relative"] = f"{seconds_ago} seconds ago"
                elif seconds_ago < 3600:
                    tool_status["last_used_relative"] = f"{seconds_ago // 60} minutes ago"
                elif seconds_ago < 86400:
                    tool_status["last_used_relative"] = f"{seconds_ago // 3600} hours ago"
                else:
                    tool_status["last_used_relative"] = f"{seconds_ago // 86400} days ago"
            
            # Add a summary status field for UI display
            if "has_valid_credentials" in tool_status and tool_status["has_valid_credentials"]:
                tool_status["status"] = "ready"
            elif "api_key_valid" in tool_status and tool_status["api_key_valid"]:
                tool_status["status"] = "ready"
            elif "has_api_key" in tool_status and tool_status["has_api_key"]:
                tool_status["status"] = "error"
            elif tool_status["name"] in ["DateTimeTool", "CalculatorTool"]:
                # Tools that don't need API keys
                tool_status["status"] = "ready"
            else:
                tool_status["status"] = "not_configured"
        
        # Categorize tools by status
        ready_tools = [t for t in tool_info if t.get("status") == "ready"]
        error_tools = [t for t in tool_info if t.get("status") == "error"]
        not_configured_tools = [t for t in tool_info if t.get("status") == "not_configured"]
        
        # Calculate cache statistics across all tools
        total_cache_entries = sum(tool.get("cache_size", 0) for tool in tool_info)
        total_cache_hits = sum(tool.get("cache_stats", {}).get("hits", 0) for tool in tool_info)
        total_cache_misses = sum(tool.get("cache_stats", {}).get("misses", 0) for tool in tool_info)
        
        # Calculate hit ratio if there are any cache accesses
        cache_hit_ratio = 0
        if total_cache_hits + total_cache_misses > 0:
            cache_hit_ratio = total_cache_hits / (total_cache_hits + total_cache_misses)
        
        return JSONResponse({
            "success": True,
            "tools": tool_info,
            "total_tools": len(tool_info),
            "summary": {
                "ready": len(ready_tools),
                "error": len(error_tools),
                "not_configured": len(not_configured_tools)
            },
            "cache_stats": {
                "total_entries": total_cache_entries,
                "total_hits": total_cache_hits,
                "total_misses": total_cache_misses,
                "hit_ratio": cache_hit_ratio
            }
        })
    except Exception as e:
        logger.error(f"Error getting tool status: {str(e)}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/clear-caches")
async def clear_tool_caches(request: Request, tool_name: Optional[str] = None):
    """Clear caches for tools to ensure fresh results.
    
    Args:
        tool_name: Optional specific tool name to clear cache for.
                  If not provided, all tool caches will be cleared.
    
    Returns:
        JSON response indicating success and which tools were affected
    """
    if not client:
        return JSONResponse({"success": False, "error": "DeepSeek client not initialized"}, status_code=500)
    
    try:
        if tool_name:
            # Clear cache for a specific tool
            success = client.clear_tool_cache(tool_name)
            if success:
                return JSONResponse({
                    "success": True, 
                    "message": f"Cache cleared for tool: {tool_name}"
                })
            else:
                return JSONResponse({
                    "success": False, 
                    "error": f"Tool not found: {tool_name}",
                    "available_tools": client.list_tools()
                }, status_code=404)
        else:
            # Clear all caches
            client.clear_tool_caches()
            return JSONResponse({
                "success": True,
                "message": "All tool caches cleared",
                "tools_affected": client.list_tools()
            })
    except Exception as e:
        logger.error(f"Error clearing tool caches: {str(e)}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/test-weather")
async def test_weather():
    """Test endpoint for the weather tool."""
    try:
        # Check if the weather tool is registered
        from deepseek_wrapper.tools import WeatherTool
        
        # Check OpenWeatherMap API key
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return JSONResponse({
                "success": False, 
                "error": "No OpenWeatherMap API key configured", 
                "env_vars": {k: bool(v) for k, v in os.environ.items() if "API" in k}
            })
        
        # Create and test the weather tool
        weather_tool = WeatherTool()
        result = weather_tool.run(location="New York", forecast_days=1)
        
        return JSONResponse({
            "success": True,
            "result": result,
            "api_key_found": bool(api_key),
            "api_key_masked": api_key[:4] + "****" + api_key[-4:] if api_key and len(api_key) > 8 else None
        })
    except Exception as e:
        logger.error(f"Error testing weather tool: {str(e)}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@app.get("/test-weather")
async def simple_test_weather():
    """Simple test endpoint for the weather tool."""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    return JSONResponse({
        "api_key_exists": bool(api_key),
        "api_key_masked": api_key[:4] + "****" + api_key[-4:] if api_key and len(api_key) > 8 else None,
        "env_keys": {k: "exists" for k in os.environ.keys() if "API" in k or "KEY" in k}
    })

@app.get("/api/models")
async def get_models():
    """Get available models and current default model."""
    if not client:
        return JSONResponse(
            {"success": False, "error": "DeepSeek client not initialized"},
            status_code=500
        )
    
    try:
        available_models = client.get_available_models()
        current_model = client.get_default_model()
        
        return JSONResponse({
            "success": True,
            "models": available_models,
            "current_model": current_model
        })
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}", exc_info=True)
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/api/set-model")
async def set_model(request: Request):
    """Set the default model."""
    if not client:
        return JSONResponse(
            {"success": False, "error": "DeepSeek client not initialized"},
            status_code=500
        )
    
    try:
        data = await request.json()
        model_name = data.get("model")
        
        if not model_name:
            return JSONResponse(
                {"success": False, "error": "Model name is required"},
                status_code=400
            )
        
        success = client.set_default_model(model_name)
        
        if success:
            return JSONResponse({
                "success": True,
                "model": model_name
            })
        else:
            return JSONResponse(
                {"success": False, "error": f"Model '{model_name}' is not supported"},
                status_code=400
            )
    except Exception as e:
        logger.error(f"Error setting model: {str(e)}", exc_info=True)
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/api/config")
async def get_config():
    """Get the current configuration settings."""
    try:
        config = load_config()
        # Remove sensitive information
        if "api_key" in config:
            del config["api_key"]
        
        return JSONResponse({
            "success": True,
            "config": config
        })
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}", exc_info=True)
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/api/set-config")
async def set_config(request: Request):
    """Set a specific configuration value."""
    try:
        data = await request.json()
        key = data.get("key")
        value = data.get("value")
        
        if not key:
            return JSONResponse(
                {"success": False, "error": "Key is required"},
                status_code=400
            )
        
        success = update_config(key, value)
        
        if success:
            return JSONResponse({
                "success": True,
                "key": key,
                "value": value
            })
        else:
            return JSONResponse(
                {"success": False, "error": "Failed to update configuration"},
                status_code=500
            )
    except Exception as e:
        logger.error(f"Error setting config: {str(e)}", exc_info=True)
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        ) 