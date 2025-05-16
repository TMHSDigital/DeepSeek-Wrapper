from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from deepseek_wrapper import DeepSeekClient, DeepSeekConfig
import asyncio
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "supersecret"))
templates = Jinja2Templates(directory="src/deepseek_wrapper/templates")
app.mount("/static", StaticFiles(directory="src/deepseek_wrapper/static"), name="static")

client = DeepSeekClient()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    history = request.session.get("history", [])
    return templates.TemplateResponse("chat.html", {"request": request, "messages": history})

@app.post("/chat", response_class=HTMLResponse)
def chat(request: Request, user_message: str = Form(...)):
    history = request.session.get("history", [])
    history.append({"role": "user", "content": user_message})
    try:
        response = client.chat_completion(history)
    except Exception as e:
        response = f"Error: {e}"
    history.append({"role": "assistant", "content": response})
    request.session["history"] = history
    return templates.TemplateResponse("chat.html", {"request": request, "messages": history})

@app.post("/completions", response_class=HTMLResponse)
def completions(request: Request, prompt: str = Form(...)):
    history = request.session.get("history", [])
    try:
        response = client.generate_text(prompt)
    except Exception as e:
        response = f"Error: {e}"
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": response})
    request.session["history"] = history
    return templates.TemplateResponse("chat.html", {"request": request, "messages": history})

@app.post("/reset", response_class=HTMLResponse)
def reset(request: Request):
    request.session["history"] = []
    return RedirectResponse("/", status_code=303) 