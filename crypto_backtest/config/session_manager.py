"""Session management for FINAL TRIGGER dashboard."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

SESSIONS_DIR = Path("sessions")
APP_STATE_FILE = Path("config/app_state.json")


def ensure_dirs():
    """Ensure required directories exist."""
    SESSIONS_DIR.mkdir(exist_ok=True)
    APP_STATE_FILE.parent.mkdir(exist_ok=True)


def generate_session_id() -> str:
    """Generate unique session ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_session(name: str, assets: list[str]) -> dict[str, Any]:
    """Create a new session."""
    ensure_dirs()
    session_id = generate_session_id()
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    session = {
        "id": session_id,
        "name": name,
        "created": datetime.now().isoformat(),
        "assets": assets,
        "status": "created",
        "current_step": 1,
        "steps_completed": [],
        "notes": "",
    }

    (session_dir / "session.json").write_text(json.dumps(session, indent=2))
    _update_app_state({"last_session": session_id})
    return session


def load_session(session_id: str) -> Optional[dict[str, Any]]:
    """Load session by ID."""
    session_file = SESSIONS_DIR / session_id / "session.json"
    if session_file.exists():
        return json.loads(session_file.read_text())
    return None


def save_session(session: dict[str, Any]) -> None:
    """Save session to disk."""
    session_dir = SESSIONS_DIR / session["id"]
    session_dir.mkdir(exist_ok=True)
    (session_dir / "session.json").write_text(json.dumps(session, indent=2))


def update_session_step(session_id: str, step: int, status: str) -> dict[str, Any]:
    """Update session progress."""
    session = load_session(session_id)
    if session:
        session["current_step"] = step
        session["status"] = status
        if step not in session["steps_completed"]:
            session["steps_completed"].append(step)
        save_session(session)
    return session


def list_sessions() -> list[dict[str, Any]]:
    """List all sessions, most recent first."""
    ensure_dirs()
    sessions = []
    for session_dir in SESSIONS_DIR.iterdir():
        if session_dir.is_dir():
            session = load_session(session_dir.name)
            if session:
                sessions.append(session)
    return sorted(sessions, key=lambda x: x["created"], reverse=True)


def get_last_session_id() -> Optional[str]:
    """Get last active session ID."""
    state = _load_app_state()
    return state.get("last_session")


def delete_session(session_id: str) -> bool:
    """Delete a session."""
    import shutil
    session_dir = SESSIONS_DIR / session_id
    if session_dir.exists():
        shutil.rmtree(session_dir)
        return True
    return False


def get_session_dir(session_id: str) -> Path:
    """Get session directory path."""
    return SESSIONS_DIR / session_id


def _load_app_state() -> dict[str, Any]:
    """Load app state."""
    ensure_dirs()
    if APP_STATE_FILE.exists():
        return json.loads(APP_STATE_FILE.read_text())
    return {}


def _update_app_state(updates: dict[str, Any]) -> None:
    """Update app state."""
    ensure_dirs()
    state = _load_app_state()
    state.update(updates)
    APP_STATE_FILE.write_text(json.dumps(state, indent=2))


# Step definitions
PIPELINE_STEPS = [
    {"id": 1, "name": "Data", "icon": "📥", "status_key": "data_loaded"},
    {"id": 2, "name": "Optimize", "icon": "⚡", "status_key": "optimized"},
    {"id": 3, "name": "Guards", "icon": "🛡️", "status_key": "guards_complete"},
    {"id": 4, "name": "Validate", "icon": "✅", "status_key": "validated"},
    {"id": 5, "name": "Deploy", "icon": "🚀", "status_key": "deployed"},
]
