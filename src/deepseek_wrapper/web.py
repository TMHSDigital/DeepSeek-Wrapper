from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from deepseek_wrapper import DeepSeekClient, DeepSeekConfig
import os
from datetime import datetime
import markdown as md

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "supersecret"))
templates = Jinja2Templates(directory="src/deepseek_wrapper/templates")
app.mount("/static", StaticFiles(directory="src/deepseek_wrapper/static"), name="static")

client = DeepSeekClient()

def now_str():
    return datetime.now().strftime("%H:%M:%S")

def render_history(history):
    # Render assistant message content as HTML using markdown
    rendered = []
    for msg in history:
        msg = msg.copy()
        if msg["role"] == "assistant":
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