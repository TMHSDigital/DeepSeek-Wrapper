from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from deepseek_wrapper import DeepSeekClient, DeepSeekConfig
import os
from datetime import datetime
import markdown as md
import json
import asyncio

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "supersecret"))
templates = Jinja2Templates(directory="src/deepseek_wrapper/templates")
app.mount("/static", StaticFiles(directory="src/deepseek_wrapper/static"), name="static")

client = DeepSeekClient()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '../../uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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
        response = await client.async_chat_completion(history)
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
        response = await client.async_generate_text(prompt)
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

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), request: Request = None):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    # Add file message to chat history if session is available
    if request is not None:
        history = request.session.get("history", [])
        history.append({
            "role": "user",
            "content": "",  # Add empty content field for API compatibility
            "file": {"filename": file.filename, "content_type": file.content_type},
            "timestamp": now_str()
        })
        request.session["history"] = history
    return JSONResponse({"filename": file.filename, "content_type": file.content_type})

@app.get("/chat/stream")
async def chat_stream(request: Request, user_message: str = None):
    """Stream chat responses using Server-Sent Events."""
    try:
        if not user_message:
            history_check = request.session.get("history", [])
            if history_check and history_check[-1]["role"] == "user":
                user_message = history_check[-1]["content"]
            else:
                return JSONResponse({"error": "No message provided in query parameters"}, status_code=400)
        
        history = request.session.get("history", [])
        
        user_msg = {"role": "user", "content": user_message, "timestamp": now_str()}
        history.append(user_msg)
        
        request.session["history"] = history
        
        async def event_generator():
            yield f"data: {json.dumps({'type': 'user_msg_received', 'message': user_msg})}\n\n"
            await asyncio.sleep(0.1)
            
            assistant_msg = {"role": "assistant", "content": "", "timestamp": now_str()}
            yield f"data: {json.dumps({'type': 'assistant_msg_start', 'message': assistant_msg})}\n\n"
            
            try:
                collected_content = []
                async for content_chunk in client.async_chat_completion_stream(history):
                    collected_content.append(content_chunk)
                    assistant_msg["content"] = ''.join(collected_content)
                    
                    yield f"data: {json.dumps({'type': 'content_chunk', 'chunk': content_chunk})}\n\n"
                    
                complete_msg = {"role": "assistant", "content": ''.join(collected_content), "timestamp": now_str()}
                history.append(complete_msg)
                request.session["history"] = history
                
                yield f"data: {json.dumps({'type': 'complete', 'message': complete_msg})}\n\n"
            except Exception as e:
                error_msg = str(e)
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
                
                error_response = f"Error: {error_msg}"
                history.append({"role": "assistant", "content": error_response, "timestamp": now_str()})
                request.session["history"] = history
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500) 