"""
main.py — FastAPI Gateway entrypoint for CogniTree backend server.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from python_backend.server.routes.rest import router as rest_router
from python_backend.server.routes.ws import router as ws_router

app = FastAPI(
    title="CogniTree Backend Gateway",
    description="Stateful Tree-Native Autonomous AI Agent Server",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rest_router)
app.include_router(ws_router)

web_ui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../web_ui"))
if os.path.exists(web_ui_dir):
    app.mount("/ui", StaticFiles(directory=web_ui_dir, html=True), name="web_ui")


def start():
    """Launches Uvicorn development server."""
    port = int(os.getenv("PORT", "8765"))
    print(f"Starting CogniTree FastAPI server on http://localhost:{port} ...")
    print(f"Web UI Canvas available at http://localhost:{port}/ui")
    uvicorn.run("python_backend.server.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    start()
