"""FastAPI app exposing the /m5 contract plus a debug web UI.

Run with:  uvicorn skydial.app:app --host 0.0.0.0 --port 8090
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .config import load_config
from .debug_ui import DEBUG_HTML
from .pipeline import SkyPipeline
from .profiles import ProfileError


class ProfileSwitch(BaseModel):
    id: str


def create_app(cfg: dict | None = None) -> FastAPI:
    cfg = cfg or load_config()
    pipeline = SkyPipeline(cfg)
    app = FastAPI(title="SkyDial Pi API", version=app_version())
    app.state.pipeline = pipeline

    @app.get("/m5/sky")
    def m5_sky(profile: str | None = None):
        try:
            return pipeline.sky(profile_id=profile)
        except ProfileError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/m5/status")
    def m5_status():
        return pipeline.status()

    @app.get("/m5/log")
    def m5_log(limit: int = 20):
        return {"now": pipeline.status().now, "sightings": pipeline.recent_log(limit)}

    @app.get("/m5/profiles")
    def m5_profiles():
        return {
            "active": pipeline.profiles.active.id,
            "profiles": pipeline.profiles.list(),
        }

    @app.post("/m5/profile")
    def m5_set_profile(switch: ProfileSwitch):
        try:
            profile = pipeline.profiles.set_active(switch.id)
        except ProfileError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"active": profile.id, "profile": profile}

    @app.get("/", response_class=HTMLResponse)
    @app.get("/debug", response_class=HTMLResponse)
    def debug_ui():
        return HTMLResponse(DEBUG_HTML)

    return app


def app_version() -> str:
    from . import __version__

    return __version__


# Module-level app for `uvicorn skydial.app:app`.
app = create_app()
