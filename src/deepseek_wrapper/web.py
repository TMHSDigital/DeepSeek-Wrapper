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
try:
    import docx
except ImportError:
    docx = None
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "supersecret"))
templates = Jinja2Templates(directory="src/deepseek_wrapper/templates")
app.mount("/static", StaticFiles(directory="src/deepseek_wrapper/static"), name="static")

# Initialize client with config validation
try:
    client_config = DeepSeekConfig()
    # Log the API configuration (masked for security)
    api_key = client_config.api_key
    masked_key = api_key[:4] + "****" + api_key[-4:] if api_key and len(api_key) > 8 else "****"
    logger.info(f"DeepSeek API Configuration: URL={client_config.base_url}, API Key={masked_key}")
    client = DeepSeekClient(client_config)
except Exception as e:
    logger.error(f"Failed to initialize DeepSeek client: {e}")
    raise

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '../../uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

MAX_FILE_CHARS = 4000  # Limit injected text for context

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
        
        response = await client.async_chat_completion(formatted_history)
        loading = False
    except Exception as e:
        response = f"Error: {e}"
        error = str(e)
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
                async for content_chunk in client.async_chat_completion_stream(
                    formatted_history, 
                    model="deepseek-chat",  # Explicitly set the model
                    temperature=0.7,  # Add reasonable temperature value
                    max_tokens=2048  # Increase max tokens for longer responses
                ):
                    print(f"DEBUG: chat_stream - Received chunk from DeepSeek: '{content_chunk}'") # Critical log
                    collected_content.append(content_chunk)
                    yield f"data: {json.dumps({'type': 'content_chunk', 'chunk': content_chunk})}\n\n"
                complete_msg = {"role": "assistant", "content": ''.join(collected_content), "timestamp": now_str()}
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