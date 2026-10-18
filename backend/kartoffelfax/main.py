"""KartoffelFax FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from kartoffelfax.api import routes_contacts, routes_fax, routes_settings, websocket
from kartoffelfax.db.database import init_db

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="KartoffelFax", version="0.1.0", lifespan=lifespan)

app.include_router(routes_fax.router)
app.include_router(routes_contacts.router)
app.include_router(routes_settings.router)
app.include_router(websocket.router)

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


def run() -> None:
    """Console-script entry point (`kartoffelfax`), see pyproject.toml."""
    import uvicorn

    uvicorn.run("kartoffelfax.main:app", host="127.0.0.1", port=8420, reload=False)


if __name__ == "__main__":
    run()
