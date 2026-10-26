
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router as chat_router
from api.stream_routes import router as stream_router
from api.upload_routes import router as upload_router
from api.react_routes import router as react_router
from api.react_email_routes import router as react_email_router

from tools.data_tools import CHART_DIR

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="LangGraph Multi-Agent API",
    version="2.0.0",
)

# Frontend static files
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)

# Backend APIs
app.include_router(chat_router)
app.include_router(stream_router)
app.include_router(upload_router)
app.include_router(react_router)
app.include_router(react_email_router)

# Generated charts
CHART_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/charts",
    StaticFiles(directory=CHART_DIR),
    name="charts",
)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/react", include_in_schema=False)
def react_home():
    return FileResponse(FRONTEND_DIR / "react.html")
