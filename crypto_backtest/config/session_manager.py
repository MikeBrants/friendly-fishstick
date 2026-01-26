"""Session management for FINAL TRIGGER dashboard."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

SESSIONS_DIR = Path("sessions")
APP_STATE_FILE = Path("config/app_state.json")
OUTPUTS_DIR = Path("outputs")


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
        "runs": [],  # List of run_ids linked to this session
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
    {"id": 4, "name": "Validate", "icon": "[OK]", "status_key": "validated"},
    {"id": 5, "name": "Deploy", "icon": "🚀", "status_key": "deployed"},
]


# -----------------------------------------------------------------------------
# Run Integration - Link sessions to their backtest runs
# -----------------------------------------------------------------------------


def add_run_to_session(session_id: str, run_id: str, run_type: str = "scan") -> dict[str, Any]:
    """
    Link a run to a session.

    Args:
        session_id: Session ID to update
        run_id: Run ID to link (e.g., "run_20260121_120000")
        run_type: Type of run ("scan", "guards", "displacement", etc.)

    Returns:
        Updated session dict
    """
    session = load_session(session_id)
    if not session:
        return None

    # Initialize runs list if missing (backwards compatibility)
    if "runs" not in session:
        session["runs"] = []

    # Add run entry with metadata
    run_entry = {
        "run_id": run_id,
        "type": run_type,
        "added": datetime.now().isoformat(),
    }

    # Avoid duplicates
    existing_ids = [r["run_id"] if isinstance(r, dict) else r for r in session["runs"]]
    if run_id not in existing_ids:
        session["runs"].append(run_entry)
        save_session(session)

    return session


def get_session_runs(session_id: str) -> list[dict[str, Any]]:
    """
    Get all runs linked to a session with their details.

    Args:
        session_id: Session ID

    Returns:
        List of run info dicts with loaded summaries
    """
    session = load_session(session_id)
    if not session:
        return []

    runs_info = []
    for run_entry in session.get("runs", []):
        # Handle both old format (string) and new format (dict)
        if isinstance(run_entry, str):
            run_id = run_entry
            run_type = "unknown"
            added = None
        else:
            run_id = run_entry["run_id"]
            run_type = run_entry.get("type", "unknown")
            added = run_entry.get("added")

        run_dir = OUTPUTS_DIR / run_id
        run_info = {
            "run_id": run_id,
            "type": run_type,
            "added": added,
            "exists": run_dir.exists(),
        }

        # Load manifest if exists
        manifest_path = run_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                run_info["description"] = manifest.get("description", "")
                run_info["timestamp"] = manifest.get("timestamp", "")
                run_info["assets"] = manifest.get("assets", [])
            except (json.JSONDecodeError, IOError):
                pass

        # Check available files
        run_info["has_scan"] = (run_dir / "scan.csv").exists()
        run_info["has_guards"] = (run_dir / "guards.csv").exists()

        params_dir = run_dir / "params"
        run_info["params_count"] = len(list(params_dir.glob("*.json"))) if params_dir.exists() else 0

        runs_info.append(run_info)

    return runs_info


def get_latest_session_run(session_id: str, run_type: Optional[str] = None) -> Optional[str]:
    """
    Get the latest run_id for a session, optionally filtered by type.

    Args:
        session_id: Session ID
        run_type: Optional filter (e.g., "scan", "guards")

    Returns:
        Latest run_id or None
    """
    runs = get_session_runs(session_id)
    if run_type:
        runs = [r for r in runs if r["type"] == run_type]

    if not runs:
        return None

    # Return most recently added
    return runs[-1]["run_id"]


def migrate_session_runs(session_id: str) -> dict[str, Any]:
    """
    Migrate a session to include runs field if missing.
    Attempts to auto-detect runs based on timestamp proximity.

    Args:
        session_id: Session ID to migrate

    Returns:
        Updated session dict
    """
    session = load_session(session_id)
    if not session:
        return None

    if "runs" not in session:
        session["runs"] = []

    # Auto-detect runs that might belong to this session based on timestamp
    session_created = datetime.fromisoformat(session["created"])

    for run_dir in OUTPUTS_DIR.iterdir():
        if not run_dir.is_dir() or not run_dir.name.startswith("run_"):
            continue

        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        try:
            manifest = json.loads(manifest_path.read_text())
            run_timestamp = datetime.fromisoformat(manifest.get("timestamp", ""))

            # If run was created within 24h after session creation, likely related
            delta = run_timestamp - session_created
            if 0 <= delta.total_seconds() <= 86400:  # 24 hours
                run_id = run_dir.name
                existing_ids = [r["run_id"] if isinstance(r, dict) else r for r in session["runs"]]
                if run_id not in existing_ids:
                    session["runs"].append({
                        "run_id": run_id,
                        "type": "auto-detected",
                        "added": datetime.now().isoformat(),
                    })
        except (json.JSONDecodeError, ValueError, IOError):
            continue

    save_session(session)
    return session
