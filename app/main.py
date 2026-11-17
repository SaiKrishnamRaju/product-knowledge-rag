from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(title="Product Knowledge RAG", version="0.1.0")
app.include_router(router)
root = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=root / "web" / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return (root / "web" / "templates" / "index.html").read_text()
