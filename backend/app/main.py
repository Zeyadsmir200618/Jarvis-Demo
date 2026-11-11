from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import chat, system, workspace
from app.core.config import CORS_ORIGINS, GENERATED_SITES_DIR
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    GENERATED_SITES_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="J.A.R.V.I.S. Core API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
app.mount("/generated_sites", StaticFiles(directory=str(GENERATED_SITES_DIR)), name="generated_sites")
app.include_router(system.router)
app.include_router(chat.router)
app.include_router(workspace.router)


@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>J.A.R.V.I.S. backend is running</h1><p>See <a href='/docs'>/docs</a>.</p>"
