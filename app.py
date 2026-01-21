"""
FINAL TRIGGER v2 - Backtest Dashboard
Interface visuelle pour piloter les backtests crypto

Usage:
    streamlit run app.py
"""
import html
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =============================================================================
# CONSOLE LOGGING SYSTEM
# =============================================================================
def init_console():
    """Initialize console in session state."""
    if "console_logs" not in st.session_state:
        st.session_state.console_logs = []
    if "console_placeholder" not in st.session_state:
        st.session_state.console_placeholder = None


def _render_console_text(text: str) -> str:
    """Render console text with compact styling."""
    safe_text = html.escape(text)
    return (
        "<pre style=\"margin:0;"
        "font-size:11px;line-height:1.2;"
        "white-space:pre-wrap;\">"
        f"{safe_text}"
        "</pre>"
    )


def console_log(msg: str, level: str = "INFO"):
    """Add message to console with timestamp."""
    emoji = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERR": "❌", "RUN": "🔄"}
    prefix = emoji.get(level, "- ")
    timestamp = datetime.now().strftime("%H:%M:%S")

    st.session_state.console_logs.append(f"{prefix} {timestamp} │ {msg}")
    st.session_state.console_logs = st.session_state.console_logs[-20:]

    if st.session_state.console_placeholder is not None:
        st.session_state.console_placeholder.markdown(
            _render_console_text("\n".join(st.session_state.console_logs)),
            unsafe_allow_html=True,
        )


def clear_console():
    """Clear console logs."""
    st.session_state.console_logs = []
    if st.session_state.console_placeholder is not None:
        st.session_state.console_placeholder.markdown(
            _render_console_text("Ready..."),
            unsafe_allow_html=True,
        )


def render_console_panel():
    """Render compact console panel in the sidebar."""
    st.sidebar.caption("🖥️ Console")
    col1, col2 = st.sidebar.columns([0.15, 0.85])
    with col1:
        if st.button("🗑", key="clear_console", help="Clear console"):
            clear_console()
    with col2:
        st.markdown("")

    st.session_state.console_placeholder = st.sidebar.empty()
    console_text = "\n".join(st.session_state.console_logs) if st.session_state.console_logs else "Ready..."
    st.session_state.console_placeholder.markdown(
        _render_console_text(console_text),
        unsafe_allow_html=True,
    )


def render_progress_stepper(current_step: int, completed_steps: list[int]):
    """Render horizontal progress stepper."""
    steps = [
        {"id": 1, "name": "Data", "icon": "📥"},
        {"id": 2, "name": "Optimize", "icon": "⚡"},
        {"id": 3, "name": "Guards", "icon": "🛡️"},
        {"id": 4, "name": "Validate", "icon": "✅"},
        {"id": 5, "name": "Deploy", "icon": "🚀"},
    ]

    stepper_html = """
    <style>
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 10px;
        background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #2D3748;
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    .step-circle {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }
    .step-completed {
        background: linear-gradient(135deg, #48BB78 0%, #38A169 100%);
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
    }
    .step-active {
        background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%);
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
        animation: pulse 2s infinite;
    }
    .step-pending {
        background: #2D3748;
        border: 2px dashed #4A5568;
    }
    .step-label {
        font-size: 12px;
        color: #A0AEC0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .step-completed .step-label { color: #48BB78; }
    .step-active .step-label { color: #00D4FF; font-weight: 600; }
    .step-connector {
        flex: 1;
        height: 3px;
        background: #2D3748;
        margin: 0 5px;
        margin-bottom: 25px;
    }
    .step-connector.completed {
        background: linear-gradient(90deg, #48BB78 0%, #38A169 100%);
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    </style>
    <div class="stepper-container">
    """

    for i, step in enumerate(steps):
        if step["id"] in completed_steps:
            status_class = "step-completed"
            icon = "✓"
        elif step["id"] == current_step:
            status_class = "step-active"
            icon = step["icon"]
        else:
            status_class = "step-pending"
            icon = step["icon"]

        stepper_html += f"""
        <div class="step">
            <div class="step-circle {status_class}">{icon}</div>
            <span class="step-label">{step["name"]}</span>
        </div>
        """

        if i < len(steps) - 1:
            connector_class = "completed" if step["id"] in completed_steps else ""
            stepper_html += f'<div class="step-connector {connector_class}"></div>'

    stepper_html += "</div>"

    components.html(stepper_html, height=120)


def advance_session_step(step_id: int, status: str):
    """Advance session to a new step if session is active."""
    if st.session_state.get("active_session"):
        session = st.session_state.active_session
        session = update_session_step(session["id"], step_id, status)
        st.session_state.active_session = session
        console_log(f"Session → Étape {step_id} ({status})", "OK")
        return True
    return False


def link_outputs_to_session(file_patterns: list[str]):
    """Copy matching output files to active session directory."""
    if not st.session_state.get("active_session"):
        return

    import shutil

    session_dir = get_session_dir(st.session_state.active_session["id"])
    outputs_dir = Path("outputs")

    if not outputs_dir.exists():
        return

    for pattern in file_patterns:
        for file_path in outputs_dir.glob(pattern):
            dest = session_dir / file_path.name
            try:
                shutil.copy2(file_path, dest)
                console_log(f"Linked: {file_path.name}", "INFO")
            except Exception as exc:
                console_log(f"Failed to link {file_path.name}: {exc}", "WARN")


def get_next_action_recommendation() -> dict:
    """Get recommended next action based on session state."""
    if not st.session_state.get("active_session"):
        return {
            "message": "Créez une session pour commencer",
            "action": "create_session",
            "button_label": "➕ Créer une session",
            "icon": "ℹ️",
        }

    session = st.session_state.active_session
    completed = session.get("steps_completed", [])
    assets = session.get("assets", [])

    if 1 not in completed:
        return {
            "message": f"Télécharger les données pour {', '.join(assets[:3])}{'...' if len(assets) > 3 else ''}",
            "action": "download",
            "button_label": "📥 Télécharger",
            "page": "📥 Download OHLCV",
            "icon": "📥",
        }
    if 2 not in completed:
        return {
            "message": f"Lancer l'optimisation Bayésienne sur {len(assets)} assets",
            "action": "optimize",
            "button_label": "⚡ Optimiser",
            "page": "⚡ Bayesian",
            "icon": "⚡",
        }
    if 3 not in completed:
        return {
            "message": "Exécuter les 7 guards de validation",
            "action": "guards",
            "button_label": "🛡️ Valider",
            "page": "🛡️ Guards",
            "icon": "🛡️",
        }
    if 4 not in completed:
        return {
            "message": "Comparer les signaux Pine Script vs Python",
            "action": "validate",
            "button_label": "🔄 Comparer",
            "page": "🔄 Comparateur Pine",
            "icon": "✅",
        }
    if 5 not in completed:
        return {
            "message": "Prêt pour le déploiement paper trading",
            "action": "deploy",
            "button_label": "🚀 Déployer",
            "page": "📊 Dashboard",
            "icon": "🚀",
        }
    return {
        "message": "Pipeline complet ! Session validée ✅",
        "action": "complete",
        "button_label": "📋 Voir résultats",
        "page": "🏆 Comparaison Assets",
        "icon": "🎉",
    }


def render_empty_state(
    icon: str,
    title: str,
    message: str,
    action_label: str | None = None,
    action_page: str | None = None,
):
    """Render empty state with optional action button."""
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 60px 20px;
        color: #A0AEC0;
    ">
        <div style="font-size: 4rem; margin-bottom: 20px;">{icon}</div>
        <div style="font-size: 1.3rem; color: #E2E8F0; margin-bottom: 10px;">{title}</div>
        <div style="font-size: 0.95rem; max-width: 400px; margin: 0 auto;">{message}</div>
    </div>
    """, unsafe_allow_html=True)

    if action_label and action_page:
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button(action_label, type="primary", use_container_width=True):
                st.session_state.current_page = action_page
                st.rerun()


def render_new_session_modal():
    """Render new session creation in sidebar or main area."""
    if not st.session_state.get("show_new_session_modal"):
        return

    st.markdown("---")
    st.subheader("➕ Nouvelle session")

    session_name = st.text_input(
        "Nom de la session",
        value=f"Session {datetime.now().strftime('%d/%m %H:%M')}",
        key="new_session_name",
    )

    asset_preset = st.selectbox(
        "Preset d'assets",
        ["Validés (BTC, ETH, AVAX, UNI, SEI)", "Top 10", "Personnalisé"],
        key="new_session_preset",
    )

    if asset_preset == "Validés (BTC, ETH, AVAX, UNI, SEI)":
        selected_assets = VALIDATED_ASSETS
    elif asset_preset == "Top 10":
        selected_assets = TOP50_ASSETS[:10]
    else:
        selected_assets = st.multiselect(
            "Sélectionner les assets",
            ALL_ASSETS,
            default=["BTC", "ETH"],
            key="new_session_assets_custom",
        )

    st.info(f"Assets: {', '.join(selected_assets)}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "✅ Créer",
            type="primary",
            use_container_width=True,
            key="create_session_btn",
        ):
            session = create_session(session_name, list(selected_assets))
            st.session_state.active_session = session
            st.session_state.show_new_session_modal = False
            console_log(f"Session créée: {session_name}", "OK")
            st.rerun()
    with col2:
        if st.button(
            "❌ Annuler",
            use_container_width=True,
            key="cancel_new_session_btn",
        ):
            st.session_state.show_new_session_modal = False
            st.rerun()


def render_load_session_modal():
    """Render session loading UI."""
    if not st.session_state.get("show_load_session_modal"):
        return

    st.markdown("---")
    st.subheader("📂 Charger une session")

    sessions = list_sessions()
    if not sessions:
        st.warning("Aucune session disponible")
        if st.button("Fermer", key="close_load_modal_btn"):
            st.session_state.show_load_session_modal = False
            st.rerun()
        return

    session_options = {f"{s['name']} ({s['id']})": s for s in sessions}
    selected = st.selectbox(
        "Session",
        list(session_options.keys()),
        key="load_session_select",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "✅ Charger",
            type="primary",
            use_container_width=True,
            key="load_session_btn",
        ):
            st.session_state.active_session = session_options[selected]
            st.session_state.show_load_session_modal = False
            console_log(f"Session chargée: {selected}", "OK")
            st.rerun()
    with col2:
        if st.button(
            "❌ Annuler",
            use_container_width=True,
            key="cancel_load_session_btn",
        ):
            st.session_state.show_load_session_modal = False
            st.rerun()
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from crypto_backtest.config.scan_assets import (
    ALL_ASSETS,
    SCAN_ASSETS,
    VALIDATED_ASSETS,
    EXCLUDED_ASSETS,
    TOP50_ASSETS,
    TIER1_ASSETS,
    TIER2_ASSETS,
    TIER3_ASSETS,
    TIER4_ASSETS,
    BONUS_ASSETS,
    PASS_CRITERIA,
)
from crypto_backtest.config.session_manager import (
    create_session,
    load_session,
    save_session,
    list_sessions,
    get_last_session_id,
    update_session_step,
    delete_session,
    get_session_dir,
    PIPELINE_STEPS,
)
from crypto_backtest.utils.system_utils import (
    get_default_workers,
    check_storage_warning,
    get_system_info,
)
from crypto_backtest.validation.fail_diagnostic import FailDiagnostic
from crypto_backtest.validation.conservative_reopt import ConservativeReoptimizer
from crypto_backtest.optimization.parallel_optimizer import (
    BASE_CONFIG,
    build_strategy_params,
    load_data as load_asset_data,
    run_backtest as run_scan_backtest,
    split_data as split_data_segments,
)
from crypto_backtest.optimization.bayesian import _instantiate_strategy
from crypto_backtest.engine.backtest import VectorizedBacktester
from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="FINAL TRIGGER v2 - Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS - Dark Trading Theme
# =============================================================================
st.markdown("""
<style>
/* Main container styling */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1F2E 0%, #0E1117 100%);
    border-right: 1px solid #2D3748;
}

[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00D4FF;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}

/* Cards / Metric boxes */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
    border: 1px solid #2D3748;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

[data-testid="stMetric"] label {
    color: #A0AEC0;
    font-size: 0.85rem;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #00D4FF;
    font-weight: 700;
}

/* Success/Warning/Error boxes */
.stSuccess {
    background: linear-gradient(135deg, #1A2F23 0%, #0E1117 100%);
    border-left: 4px solid #48BB78;
}

.stWarning {
    background: linear-gradient(135deg, #2F2A1A 0%, #0E1117 100%);
    border-left: 4px solid #ECC94B;
}

.stError {
    background: linear-gradient(135deg, #2F1A1A 0%, #0E1117 100%);
    border-left: 4px solid #F56565;
}

.stInfo {
    background: linear-gradient(135deg, #1A1F2E 0%, #0E1117 100%);
    border-left: 4px solid #00D4FF;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%);
    color: #0E1117;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.6rem 1.2rem;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #00E5FF 0%, #00AADD 100%);
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
    transform: translateY(-1px);
}

/* Primary button (type="primary") */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%);
}

/* DataFrames */
[data-testid="stDataFrame"] {
    border: 1px solid #2D3748;
    border-radius: 10px;
    overflow: hidden;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #1A1F2E;
    border-radius: 10px;
    padding: 0.3rem;
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: #A0AEC0;
    padding: 0.5rem 1rem;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #00D4FF 0%, #0099CC 100%);
    color: #0E1117;
}

/* Sliders */
.stSlider [data-baseweb="slider"] {
    margin-top: 0.5rem;
}

/* Expanders */
.streamlit-expanderHeader {
    background: #1A1F2E;
    border: 1px solid #2D3748;
    border-radius: 8px;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #00D4FF 0%, #00FF88 100%);
}

/* Selectbox / Multiselect */
[data-baseweb="select"] {
    background: #1A1F2E;
}

/* Radio buttons */
.stRadio > div {
    background: transparent;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed #2D3748;
    border-radius: 10px;
    padding: 1rem;
}

[data-testid="stFileUploader"]:hover {
    border-color: #00D4FF;
}

/* Headers */
h1 {
    color: #FFFFFF;
    font-weight: 700;
    margin-bottom: 1rem;
}

h2, h3 {
    color: #E2E8F0;
}

/* Divider */
hr {
    border-color: #2D3748;
    margin: 1.5rem 0;
}

/* Code blocks */
code {
    background: #1A1F2E;
    border: 1px solid #2D3748;
    border-radius: 4px;
    padding: 0.2rem 0.4rem;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #0E1117;
}

::-webkit-scrollbar-thumb {
    background: #2D3748;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #4A5568;
}

/* Plotly charts dark background */
.js-plotly-plot .plotly .modebar {
    background: transparent !important;
}

/* Sidebar logo area */
.sidebar-logo {
    text-align: center;
    padding: 1rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid #2D3748;
}

.sidebar-logo h1 {
    font-size: 1.5rem;
    background: linear-gradient(135deg, #00D4FF 0%, #00FF88 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR - Navigation Groupée
# =============================================================================
st.sidebar.title("🎯 FINAL TRIGGER v2")

init_console()

# Session Management
if "active_session" not in st.session_state:
    last_id = get_last_session_id()
    if last_id:
        st.session_state.active_session = load_session(last_id)
    else:
        st.session_state.active_session = None

st.sidebar.markdown("### 📂 Session")
sessions = list_sessions()

if st.session_state.active_session:
    st.sidebar.success(f"**{st.session_state.active_session['name']}**")
    st.sidebar.caption(f"Étape {st.session_state.active_session['current_step']}/5")

if st.sidebar.button("➕ Nouvelle session", use_container_width=True):
    st.session_state.show_new_session_modal = True

if sessions and st.sidebar.button("📂 Charger session", use_container_width=True):
    st.session_state.show_load_session_modal = True

st.sidebar.markdown("---")

# Initialize session state for navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "📊 Dashboard"

# Section: Accueil
st.sidebar.markdown("### 🏠 Accueil")
if st.sidebar.button("📊 Dashboard", use_container_width=True, key="btn_dashboard"):
    st.session_state.current_page = "📊 Dashboard"

# Section: Données
st.sidebar.markdown("### 📁 Données")
if st.sidebar.button("📥 Download OHLCV", use_container_width=True, key="btn_download"):
    st.session_state.current_page = "📥 Download OHLCV"
if st.sidebar.button("🔄 Comparateur Pine", use_container_width=True, key="btn_pine"):
    st.session_state.current_page = "🔄 Comparateur Pine"

# Section: Optimisation
st.sidebar.markdown("### ⚙️ Optimisation")
if st.sidebar.button("⚡ Bayesian", use_container_width=True, key="btn_bayesian"):
    st.session_state.current_page = "⚡ Bayesian"
if st.sidebar.button("🎚️ Displacement Grid", use_container_width=True, key="btn_displacement"):
    st.session_state.current_page = "🎚️ Displacement Grid"
if st.sidebar.button("🛡️ Guards", use_container_width=True, key="btn_guards"):
    st.session_state.current_page = "🛡️ Guards"

# Section: Analyse
st.sidebar.markdown("### 🔍 Analyse")
if st.sidebar.button("🏆 Comparaison Assets", use_container_width=True, key="btn_compare"):
    st.session_state.current_page = "🏆 Comparaison Assets"
if st.sidebar.button("💼 Portfolio Builder", use_container_width=True, key="btn_portfolio"):
    st.session_state.current_page = "💼 Portfolio Builder"
if st.sidebar.button("📉 Visualisation", use_container_width=True, key="btn_viz"):
    st.session_state.current_page = "📉 Visualisation"
if st.sidebar.button("📈 Fichiers", use_container_width=True, key="btn_files"):
    st.session_state.current_page = "📈 Fichiers"
if st.sidebar.button("📋 Historique", use_container_width=True, key="btn_history"):
    st.session_state.current_page = "📋 Historique"

# Keyboard shortcuts
st.sidebar.markdown("---")
with st.sidebar.expander("⌨️ Raccourcis"):
    st.markdown("""
    - `R` — Refresh data
    - `N` — Nouvelle session
    - `D` — Dashboard
    - `H` — Historique
    """)

# Set active page
page = st.session_state.current_page

# Render modals if triggered
render_new_session_modal()
render_load_session_modal()

st.sidebar.markdown("---")
st.sidebar.markdown("### ✅ Assets Validés")
st.sidebar.success("BTC, ETH, AVAX, UNI, SEI")

st.sidebar.markdown("### 📋 Critères")
st.sidebar.info(f"""
Sharpe > {PASS_CRITERIA['oos_sharpe_min']} | WFE > {PASS_CRITERIA['wfe_min']}
Max DD < {PASS_CRITERIA['max_dd_max']*100:.0f}% | Trades > {PASS_CRITERIA['oos_trades_min']}
""")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_available_data():
    """List available data files."""
    data_dir = Path("data")
    if not data_dir.exists():
        return []

    files = list(data_dir.glob("*.parquet")) + list(data_dir.glob("*.csv"))
    return sorted([f.stem.replace("_1H", "") for f in files])


def get_scan_results():
    """Get list of scan result files."""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return []
    return sorted(outputs_dir.glob("multiasset_scan_*.csv"), reverse=True)


def get_guards_summary_path() -> Path | None:
    """Return most recent guards summary path if available."""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return None
    candidates = list(outputs_dir.glob("multiasset_guards_summary_*.csv"))
    if candidates:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    legacy = outputs_dir / "multiasset_guards_summary.csv"
    if legacy.exists():
        return legacy
    return None


def get_guards_results():
    """Get guards summary if exists."""
    path = get_guards_summary_path()
    if path is not None and path.exists():
        df = pd.read_csv(path)
        if path.name.startswith("multiasset_guards_summary_"):
            run_id = path.stem.replace("multiasset_guards_summary_", "")
            df["run_id"] = run_id
        return df
    return None


def get_guard_display_columns(guards_df: pd.DataFrame) -> list[str]:
    """Return ordered guard columns including value metrics when available."""
    desired = [
        "asset",
        "all_pass",
        "base_sharpe",
        "guard001_p_value",
        "guard001_pass",
        "guard002_variance_pct",
        "guard002_pass",
        "guard003_sharpe_ci_lower",
        "guard003_pass",
        "guard005_top10_pct",
        "guard005_pass",
        "guard006_stress1_sharpe",
        "guard006_pass",
        "guard007_mismatch_pct",
        "guard007_pass",
        "error",
        "run_id",
    ]
    return [col for col in desired if col in guards_df.columns]


def resolve_guard_file(
    outputs_dir: Path,
    asset: str,
    guard_key: str,
    run_id: str | None,
) -> Path | None:
    """Resolve guard file path using run_id, then newest timestamp, then legacy."""
    if run_id:
        candidate = outputs_dir / f"{asset}_{guard_key}_{run_id}.csv"
        if candidate.exists():
            return candidate
    candidates = sorted(
        outputs_dir.glob(f"{asset}_{guard_key}_*.csv"),
        key=lambda p: p.stat().st_mtime,
    )
    if candidates:
        return candidates[-1]
    legacy = outputs_dir / f"{asset}_{guard_key}.csv"
    if legacy.exists():
        return legacy
    return None


def load_diagnostic_history() -> dict:
    """Load diagnostic history from disk."""
    history_file = Path("outputs/diagnostic_history.json")
    if history_file.exists():
        try:
            return json.loads(history_file.read_text())
        except json.JSONDecodeError:
            return {"diagnostics": []}
    return {"diagnostics": []}


def load_reopt_history() -> dict:
    """Load reoptimization history from disk."""
    history_file = Path("outputs/reoptimization_history.json")
    if history_file.exists():
        try:
            return json.loads(history_file.read_text())
        except json.JSONDecodeError:
            return {"reoptimizations": []}
    return {"reoptimizations": []}


def _run_trades_for_params(data: pd.DataFrame, params: dict[str, float]) -> pd.DataFrame:
    """Run backtest and return trades with pnl_pct."""
    if data.empty:
        return pd.DataFrame()

    strategy = _instantiate_strategy(FinalTriggerStrategy, params)
    backtester = VectorizedBacktester(BASE_CONFIG)
    result = backtester.run(data, strategy)
    trades = result.trades.copy()

    if not trades.empty and "pnl_pct" not in trades.columns:
        if "net_pnl" in trades.columns and "notional" in trades.columns:
            trades["pnl_pct"] = (trades["net_pnl"] / trades["notional"]) * 100.0
        elif "gross_pnl" in trades.columns and "notional" in trades.columns:
            trades["pnl_pct"] = (trades["gross_pnl"] / trades["notional"]) * 100.0

    return trades


def _build_params_from_scan_row(row: dict) -> dict[str, float]:
    """Build strategy params from a scan row."""
    return build_strategy_params(
        sl_mult=float(row.get("sl_mult", 0)),
        tp1_mult=float(row.get("tp1_mult", 0)),
        tp2_mult=float(row.get("tp2_mult", 0)),
        tp3_mult=float(row.get("tp3_mult", 0)),
        tenkan=int(row.get("tenkan", 0)),
        kijun=int(row.get("kijun", 0)),
        tenkan_5=int(row.get("tenkan_5", 0)),
        kijun_5=int(row.get("kijun_5", 0)),
    )


def display_fail_diagnostic(
    asset: str,
    scan_result: dict,
    data: pd.DataFrame,
    trades_is: pd.DataFrame | None = None,
    trades_oos: pd.DataFrame | None = None,
):
    """Display the diagnostic report for a failed asset."""
    st.error(f"❌ {asset} FAIL — Analyse en cours...")

    diag = FailDiagnostic(asset, scan_result, data, trades_is, trades_oos)
    report = diag.run_full_diagnostic()

    primary = report["primary_cause"]
    if primary:
        severity_colors = {
            "CRITICAL": "🔴",
            "SEVERE": "🟠",
            "MODERATE": "🟡",
            "LOW": "🟢",
        }
        color = severity_colors.get(primary["severity"], "⚪")

        st.markdown(f"### 🔍 Cause principale: **{primary['cause']}**")
        st.markdown(
            f"**Sévérité:** {color} {primary['severity']} | "
            f"**Probabilité:** {primary['probability']}%"
        )
        st.info(primary["explanation"])

        with st.expander("📊 Métriques détaillées"):
            st.json(primary["metrics"])

        st.markdown(f"**💡 Fix suggéré:** {primary['fix']}")

    with st.expander("🔬 Analyse complète (toutes les causes)"):
        for cause in report["all_causes"]:
            severity_colors = {
                "CRITICAL": "🔴",
                "SEVERE": "🟠",
                "MODERATE": "🟡",
                "LOW": "🟢",
                "UNKNOWN": "⚪",
            }
            color = severity_colors.get(cause.get("severity", "UNKNOWN"), "⚪")
            st.markdown(
                f"{color} **{cause['cause']}** ({cause.get('probability', 0)}%): "
                f"{cause.get('explanation', 'N/A')}"
            )

    st.markdown("### 💡 Recommandation")
    rec = report["recommendation"]

    col1, col2 = st.columns([3, 1])
    with col1:
        if report["recoverable"]:
            st.success(f"**{rec['action']}**: {rec['details']}")
        else:
            st.error(f"**{rec['action']}**: {rec['details']}")
            st.warning("⚠️ Cet asset est probablement non viable")

    with col2:
        if rec.get("auto_actionable", False) and "REOPT" in rec.get("command", ""):
            if st.button(f"🔄 Reopt {asset}", key=f"reopt_{asset}"):
                st.session_state[f"trigger_reopt_{asset}"] = True

    if st.session_state.get(f"trigger_reopt_{asset}", False):
        st.session_state[f"trigger_reopt_{asset}"] = False
        run_conservative_reoptimization(asset, data)

    return report


def run_conservative_reoptimization(asset: str, data: pd.DataFrame):
    """Run conservative reoptimization with UI feedback."""
    st.markdown(f"### 🔄 Réoptimisation conservative: {asset}")

    progress_bar = st.progress(0)
    status_text = st.empty()

    def backtest_wrapper(data_slice: pd.DataFrame, params: dict) -> dict:
        full_params = build_strategy_params(
            sl_mult=params["sl_mult"],
            tp1_mult=params["tp1_mult"],
            tp2_mult=params["tp2_mult"],
            tp3_mult=params["tp3_mult"],
            tenkan=params["tenkan"],
            kijun=params["kijun"],
            tenkan_5=params["tenkan_5"],
            kijun_5=params["kijun_5"],
        )
        return run_scan_backtest(data_slice, full_params)

    status_text.text("Phase 1/3: Optimisation ATR (grid discret)...")
    progress_bar.progress(10)

    reoptimizer = ConservativeReoptimizer(asset, data, backtest_wrapper)
    result = reoptimizer.run_conservative_optimization()

    progress_bar.progress(100)

    if result["status"] == "SUCCESS":
        st.success(
            f"✅ {asset} récupéré! OOS Sharpe={result['oos_sharpe']:.2f}, "
            f"WFE={result['wfe']:.2f}"
        )
        st.markdown("**Nouveaux paramètres:**")
        st.json(result["params"])

        if st.button(f"➕ Ajouter {asset} aux assets validés"):
            add_to_validated_assets(asset, result)
            st.success(f"{asset} ajouté aux assets validés!")
    else:
        st.error(
            f"❌ {asset} FAIL AGAIN — OOS Sharpe={result['oos_sharpe']:.2f}, "
            f"WFE={result['wfe']:.2f}"
        )
        st.warning("Cet asset n'est pas compatible avec la stratégie Final Trigger")

        if st.button(f"☠️ Marquer {asset} comme non viable"):
            mark_as_dead(asset)
            st.info(f"{asset} marqué comme non viable")

    return result


def add_to_validated_assets(asset: str, result: dict) -> None:
    """Add asset to validated assets list."""
    validated_file = Path("outputs/validated_assets.json")
    if validated_file.exists():
        validated = json.loads(validated_file.read_text())
    else:
        validated = {"assets": []}

    existing = {entry["asset"] for entry in validated.get("assets", [])}
    if asset in existing:
        return

    validated["assets"].append(
        {
            "asset": asset,
            "params": result["params"],
            "oos_sharpe": result["oos_sharpe"],
            "wfe": result["wfe"],
            "added_at": result["timestamp"],
            "mode": result["mode"],
        }
    )

    validated_file.write_text(json.dumps(validated, indent=2))


def mark_as_dead(asset: str) -> None:
    """Mark asset as non-viable."""
    dead_file = Path("outputs/dead_assets.json")
    if dead_file.exists():
        dead = json.loads(dead_file.read_text())
    else:
        dead = {"assets": []}

    existing = {entry["asset"] for entry in dead.get("assets", [])}
    if asset in existing:
        return

    dead["assets"].append(
        {
            "asset": asset,
            "marked_at": datetime.now().isoformat(),
            "reason": "Failed conservative reoptimization",
        }
    )
    dead_file.write_text(json.dumps(dead, indent=2))


def display_history_sidebar() -> None:
    """Render diagnostic and reoptimization history in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📜 Historique")

    diag_history = load_diagnostic_history()
    if diag_history.get("diagnostics"):
        with st.sidebar.expander(f"🔍 Diagnostics ({len(diag_history['diagnostics'])})"):
            for item in reversed(diag_history["diagnostics"][-10:]):
                status = "🟢" if item.get("recoverable") else "🔴"
                st.markdown(f"{status} **{item['asset']}**: {item.get('primary_cause', 'N/A')}")

    reopt_history = load_reopt_history()
    if reopt_history.get("reoptimizations"):
        with st.sidebar.expander(
            f"🔄 Réoptimisations ({len(reopt_history['reoptimizations'])})"
        ):
            for item in reversed(reopt_history["reoptimizations"][-10:]):
                status = "✅" if item["status"] == "SUCCESS" else "❌"
                st.markdown(
                    f"{status} **{item['asset']}**: Sharpe={item['oos_sharpe']:.2f}"
                )

    validated_file = Path("outputs/validated_assets.json")
    if validated_file.exists():
        validated = json.loads(validated_file.read_text())
        with st.sidebar.expander(f"✅ Assets validés ({len(validated['assets'])})"):
            for item in validated["assets"]:
                st.markdown(f"**{item['asset']}**: Sharpe={item['oos_sharpe']:.2f}")

    dead_file = Path("outputs/dead_assets.json")
    if dead_file.exists():
        dead = json.loads(dead_file.read_text())
        with st.sidebar.expander(f"☠️ Assets morts ({len(dead['assets'])})"):
            for item in dead["assets"]:
                st.markdown(f"**{item['asset']}**")


def run_command(cmd: list, placeholder, show_in_console: bool = True):
    """Run a command and stream output to Streamlit."""
    if show_in_console:
        console_log(f"Exec: {' '.join(cmd[:3])}...", "RUN")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines = []
    for line in iter(process.stdout.readline, ""):
        output_lines.append(line)
        placeholder.code("".join(output_lines[-50:]))  # Show last 50 lines

        line_lower = line.lower()
        if "error" in line_lower or "failed" in line_lower:
            console_log(line.strip()[:60], "ERR")
        elif "complete" in line_lower or "finished" in line_lower or "pass" in line_lower:
            console_log(line.strip()[:60], "OK")

    process.wait()

    if process.returncode == 0:
        console_log("Process completed successfully", "OK")
    else:
        console_log(f"Process failed (code {process.returncode})", "ERR")

    return process.returncode, "".join(output_lines)


# =============================================================================
# PAGES
# =============================================================================

# -----------------------------------------------------------------------------
# DASHBOARD
# -----------------------------------------------------------------------------
if page == "📊 Dashboard":
    st.title("📊 Dashboard Principal")

    # Show progress stepper if session active
    if st.session_state.get("active_session"):
        session = st.session_state.active_session
        render_progress_stepper(
            current_step=session.get("current_step", 1),
            completed_steps=session.get("steps_completed", []),
        )
    else:
        render_empty_state(
            icon="🎯",
            title="Bienvenue dans FINAL TRIGGER v2",
            message="Créez votre première session pour commencer le pipeline de backtesting et validation.",
        )
        if st.button("➕ Créer une session", type="primary", key="empty_create"):
            st.session_state.show_new_session_modal = True
            st.rerun()
        st.stop()

    # Next action recommendation
    rec = get_next_action_recommendation()

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1A2F23 0%, #0E1117 100%);
        border: 1px solid #48BB78;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    ">
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 2rem;">{rec['icon']}</span>
            <div>
                <div style="color: #48BB78; font-weight: 600; font-size: 1.1rem;">
                    Prochaine action recommandée
                </div>
                <div style="color: #E2E8F0; margin-top: 4px;">
                    {rec['message']}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if rec.get("page"):
            if st.button(rec["button_label"], type="primary", use_container_width=True):
                st.session_state.current_page = rec["page"]
                st.rerun()
    with col2:
        if st.button("📋 Détails session", use_container_width=True):
            st.session_state.show_session_details = True
    with col3:
        if st.button("⏸️ Plus tard", use_container_width=True):
            pass

    col1, col2, col3 = st.columns(3)

    # Data status
    with col1:
        st.subheader("📁 Données")
        available_data = get_available_data()
        if available_data:
            st.success(f"{len(available_data)} assets disponibles")
            with st.expander("Voir les assets"):
                for asset in available_data:
                    st.write(f"• {asset}")
        else:
            st.warning("Aucune donnée. Allez dans 'Download Data'")

    # Optimization status
    with col2:
        st.subheader("⚡ Optimisations")
        scan_results = get_scan_results()
        if scan_results:
            st.success(f"{len(scan_results)} scans effectués")
            latest = scan_results[0]
            st.caption(f"Dernier: {latest.name}")
        else:
            st.warning("Aucun scan. Allez dans 'Optimization'")

    # Guards status
    with col3:
        st.subheader("🛡️ Guards")
        guards_df = get_guards_results()
        if guards_df is not None:
            passed = guards_df["all_pass"].sum()
            total = len(guards_df)
            if passed == total:
                st.success(f"{passed}/{total} assets validés")
            else:
                st.warning(f"{passed}/{total} assets validés")
        else:
            st.info("Guards non exécutés")

    is_warning, storage_msg = check_storage_warning()
    if is_warning:
        st.warning(storage_msg)
        with st.expander("💡 Libérer de l'espace"):
            st.markdown("""
            ```bash
            # Supprimer les anciens runs (> 30 jours)
            find outputs -name "run_*" -mtime +30 -exec rm -rf {} \\;

            # Ou compresser
            tar -czvf old_runs.tar.gz outputs/run_2026011* && rm -rf outputs/run_2026011*
            ```
            """)

    st.markdown("---")

    # Quick stats from latest scan
    if scan_results:
        st.subheader("📈 Derniers Résultats de Scan")
        try:
            df = pd.read_csv(scan_results[0])

            # Filter PASS assets
            pass_mask = (
                (df["oos_sharpe"] >= PASS_CRITERIA["oos_sharpe_min"]) &
                (df["wfe"] >= PASS_CRITERIA["wfe_min"])
            )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### ✅ Assets PASS")
                pass_df = df[pass_mask][["asset", "oos_sharpe", "wfe", "oos_return", "oos_max_dd"]]
                if not pass_df.empty:
                    st.dataframe(
                        pass_df.style.format({
                            "oos_sharpe": "{:.2f}",
                            "wfe": "{:.2f}",
                            "oos_return": "{:.1f}%",
                            "oos_max_dd": "{:.1f}%",
                        }),
                        use_container_width=True,
                    )
                else:
                    st.info("Aucun asset PASS")

            with col2:
                st.markdown("#### ❌ Assets FAIL")
                fail_df = df[~pass_mask][["asset", "oos_sharpe", "wfe", "oos_return", "oos_max_dd"]]
                if not fail_df.empty:
                    st.dataframe(
                        fail_df.style.format({
                            "oos_sharpe": "{:.2f}",
                            "wfe": "{:.2f}",
                            "oos_return": "{:.1f}%",
                            "oos_max_dd": "{:.1f}%",
                        }),
                        use_container_width=True,
                    )
                else:
                    st.success("Tous les assets sont PASS!")

            if not fail_df.empty:
                st.markdown("---")
                st.subheader("🔍 Diagnostic FAIL")
                selected_fail = st.selectbox(
                    "Asset FAIL",
                    fail_df["asset"].tolist(),
                    key="fail_diagnostic_asset",
                )
                if st.button("Lancer diagnostic", key="run_fail_diagnostic"):
                    scan_row = df[df["asset"] == selected_fail].iloc[0].to_dict()
                    scan_row["params"] = {
                        "sl_mult": scan_row.get("sl_mult"),
                        "tp1_mult": scan_row.get("tp1_mult"),
                        "tp2_mult": scan_row.get("tp2_mult"),
                        "tp3_mult": scan_row.get("tp3_mult"),
                        "tenkan": scan_row.get("tenkan"),
                        "kijun": scan_row.get("kijun"),
                        "tenkan_5": scan_row.get("tenkan_5"),
                        "kijun_5": scan_row.get("kijun_5"),
                    }
                    try:
                        data = load_asset_data(selected_fail)
                        params = _build_params_from_scan_row(scan_row)
                        df_is, _, df_oos = split_data_segments(data)
                        trades_is = _run_trades_for_params(df_is, params)
                        trades_oos = _run_trades_for_params(df_oos, params)
                        display_fail_diagnostic(
                            asset=selected_fail,
                            scan_result=scan_row,
                            data=data,
                            trades_is=trades_is,
                            trades_oos=trades_oos,
                        )
                    except Exception as diag_error:
                        st.error(f"Erreur diagnostic: {diag_error}")

        except Exception as e:
            st.error(f"Erreur lecture scan: {e}")


# -----------------------------------------------------------------------------
# DOWNLOAD DATA
# -----------------------------------------------------------------------------
elif page == "📥 Download OHLCV":
    st.title("📥 Télécharger les Données OHLCV")

    if st.session_state.get("active_session"):
        session = st.session_state.active_session
        render_progress_stepper(
            session.get("current_step", 1),
            session.get("steps_completed", []),
        )
        st.info(f"📂 Session active: **{session['name']}** — Assets: {', '.join(session['assets'])}")

    st.markdown("""
    Télécharge les données historiques depuis les exchanges (Binance, Bybit).
    Les données sont sauvegardées en format Parquet dans le dossier `data/`.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")

        available_data = get_available_data()
        if st.session_state.get("active_session"):
            session_assets = st.session_state.active_session.get("assets", [])
        else:
            session_assets = []

        options = []
        if session_assets:
            options.append("Assets de la session")
        options.extend([
            "Top 50 complet",
            "Assets validés (production)",
            "Sélection manuelle",
        ])

        default_index = 0 if session_assets else 1
        asset_option = st.radio(
            "Assets à télécharger",
            options,
            index=default_index,
        )

        if asset_option == "Assets de la session":
            selected_assets = session_assets
        elif asset_option == "Sélection manuelle":
            selected_assets = st.multiselect(
                "Choisir les assets",
                sorted(ALL_ASSETS),
                default=session_assets or ["BTC", "ETH"],
            )
        elif asset_option == "Top 50 complet":
            selected_assets = TOP50_ASSETS
        elif asset_option == "Assets validés (production)":
            selected_assets = VALIDATED_ASSETS
        else:
            selected_assets = available_data

        days_back = st.slider("Jours d'historique", 90, 1095, 730)

        output_format = st.radio("Format de sortie", ["parquet", "csv"])

    with col2:
        st.subheader("Assets sélectionnés")
        st.info(", ".join(selected_assets))

        st.subheader("Données existantes")
        existing = get_available_data()
        if existing:
            for asset in selected_assets:
                if asset in existing:
                    st.success(f"✓ {asset} (déjà présent)")
                else:
                    st.warning(f"○ {asset} (à télécharger)")
        else:
            st.warning("Aucune donnée existante")

    st.markdown("---")

    if st.button("🚀 Lancer le téléchargement", type="primary", use_container_width=True):
        console_log(f"Download {len(selected_assets)} assets", "RUN")
        with st.spinner("Téléchargement en cours..."):
            output_placeholder = st.empty()

            cmd = [
                sys.executable, "scripts/download_data.py",
                "--assets", *selected_assets,
                "--days", str(days_back),
                "--format", output_format,
            ]

            returncode, output = run_command(cmd, output_placeholder)

            if returncode == 0:
                st.success("✅ Téléchargement terminé!")
                st.balloons()

                # Update session progress
                advance_session_step(1, "data_loaded")

                st.markdown("---")
                if st.button("⚡ Continuer vers l'optimisation →", type="primary"):
                    st.session_state.current_page = "⚡ Bayesian"
                    st.rerun()
            else:
                st.error(f"❌ Erreur (code {returncode})")


# -----------------------------------------------------------------------------
# COMPARATEUR PINE VS PYTHON
# -----------------------------------------------------------------------------
elif page == "🔄 Comparateur Pine":
    st.title("🔄 Comparateur Pine Script vs Python")

    if st.session_state.get("active_session"):
        session = st.session_state.active_session
        render_progress_stepper(
            session.get("current_step", 1),
            session.get("steps_completed", []),
        )

    st.markdown("""
    Compare les signaux FINAL LONG/SHORT générés par Pine Script (TradingView)
    avec ceux générés par l'implémentation Python.

    **Format CSV attendu** (export TradingView):
    - Colonnes OHLCV: `time`, `open`, `high`, `low`, `close`
    - Signaux Pine: `FINAL LONG` (1/0), `FINAL SHORT` (1/0)
    """)

    st.markdown("---")

    # File upload
    uploaded_file = st.file_uploader(
        "📁 Uploader le CSV exporté de TradingView",
        type=["csv"],
        help="Le fichier doit contenir les colonnes OHLCV et les signaux FINAL LONG/SHORT"
    )

    col1, col2 = st.columns(2)

    with col1:
        warmup = st.slider(
            "Période de warmup (bougies à ignorer)",
            min_value=50,
            max_value=500,
            value=150,
            step=10,
            help="Les indicateurs MESA nécessitent ~150-300 bougies pour converger"
        )

    with col2:
        debug_trend = st.checkbox(
            "Mode debug (Ichimoku trend state)",
            value=False,
            help="Compare aussi l'état de tendance Ichimoku si disponible"
        )

    if uploaded_file is not None:
        st.markdown("---")

        try:
            # Load uploaded file
            import io
            import numpy as np

            df = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode("utf-8")))
            df.columns = [col.strip() for col in df.columns]

            st.success(f"✅ Fichier chargé: {len(df)} lignes")

            # Show preview
            with st.expander("📋 Aperçu des données"):
                st.dataframe(df.head(20), use_container_width=True)
                st.caption(f"Colonnes: {', '.join(df.columns.tolist())}")

            # Check required columns
            required_ohlc = {"open", "high", "low", "close"}
            required_signals = {"FINAL LONG", "FINAL SHORT"}

            missing_ohlc = required_ohlc - set(df.columns)
            missing_signals = required_signals - set(df.columns)

            if missing_ohlc:
                st.error(f"❌ Colonnes OHLC manquantes: {missing_ohlc}")
                st.stop()

            if missing_signals:
                st.error(f"❌ Colonnes signaux manquantes: {missing_signals}")
                st.info("Le CSV doit contenir les colonnes 'FINAL LONG' et 'FINAL SHORT' exportées de Pine Script")
                st.stop()

            # Run comparison
            if st.button("🚀 Lancer la comparaison", type="primary", use_container_width=True):
                with st.spinner("Comparaison en cours..."):
                    # Import comparison logic
                    from crypto_backtest.indicators.five_in_one import FiveInOneConfig
                    from crypto_backtest.strategies.final_trigger import (
                        FinalTriggerParams,
                        FinalTriggerStrategy,
                    )

                    # Prepare OHLCV data
                    data = df.copy()
                    if "volume" not in data.columns:
                        data["volume"] = 0.0
                    if "time" in data.columns:
                        time_series = data["time"]
                        if pd.api.types.is_numeric_dtype(time_series):
                            time_unit = "ms" if time_series.max() >= 1_000_000_000_000 else "s"
                            data["time"] = pd.to_datetime(time_series, unit=time_unit, utc=True, errors="coerce")
                        else:
                            data["time"] = pd.to_datetime(time_series, utc=True, errors="coerce")
                        data = data.dropna(subset=["time"]).set_index("time")

                    ohlcv = data[["open", "high", "low", "close", "volume"]]

                    # Build strategy with default params
                    five_in_one = FiveInOneConfig(
                        use_distance_filter=False,
                        use_volume_filter=False,
                        use_regression_cloud=False,
                        use_kama_oscillator=False,
                        use_ichimoku_filter=True,
                        ichi5in1_strict=False,
                        use_transition_mode=False,
                    )
                    params = FinalTriggerParams(
                        grace_bars=1,
                        use_mama_kama_filter=False,
                        require_fama_between=False,
                        strict_lock_5in1_last=False,
                        five_in_one=five_in_one,
                    )
                    strategy = FinalTriggerStrategy(params)

                    # Generate Python signals
                    signals_df = strategy.generate_signals(ohlcv)
                    signals_py = signals_df["signal"].to_numpy()

                    # Get Pine signals
                    final_long_pine = df["FINAL LONG"].fillna(0).astype(int).values
                    final_short_pine = df["FINAL SHORT"].fillna(0).astype(int).values

                    # Compare (after warmup)
                    long_py = (signals_py == 1)[warmup:]
                    short_py = (signals_py == -1)[warmup:]
                    long_pine = final_long_pine[warmup:]
                    short_pine = final_short_pine[warmup:]

                    # Calculate matches
                    long_match = int(np.sum(long_py & (long_pine == 1)))
                    short_match = int(np.sum(short_py & (short_pine == 1)))
                    long_total_pine = int(np.sum(long_pine == 1))
                    short_total_pine = int(np.sum(short_pine == 1))
                    long_total_py = int(np.sum(long_py))
                    short_total_py = int(np.sum(short_py))

                    long_rate = (long_match / max(long_total_pine, 1)) * 100.0
                    short_rate = (short_match / max(short_total_pine, 1)) * 100.0

                    st.markdown("---")
                    st.subheader("📊 Résultats de la Comparaison")

                    # Metrics
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("#### 🟢 LONG Signals")
                        st.metric("Python", long_total_py)
                        st.metric("Pine Script", long_total_pine)
                        if long_rate >= 95:
                            st.success(f"Match: {long_rate:.1f}%")
                        elif long_rate >= 80:
                            st.warning(f"Match: {long_rate:.1f}%")
                        else:
                            st.error(f"Match: {long_rate:.1f}%")

                    with col2:
                        st.markdown("#### 🔴 SHORT Signals")
                        st.metric("Python", short_total_py)
                        st.metric("Pine Script", short_total_pine)
                        if short_rate >= 95:
                            st.success(f"Match: {short_rate:.1f}%")
                        elif short_rate >= 80:
                            st.warning(f"Match: {short_rate:.1f}%")
                        else:
                            st.error(f"Match: {short_rate:.1f}%")

                    with col3:
                        st.markdown("#### 📈 Global")
                        total_pine = long_total_pine + short_total_pine
                        total_match = long_match + short_match
                        global_rate = (total_match / max(total_pine, 1)) * 100.0
                        st.metric("Total Signaux Pine", total_pine)
                        st.metric("Signaux Matchés", total_match)
                        if global_rate >= 95:
                            st.success(f"Match Global: {global_rate:.1f}%")

                            # Update session progress
                            advance_session_step(4, "validated")

                            st.markdown("---")
                            st.success("🎉 Validation Pine Script réussie !")
                            if st.button("🚀 Voir le résumé final →", type="primary"):
                                st.session_state.current_page = "📊 Dashboard"
                                st.rerun()
                        elif global_rate >= 80:
                            st.warning(f"Match Global: {global_rate:.1f}%")
                        else:
                            st.error(f"Match Global: {global_rate:.1f}%")

                    # Show divergences
                    st.markdown("---")
                    st.subheader("🔍 Analyse des Divergences")

                    # Find divergence indices
                    long_diverge = (long_py != (long_pine == 1))
                    short_diverge = (short_py != (short_pine == 1))

                    long_div_count = int(np.sum(long_diverge))
                    short_div_count = int(np.sum(short_diverge))

                    if long_div_count == 0 and short_div_count == 0:
                        st.success("✅ Aucune divergence après warmup! Les signaux sont identiques.")
                    else:
                        st.warning(f"⚠️ {long_div_count} divergences LONG, {short_div_count} divergences SHORT")

                        # Create divergence report
                        report_data = []
                        for i in range(len(long_py)):
                            actual_idx = warmup + i
                            if long_diverge[i] or short_diverge[i]:
                                report_data.append({
                                    "Index": actual_idx,
                                    "Time": ohlcv.index[actual_idx] if actual_idx < len(ohlcv) else "N/A",
                                    "Close": float(ohlcv.iloc[actual_idx]["close"]) if actual_idx < len(ohlcv) else 0,
                                    "Python LONG": bool(long_py[i]),
                                    "Pine LONG": bool(long_pine[i]),
                                    "Python SHORT": bool(short_py[i]),
                                    "Pine SHORT": bool(short_pine[i]),
                                })

                        if report_data:
                            report_df = pd.DataFrame(report_data[:100])  # Limit to 100
                            st.dataframe(report_df, use_container_width=True)

                            if len(report_data) > 100:
                                st.caption(f"Affichage limité aux 100 premières divergences sur {len(report_data)}")

                            # Download button
                            full_report = pd.DataFrame(report_data)
                            csv = full_report.to_csv(index=False)
                            st.download_button(
                                "📥 Télécharger le rapport complet",
                                csv,
                                file_name="pine_python_divergences.csv",
                                mime="text/csv",
                            )

        except Exception as e:
            st.error(f"❌ Erreur lors du traitement: {e}")
            import traceback
            st.code(traceback.format_exc())

    else:
        st.info("👆 Uploadez un fichier CSV pour commencer la comparaison")

        # Show example format
        with st.expander("📝 Exemple de format CSV"):
            example_df = pd.DataFrame({
                "time": [1704067200000, 1704070800000, 1704074400000],
                "open": [42000.0, 42100.0, 42050.0],
                "high": [42150.0, 42200.0, 42100.0],
                "low": [41950.0, 42000.0, 41980.0],
                "close": [42100.0, 42050.0, 42080.0],
                "FINAL LONG": [0, 1, 0],
                "FINAL SHORT": [0, 0, 0],
            })
            st.dataframe(example_df, use_container_width=True)


# -----------------------------------------------------------------------------
# OPTIMIZATION - BAYESIAN
# -----------------------------------------------------------------------------
elif page == "⚡ Bayesian":
    st.title("⚡ Optimisation Bayésienne")

    if st.session_state.get("active_session"):
        session = st.session_state.active_session
        render_progress_stepper(
            session.get("current_step", 1),
            session.get("steps_completed", []),
        )
        st.info(f"📂 Session active: **{session['name']}**")

    st.markdown("""
    Lance l'optimisation des paramètres ATR et Ichimoku sur les assets sélectionnés.
    Utilise Optuna (TPE) pour trouver les meilleurs paramètres.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")

        # Check available data
        available_data = get_available_data()

        if not available_data:
            st.error("⚠️ Aucune donnée disponible. Téléchargez d'abord les données.")
            st.stop()

        if st.session_state.get("active_session"):
            session_assets = st.session_state.active_session.get("assets", [])
            default_assets = [a for a in session_assets if a in available_data]
        else:
            default_assets = [a for a in SCAN_ASSETS if a in available_data][:3]

        selected_assets = st.multiselect(
            "Assets à optimiser",
            available_data,
            default=default_assets,
        )

        trials_atr = st.slider("Trials ATR", 20, 200, 100)
        trials_ichi = st.slider("Trials Ichimoku", 20, 200, 100)

        import os
        max_workers = max(os.cpu_count() or 4, get_default_workers("bayesian"))
        workers = st.slider(
            "Workers (parallélisme)",
            1,
            max_workers,
            get_default_workers("bayesian"),
        )

        skip_download = st.checkbox("Skip download (données déjà présentes)", value=True)

        st.markdown("---")
        st.markdown("##### Options avancées")

        include_displacement = st.checkbox(
            "Inclure Displacement dans l'optimisation",
            value=False,
            help="Ajoute le paramètre displacement (26, 39, 52, 65, 78) à l'espace de recherche Bayésien. "
                 "Attention: augmente significativement le temps d'optimisation."
        )

        if include_displacement:
            displacement_values = st.multiselect(
                "Valeurs de displacement",
                [26, 39, 52, 65, 78],
                default=[26, 39, 52, 65, 78],
                help="Sélectionnez les valeurs à inclure dans l'optimisation"
            )
        else:
            displacement_values = [52]  # Default

    with col2:
        st.subheader("Espace de recherche")

        st.markdown("""
        **ATR Parameters:**
        - SL mult: 1.5 - 5.0
        - TP1 mult: 1.5 - 5.0
        - TP2 mult: 3.0 - 12.0
        - TP3 mult: 2.0 - 10.0

        **Ichimoku Parameters:**
        - Tenkan: 5 - 20
        - Kijun: 20 - 40
        - Tenkan 5in1: 8 - 16
        - Kijun 5in1: 15 - 30
        """)

        if include_displacement:
            st.markdown(f"""
            **Displacement (activé):**
            - Valeurs: {', '.join(map(str, displacement_values))}
            """)
            st.warning("⚠️ L'ajout du displacement multiplie l'espace de recherche. "
                      f"Avec {len(displacement_values)} valeurs, le temps d'optimisation augmente d'environ {len(displacement_values)}x.")

    st.markdown("---")

    if not selected_assets:
        st.warning("Sélectionnez au moins un asset")
    else:
        if st.button("🚀 Lancer l'optimisation", type="primary", use_container_width=True):
            console_log(f"Bayesian optim: {', '.join(selected_assets[:3])}...", "RUN")
            with st.spinner(f"Optimisation de {len(selected_assets)} assets..."):
                output_placeholder = st.empty()

                cmd = [
                    sys.executable, "scripts/run_full_pipeline.py",
                    "--assets", *selected_assets,
                    "--trials-atr", str(trials_atr),
                    "--trials-ichi", str(trials_ichi),
                    "--workers", str(workers),
                ]

                if skip_download:
                    cmd.append("--skip-download")

                if include_displacement and len(displacement_values) > 1:
                    cmd.extend(["--displacement-values", ",".join(map(str, displacement_values))])
                    st.info(f"Displacement inclus dans l'optimisation: {displacement_values}")

                returncode, output = run_command(cmd, output_placeholder)

                if returncode == 0:
                    st.success("✅ Optimisation terminée!")
                    link_outputs_to_session(["multiasset_scan_*.csv", "pine_plan_*.csv"])

                    scan_results = get_scan_results()
                    has_pass = False
                    pass_mask = None
                    df = None
                    if scan_results:
                        df = pd.read_csv(scan_results[0])
                        if "status" in df.columns:
                            pass_mask = df["status"].astype(str).str.startswith("SUCCESS")
                        else:
                            pass_mask = (
                                (df["oos_sharpe"] >= PASS_CRITERIA["oos_sharpe_min"]) &
                                (df["wfe"] >= PASS_CRITERIA["wfe_min"])
                            )
                        has_pass = pass_mask.any()

                        st.subheader("📊 Résultats")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Assets PASS", int(pass_mask.sum()))
                        with col2:
                            st.metric("Assets FAIL", int((~pass_mask).sum()))

                        st.dataframe(
                            df[["asset", "oos_sharpe", "wfe", "oos_return"]].style.format({
                                "oos_sharpe": "{:.2f}",
                                "wfe": "{:.2f}",
                                "oos_return": "{:.1f}%",
                            }),
                            use_container_width=True,
                        )

                    st.markdown("---")

                    if has_pass:
                        st.balloons()
                        advance_session_step(2, "optimized")
                        console_log(
                            f"Optimisation OK: {int(pass_mask.sum())} assets PASS",
                            "OK",
                        )

                        if st.button(
                            "🛡️ Continuer vers les Guards →",
                            type="primary",
                            use_container_width=True,
                        ):
                            st.session_state.current_page = "🛡️ Guards"
                            st.rerun()
                    else:
                        st.warning(
                            "⚠️ Aucun asset n'a passé les critères (Sharpe ≥ 1.0 ET WFE ≥ 0.6)"
                        )
                        console_log("Optimisation: 0 assets PASS", "WARN")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(
                                "🔄 Réessayer avec plus de trials",
                                use_container_width=True,
                            ):
                                st.rerun()
                        with col2:
                            if st.button(
                                "🛡️ Forcer Guards quand même",
                                use_container_width=True,
                            ):
                                advance_session_step(2, "optimized")
                                st.session_state.current_page = "🛡️ Guards"
                                st.rerun()

                        if df is not None and pass_mask is not None:
                            fail_assets = df.loc[~pass_mask, "asset"].tolist()
                            if fail_assets:
                                st.markdown("---")
                                st.subheader("🔍 Diagnostic FAIL")
                                selected_fail = st.selectbox(
                                    "Asset FAIL",
                                    fail_assets,
                                    key="bayes_fail_diagnostic_asset",
                                )
                                if st.button(
                                    "Lancer diagnostic",
                                    key="bayes_run_fail_diagnostic",
                                ):
                                    scan_row = df[df["asset"] == selected_fail].iloc[0].to_dict()
                                    scan_row["params"] = {
                                        "sl_mult": scan_row.get("sl_mult"),
                                        "tp1_mult": scan_row.get("tp1_mult"),
                                        "tp2_mult": scan_row.get("tp2_mult"),
                                        "tp3_mult": scan_row.get("tp3_mult"),
                                        "tenkan": scan_row.get("tenkan"),
                                        "kijun": scan_row.get("kijun"),
                                        "tenkan_5": scan_row.get("tenkan_5"),
                                        "kijun_5": scan_row.get("kijun_5"),
                                    }
                                    try:
                                        data = load_asset_data(selected_fail)
                                        params = _build_params_from_scan_row(scan_row)
                                        df_is, _, df_oos = split_data_segments(data)
                                        trades_is = _run_trades_for_params(df_is, params)
                                        trades_oos = _run_trades_for_params(df_oos, params)
                                        display_fail_diagnostic(
                                            asset=selected_fail,
                                            scan_result=scan_row,
                                            data=data,
                                            trades_is=trades_is,
                                            trades_oos=trades_oos,
                                        )
                                    except Exception as diag_error:
                                        st.error(f"Erreur diagnostic: {diag_error}")
                else:
                    st.error(f"❌ Erreur (code {returncode})")


# -----------------------------------------------------------------------------
# DISPLACEMENT GRID OPTIMIZATION
# -----------------------------------------------------------------------------
elif page == "🎚️ Displacement Grid":
    st.title("🎚️ Optimisation Displacement Grid")

    st.markdown("""
    **Priorité P1** - Optimise le paramètre `displacement` de l'Ichimoku sur les assets validés.

    Le displacement contrôle la projection du nuage (Kumo) dans le futur.
    Valeurs testées: **26, 39, 52 (défaut), 65, 78**
    """)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")

        # Assets selection
        available_data = get_available_data()

        if not available_data:
            st.error("⚠️ Aucune donnée disponible. Téléchargez d'abord les données.")
            st.stop()

        # Default to validated assets
        default_assets = [a for a in VALIDATED_ASSETS if a in available_data]

        selected_assets = st.multiselect(
            "Assets à tester",
            available_data,
            default=default_assets,
        )

        displacement_values = st.multiselect(
            "Valeurs de displacement à tester",
            [26, 39, 52, 65, 78],
            default=[26, 39, 52, 65, 78],
        )

        import os
        max_workers = max(os.cpu_count() or 4, get_default_workers("displacement_grid"))
        workers = st.slider(
            "Workers",
            1,
            max_workers,
            get_default_workers("displacement_grid"),
        )

    with col2:
        st.subheader("Explication")

        st.markdown("""
        **Impact du Displacement:**

        | Valeur | Effet |
        |--------|-------|
        | 26 | Plus réactif, signaux plus fréquents |
        | 39 | Intermédiaire |
        | **52** | Standard Ichimoku (défaut) |
        | 65 | Plus conservateur |
        | 78 | Très lent, moins de trades |

        **Critère de succès:**
        Amélioration du Sharpe OOS > 0.1 par rapport au défaut (52)
        """)

    st.markdown("---")

    if not selected_assets:
        st.warning("Sélectionnez au moins un asset")
    elif not displacement_values:
        st.warning("Sélectionnez au moins une valeur de displacement")
    else:
        if st.button("🚀 Lancer le Grid Search", type="primary", use_container_width=True):
            with st.spinner(f"Test de {len(displacement_values)} valeurs sur {len(selected_assets)} assets..."):

                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_placeholder = st.empty()

                results = []
                total_tests = len(selected_assets) * len(displacement_values)
                current_test = 0

                try:
                    from crypto_backtest.engine.backtest import BacktestConfig, VectorizedBacktester
                    from crypto_backtest.analysis.metrics import compute_metrics
                    from crypto_backtest.optimization.parallel_optimizer import load_data, build_strategy_params
                    from crypto_backtest.optimization.bayesian import _instantiate_strategy
                    from crypto_backtest.strategies.final_trigger import FinalTriggerStrategy
                    from crypto_backtest.config.scan_assets import OPTIM_CONFIG

                    base_config = BacktestConfig(
                        initial_capital=10000.0,
                        fees_bps=5.0,
                        slippage_bps=2.0,
                        sizing_mode="fixed",
                    )

                    for asset in selected_assets:
                        status_text.text(f"Testing {asset}...")

                        # Load data
                        data = load_data(asset, "data")
                        if data.index.tz is None:
                            data.index = data.index.tz_localize("UTC")
                        warmup = OPTIM_CONFIG["warmup_bars"]
                        data = data.iloc[warmup:]

                        for disp in displacement_values:
                            current_test += 1
                            progress_bar.progress(current_test / total_tests)

                            # Build params with this displacement
                            params = build_strategy_params(
                                sl_mult=2.5,
                                tp1_mult=2.0,
                                tp2_mult=6.0,
                                tp3_mult=10.0,
                                tenkan=9,
                                kijun=26,
                                tenkan_5=12,
                                kijun_5=26,
                                displacement=disp,  # Variable
                            )

                            strategy = _instantiate_strategy(FinalTriggerStrategy, params)
                            backtester = VectorizedBacktester(base_config)
                            result = backtester.run(data, strategy)

                            metrics = compute_metrics(result.equity_curve, result.trades)

                            results.append({
                                "asset": asset,
                                "displacement": disp,
                                "sharpe": float(metrics.get("sharpe_ratio", 0) or 0),
                                "return_pct": float(metrics.get("total_return", 0) or 0) * 100,
                                "max_dd_pct": float(metrics.get("max_drawdown", 0) or 0) * 100,
                                "trades": len(result.trades),
                            })

                    progress_bar.progress(1.0)
                    status_text.text("✅ Terminé!")

                    # Display results
                    st.markdown("---")
                    st.subheader("📊 Résultats")

                    results_df = pd.DataFrame(results)

                    # Find best displacement per asset
                    best_per_asset = results_df.loc[results_df.groupby("asset")["sharpe"].idxmax()]

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### Meilleur Displacement par Asset")
                        st.dataframe(
                            best_per_asset[["asset", "displacement", "sharpe", "return_pct"]].style.format({
                                "sharpe": "{:.2f}",
                                "return_pct": "{:.1f}%",
                            }),
                            use_container_width=True,
                        )

                    with col2:
                        st.markdown("#### Comparaison vs Défaut (52)")
                        default_results = results_df[results_df["displacement"] == 52].set_index("asset")["sharpe"]

                        comparison = []
                        for _, row in best_per_asset.iterrows():
                            default_sharpe = default_results.get(row["asset"], 0)
                            improvement = row["sharpe"] - default_sharpe
                            comparison.append({
                                "asset": row["asset"],
                                "best_disp": int(row["displacement"]),
                                "best_sharpe": row["sharpe"],
                                "default_sharpe": default_sharpe,
                                "improvement": improvement,
                                "status": "✅" if improvement > 0.1 else "➖",
                            })

                        comp_df = pd.DataFrame(comparison)
                        st.dataframe(
                            comp_df.style.format({
                                "best_sharpe": "{:.2f}",
                                "default_sharpe": "{:.2f}",
                                "improvement": "{:+.2f}",
                            }),
                            use_container_width=True,
                        )

                    # Full results table
                    st.markdown("---")
                    st.subheader("📋 Résultats Complets")

                    # Pivot table
                    pivot = results_df.pivot(index="asset", columns="displacement", values="sharpe")
                    st.dataframe(
                        pivot.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=1),
                        use_container_width=True,
                    )

                    # Download
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Télécharger les résultats",
                        csv,
                        file_name="displacement_grid_results.csv",
                        mime="text/csv",
                    )

                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
                    import traceback
                    st.code(traceback.format_exc())


# -----------------------------------------------------------------------------
# GUARDS
# -----------------------------------------------------------------------------
elif page == "🛡️ Guards":
    st.title("🛡️ Tests de Robustesse (Guards)")

    if st.session_state.get("active_session"):
        session = st.session_state.active_session
        render_progress_stepper(
            session.get("current_step", 1),
            session.get("steps_completed", []),
        )
        st.info(f"📂 Session active: **{session['name']}**")

    st.markdown("""
    Exécute les 7 tests de validation sur les assets optimisés:
    - **GUARD-001**: Monte Carlo (p-value < 0.05)
    - **GUARD-002**: Sensitivity (variance < 10%)
    - **GUARD-003**: Bootstrap CI (Sharpe lower > 1.0)
    - **GUARD-005**: Trade Distribution (top 10 < 40%)
    - **GUARD-006**: Stress Test (Sharpe stress1 > 1.0)
    - **GUARD-007**: Regime Reconciliation (mismatch < 1%)
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")

        # Find params file
        params_files = sorted(Path("outputs").glob("pine_plan*.csv"), reverse=True)

        if not params_files:
            st.error("⚠️ Aucun fichier de paramètres trouvé. Lancez d'abord l'optimisation.")
            st.stop()

        params_file = st.selectbox(
            "Fichier de paramètres",
            params_files,
            format_func=lambda x: x.name,
        )

        # Read assets from params file
        try:
            params_df = pd.read_csv(params_file)
            available_assets = params_df["asset"].tolist()
        except Exception:
            available_assets = []

        if not available_assets:
            st.error("Impossible de lire les assets depuis le fichier")
            st.stop()

        if st.session_state.get("active_session"):
            session_assets = st.session_state.active_session.get("assets", [])
            default_assets = [a for a in session_assets if a in available_assets]
        else:
            default_assets = available_assets

        selected_assets = st.multiselect(
            "Assets à valider",
            available_assets,
            default=default_assets,
        )

        import os
        max_workers = max(os.cpu_count() or 4, get_default_workers("guards"))
        workers = st.slider("Workers", 1, max_workers, get_default_workers("guards"))

    with col2:
        st.subheader("Résultats précédents")
        guards_df = get_guards_results()
        if guards_df is not None:
            guard_cols = get_guard_display_columns(guards_df)
            st.dataframe(
                guards_df[guard_cols],
                use_container_width=True,
            )
        else:
            st.info("Aucun résultat précédent")

    st.markdown("---")

    if not selected_assets:
        st.warning("Sélectionnez au moins un asset")
    else:
        if st.button("🚀 Lancer les Guards", type="primary", use_container_width=True):
            console_log(f"Guards validation: {len(selected_assets)} assets", "RUN")
            with st.spinner(f"Validation de {len(selected_assets)} assets..."):
                output_placeholder = st.empty()

                cmd = [
                    sys.executable, "scripts/run_guards_multiasset.py",
                    "--assets", *selected_assets,
                    "--params-file", str(params_file),
                    "--workers", str(workers),
                ]

                returncode, output = run_command(cmd, output_placeholder)

                if returncode == 0:
                    st.success("✅ Guards terminés!")
                    st.balloons()

                    # Update session progress
                    advance_session_step(3, "guards_complete")
                    link_outputs_to_session([
                        "*_montecarlo.csv",
                        "*_montecarlo_*.csv",
                        "*_sensitivity.csv",
                        "*_sensitivity_*.csv",
                        "*_bootstrap.csv",
                        "*_bootstrap_*.csv",
                        "*_tradedist.csv",
                        "*_tradedist_*.csv",
                        "*_stresstest.csv",
                        "*_stresstest_*.csv",
                        "*_regime.csv",
                        "*_regime_*.csv",
                        "multiasset_guards_summary.csv",
                        "multiasset_guards_summary_*.csv",
                    ])

                    st.markdown("---")
                    if st.button("✅ Continuer vers la validation Pine →", type="primary"):
                        st.session_state.current_page = "🔄 Comparateur Pine"
                        st.rerun()

                    # Show results
                    guards_df = get_guards_results()
                    if guards_df is not None:
                        st.subheader("Résultats")

                        # Color code pass/fail
                        def highlight_pass(val):
                            if val is True:
                                return "background-color: #90EE90"
                            elif val is False:
                                return "background-color: #FFB6C1"
                            return ""

                        st.dataframe(
                            guards_df.style.applymap(
                                highlight_pass,
                                subset=[c for c in guards_df.columns if "pass" in c]
                            ),
                            use_container_width=True,
                        )
                else:
                    st.error(f"❌ Erreur (code {returncode})")


# -----------------------------------------------------------------------------
# RESULTS
# -----------------------------------------------------------------------------
elif page == "📈 Fichiers":
    st.title("📈 Visualisation des Résultats")

    outputs_dir = Path("outputs")

    if not outputs_dir.exists():
        st.warning("Aucun résultat disponible. Lancez d'abord une optimisation.")
        st.stop()

    # Tabs for different result types
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Scan Results", "🛡️ Guards", "📋 Parameters", "📁 Fichiers"])

    with tab1:
        st.subheader("Résultats de Scan")
        scan_results = get_scan_results()

        if scan_results:
            selected_scan = st.selectbox(
                "Sélectionner un scan",
                scan_results,
                format_func=lambda x: x.name,
            )

            df = pd.read_csv(selected_scan)

            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Assets", len(df))
            with col2:
                pass_count = ((df["oos_sharpe"] >= 1.0) & (df["wfe"] >= 0.6)).sum()
                st.metric("PASS", pass_count)
            with col3:
                avg_sharpe = df["oos_sharpe"].mean()
                st.metric("Avg Sharpe", f"{avg_sharpe:.2f}")
            with col4:
                avg_wfe = df["wfe"].mean()
                st.metric("Avg WFE", f"{avg_wfe:.2f}")

            st.dataframe(df, use_container_width=True)

            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Télécharger CSV",
                csv,
                file_name=selected_scan.name,
                mime="text/csv",
            )
        else:
            st.info("Aucun scan disponible")

    with tab2:
        st.subheader("Résultats Guards")
        guards_df = get_guards_results()

        if guards_df is not None:
            run_id = None
            if "run_id" in guards_df.columns:
                run_id_series = guards_df["run_id"].dropna()
                if not run_id_series.empty:
                    run_id = str(run_id_series.iloc[0])
            # Summary
            col1, col2 = st.columns(2)
            with col1:
                passed = guards_df["all_pass"].sum()
                st.metric("Assets Validés", f"{passed}/{len(guards_df)}")
            with col2:
                pass_rate = passed / len(guards_df) * 100
                st.metric("Taux de Réussite", f"{pass_rate:.0f}%")

            st.dataframe(guards_df, use_container_width=True)

            # Per-asset details
            st.markdown("---")
            st.subheader("Détails par Asset")

            selected_asset = st.selectbox(
                "Asset",
                guards_df["asset"].tolist(),
            )

            # Load individual guard files
            guard_files = {
                "Monte Carlo": "montecarlo",
                "Sensitivity": "sensitivity",
                "Bootstrap": "bootstrap",
                "Trade Dist": "tradedist",
                "Stress Test": "stresstest",
                "Regime": "regime",
            }

            for name, guard_key in guard_files.items():
                filepath = resolve_guard_file(outputs_dir, selected_asset, guard_key, run_id)
                if filepath is not None and filepath.exists():
                    with st.expander(f"📋 {name}"):
                        st.caption(filepath.name)
                        st.dataframe(pd.read_csv(filepath), use_container_width=True)
        else:
            st.info("Aucun résultat de guards disponible")

    with tab3:
        st.subheader("Paramètres Optimaux")

        params_files = sorted(outputs_dir.glob("pine_plan*.csv"), reverse=True)

        if params_files:
            selected_params = st.selectbox(
                "Fichier de paramètres",
                params_files,
                format_func=lambda x: x.name,
            )

            df = pd.read_csv(selected_params)
            st.dataframe(df, use_container_width=True)

            # Download
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Télécharger CSV",
                csv,
                file_name=selected_params.name,
                mime="text/csv",
            )
        else:
            st.info("Aucun fichier de paramètres disponible")

    with tab4:
        st.subheader("Tous les Fichiers Output")

        all_files = sorted(outputs_dir.glob("*.*"))

        if all_files:
            file_data = []
            for f in all_files:
                file_data.append({
                    "Fichier": f.name,
                    "Taille": f"{f.stat().st_size / 1024:.1f} KB",
                    "Modifié": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                })

            st.dataframe(pd.DataFrame(file_data), use_container_width=True)
        else:
            st.info("Aucun fichier")


# -----------------------------------------------------------------------------
# COMPARAISON
# -----------------------------------------------------------------------------
elif page == "🏆 Comparaison Assets":
    st.title("🏆 Comparaison des Assets")

    st.markdown("""
    Compare et trie tous les assets testés par performance, paramètres, et métriques de robustesse.
    """)

    outputs_dir = Path("outputs")

    # Load all available data
    scan_results = get_scan_results()
    guards_df = get_guards_results()

    if not scan_results:
        st.warning("Aucun résultat de scan disponible. Lancez d'abord une optimisation.")
        st.stop()

    # Load scan data
    scan_df = pd.read_csv(scan_results[0])

    # Merge with guards if available
    if guards_df is not None:
        guard_cols = get_guard_display_columns(guards_df)
        merge_cols = [col for col in guard_cols if col != "asset"]
        merged_df = scan_df.merge(
            guards_df[["asset"] + merge_cols],
            on="asset",
            how="left"
        )
    else:
        merged_df = scan_df.copy()
        merged_df["all_pass"] = None

    st.markdown("---")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🔍 Filtres")

        min_sharpe = st.slider(
            "Sharpe OOS minimum",
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.1,
        )

        min_wfe = st.slider(
            "WFE minimum",
            min_value=-2.0,
            max_value=3.0,
            value=0.0,
            step=0.1,
        )

    with col2:
        st.subheader("📊 Tri")

        sort_column = st.selectbox(
            "Trier par",
            options=[
                "oos_sharpe",
                "wfe",
                "oos_return",
                "oos_max_dd",
                "is_sharpe",
                "oos_trades",
            ],
            format_func=lambda x: {
                "oos_sharpe": "Sharpe OOS",
                "wfe": "Walk-Forward Efficiency",
                "oos_return": "Return OOS (%)",
                "oos_max_dd": "Max Drawdown OOS",
                "is_sharpe": "Sharpe IS",
                "oos_trades": "Nombre de trades",
            }.get(x, x)
        )

        sort_order = st.radio("Ordre", ["Décroissant", "Croissant"], horizontal=True)

    with col3:
        st.subheader("🏷️ Statut")

        show_pass_only = st.checkbox("Afficher seulement les PASS", value=False)
        show_guards_pass = st.checkbox("Afficher seulement guards OK", value=False)

    # Apply filters
    filtered_df = merged_df.copy()

    if "oos_sharpe" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["oos_sharpe"] >= min_sharpe]

    if "wfe" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["wfe"] >= min_wfe]

    if show_pass_only:
        filtered_df = filtered_df[
            (filtered_df["oos_sharpe"] >= PASS_CRITERIA["oos_sharpe_min"]) &
            (filtered_df["wfe"] >= PASS_CRITERIA["wfe_min"])
        ]

    if show_guards_pass and "all_pass" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["all_pass"] == True]

    # Sort
    if sort_column in filtered_df.columns:
        filtered_df = filtered_df.sort_values(
            sort_column,
            ascending=(sort_order == "Croissant")
        )

    st.markdown("---")

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Assets affichés", len(filtered_df))
    with col2:
        if "oos_sharpe" in filtered_df.columns and len(filtered_df) > 0:
            st.metric("Sharpe moyen", f"{filtered_df['oos_sharpe'].mean():.2f}")
    with col3:
        if "wfe" in filtered_df.columns and len(filtered_df) > 0:
            st.metric("WFE moyen", f"{filtered_df['wfe'].mean():.2f}")
    with col4:
        if "all_pass" in filtered_df.columns:
            guards_ok = filtered_df["all_pass"].sum() if filtered_df["all_pass"].notna().any() else 0
            st.metric("Guards OK", int(guards_ok))

    st.markdown("---")

    # Display columns selection
    available_cols = filtered_df.columns.tolist()
    default_cols = ["asset", "oos_sharpe", "wfe", "oos_return", "oos_max_dd", "oos_trades"]
    if "all_pass" in available_cols:
        default_cols.append("all_pass")

    display_cols = st.multiselect(
        "Colonnes à afficher",
        available_cols,
        default=[c for c in default_cols if c in available_cols],
    )

    if display_cols:
        display_df = filtered_df[display_cols].copy()

        # Color coding for performance
        def highlight_performance(row):
            styles = []
            for col in row.index:
                if col == "oos_sharpe":
                    if row[col] >= 2.0:
                        styles.append("background-color: #90EE90")  # Green
                    elif row[col] >= 1.0:
                        styles.append("background-color: #FFFFE0")  # Light yellow
                    elif row[col] < 0:
                        styles.append("background-color: #FFB6C1")  # Light red
                    else:
                        styles.append("")
                elif col == "wfe":
                    if row[col] >= 1.0:
                        styles.append("background-color: #90EE90")
                    elif row[col] >= 0.6:
                        styles.append("background-color: #FFFFE0")
                    elif row[col] < 0:
                        styles.append("background-color: #FFB6C1")
                    else:
                        styles.append("")
                elif col == "all_pass":
                    if row[col] == True:
                        styles.append("background-color: #90EE90")
                    elif row[col] == False:
                        styles.append("background-color: #FFB6C1")
                    else:
                        styles.append("")
                else:
                    styles.append("")
            return styles

        styled_df = display_df.style.apply(highlight_performance, axis=1)

        # Format numeric columns
        format_dict = {}
        for col in display_df.columns:
            if col in ["oos_sharpe", "is_sharpe", "wfe"]:
                format_dict[col] = "{:.2f}"
            elif col in ["oos_return", "is_return", "oos_max_dd", "is_max_dd"]:
                format_dict[col] = "{:.1f}%"

        if format_dict:
            styled_df = styled_df.format(format_dict)

        st.dataframe(styled_df, use_container_width=True, height=500)

        # Download
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📥 Télécharger les résultats filtrés",
            csv,
            file_name="comparison_filtered.csv",
            mime="text/csv",
        )

    st.markdown("---")

    # Parameter comparison
    st.subheader("📐 Comparaison des Paramètres")

    params_files = sorted(outputs_dir.glob("pine_plan*.csv"), reverse=True)

    if params_files:
        params_df = pd.read_csv(params_files[0])

        # Merge with performance
        if "asset" in params_df.columns and "asset" in filtered_df.columns:
            params_merged = params_df.merge(
                filtered_df[["asset", "oos_sharpe", "wfe"]],
                on="asset",
                how="inner"
            )

            if not params_merged.empty:
                st.markdown("**Paramètres par asset (triés par performance)**")

                params_merged = params_merged.sort_values("oos_sharpe", ascending=False)
                st.dataframe(params_merged, use_container_width=True)

                # Parameter distribution
                st.markdown("---")
                st.subheader("📊 Distribution des Paramètres")

                param_cols = ["sl_mult", "tp1_mult", "tp2_mult", "tp3_mult", "tenkan", "kijun"]
                available_param_cols = [c for c in param_cols if c in params_merged.columns]

                if available_param_cols:
                    col1, col2 = st.columns(2)

                    with col1:
                        selected_param = st.selectbox("Paramètre", available_param_cols)

                    with col2:
                        st.markdown(f"**Stats pour {selected_param}:**")
                        st.write(f"- Min: {params_merged[selected_param].min():.2f}")
                        st.write(f"- Max: {params_merged[selected_param].max():.2f}")
                        st.write(f"- Moyenne: {params_merged[selected_param].mean():.2f}")
                        st.write(f"- Médiane: {params_merged[selected_param].median():.2f}")

                    # Simple bar chart
                    import plotly.express as px

                    fig = px.bar(
                        params_merged,
                        x="asset",
                        y=selected_param,
                        color="oos_sharpe",
                        color_continuous_scale="RdYlGn",
                        title=f"{selected_param} par Asset (coloré par Sharpe OOS)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun fichier de paramètres disponible")


# -----------------------------------------------------------------------------
# PORTFOLIO BUILDER
# -----------------------------------------------------------------------------
elif page == "💼 Portfolio Builder":
    st.title("💼 Portfolio Builder")

    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown("""
    Construis un portfolio optimisé en sélectionnant des assets complémentaires (faible corrélation).
    """)

    outputs_dir = Path("outputs")
    scan_results = get_scan_results()

    if not scan_results:
        st.warning("Aucun résultat de scan disponible. Lancez d'abord une optimisation.")
        st.stop()

    scan_df = pd.read_csv(scan_results[0])

    st.markdown("---")

    # Tabs
    portfolio_tabs = st.tabs(["📊 Corrélations", "🤖 Auto-Sélection", "✋ Sélection Manuelle"])

    # -------------------------------------------------------------------------
    # TAB 1: Correlations
    # -------------------------------------------------------------------------
    with portfolio_tabs[0]:
        st.subheader("Matrice de Corrélation des Returns")

        # Load equity curves if available
        equity_files = list(outputs_dir.glob("*_equity.csv"))

        if not equity_files:
            st.info("""
            Les fichiers d'equity curves ne sont pas encore générés.

            Pour calculer les corrélations, vous devez d'abord lancer un backtest complet
            qui sauvegarde les equity curves dans `outputs/`.

            **Alternative**: Utilisez les corrélations basées sur les métriques disponibles.
            """)

            # Use metrics correlation as fallback
            if len(scan_df) > 2:
                metric_cols = ["oos_sharpe", "wfe", "oos_return", "oos_max_dd"]
                available_metrics = [c for c in metric_cols if c in scan_df.columns]

                if available_metrics:
                    corr_data = scan_df.set_index("asset")[available_metrics].T
                    asset_corr = corr_data.corr()

                    st.markdown("#### Corrélation basée sur les métriques")

                    fig = px.imshow(
                        asset_corr,
                        title="Corrélation des profils de performance",
                        color_continuous_scale="RdBu_r",
                        aspect="auto",
                        text_auto=".2f",
                        zmin=-1, zmax=1,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.caption("Note: Cette corrélation est basée sur les métriques de performance, pas sur les returns journaliers.")

        else:
            # Load and compute real correlations
            returns_dict = {}
            for eq_file in equity_files:
                asset = eq_file.stem.replace("_equity", "")
                try:
                    eq_df = pd.read_csv(eq_file, parse_dates=["time"], index_col="time")
                    returns = eq_df["equity"].pct_change().dropna()
                    returns_dict[asset] = returns
                except Exception:
                    continue

            if returns_dict:
                returns_df = pd.DataFrame(returns_dict)
                corr_matrix = returns_df.corr()

                fig = px.imshow(
                    corr_matrix,
                    title="Corrélation des Returns",
                    color_continuous_scale="RdBu_r",
                    aspect="auto",
                    text_auto=".2f",
                    zmin=-1, zmax=1,
                )
                st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: Auto Selection
    # -------------------------------------------------------------------------
    with portfolio_tabs[1]:
        st.subheader("🤖 Sélection Automatique d'Assets Complémentaires")

        st.markdown("""
        L'algorithme sélectionne les meilleurs assets en maximisant le Sharpe
        tout en minimisant la corrélation entre eux.
        """)

        if len(scan_df) < 2:
            st.warning(
                "⚠️ Minimum 2 assets requis pour construire un portfolio. "
                "Lancez d'abord un scan multi-assets."
            )
            st.stop()

        col1, col2 = st.columns(2)

        with col1:
            max_assets = st.slider(
                "Nombre maximum d'assets",
                min_value=2,
                max_value=max(2, min(15, len(scan_df))),
                value=min(5, len(scan_df)),
            )

            min_sharpe = st.slider(
                "Sharpe minimum requis",
                min_value=0.0,
                max_value=3.0,
                value=1.0,
                step=0.1,
            )

            max_correlation = st.slider(
                "Corrélation maximum entre assets",
                min_value=0.1,
                max_value=1.0,
                value=0.7,
                step=0.05,
            )

        with col2:
            st.markdown("""
            **Algorithme:**
            1. Filtre les assets avec Sharpe >= seuil
            2. Trie par Sharpe décroissant
            3. Ajoute les assets un par un si corrélation < max
            4. S'arrête quand nombre max atteint
            """)

        if st.button("🚀 Lancer la sélection automatique", type="primary"):
            # Filter by sharpe
            candidates = scan_df[scan_df["oos_sharpe"] >= min_sharpe].copy()
            candidates = candidates.sort_values("oos_sharpe", ascending=False)

            if len(candidates) == 0:
                st.warning(f"Aucun asset avec Sharpe >= {min_sharpe}")
            else:
                # Simple greedy selection (using metric correlation as proxy)
                selected = [candidates.iloc[0]["asset"]]

                metric_cols = ["oos_sharpe", "wfe", "oos_return", "oos_max_dd"]
                available_metrics = [c for c in metric_cols if c in candidates.columns]

                if available_metrics and len(candidates) > 1:
                    profile_data = candidates.set_index("asset")[available_metrics]

                    for _, row in candidates.iloc[1:].iterrows():
                        if len(selected) >= max_assets:
                            break

                        asset = row["asset"]
                        asset_profile = profile_data.loc[asset]

                        # Check correlation with all selected
                        max_corr_found = 0
                        for sel_asset in selected:
                            sel_profile = profile_data.loc[sel_asset]
                            corr = np.corrcoef(asset_profile.values, sel_profile.values)[0, 1]
                            max_corr_found = max(max_corr_found, abs(corr))

                        if max_corr_found < max_correlation:
                            selected.append(asset)

                st.success(f"✅ {len(selected)} assets sélectionnés")

                # Display selected
                selected_df = scan_df[scan_df["asset"].isin(selected)].copy()
                selected_df = selected_df.sort_values("oos_sharpe", ascending=False)

                st.dataframe(
                    selected_df[["asset", "oos_sharpe", "wfe", "oos_return", "oos_max_dd", "oos_trades"]].style.format({
                        "oos_sharpe": "{:.2f}",
                        "wfe": "{:.2f}",
                        "oos_return": "{:.1f}%",
                        "oos_max_dd": "{:.1f}%",
                    }),
                    use_container_width=True,
                )

                # Portfolio metrics
                st.markdown("---")
                st.subheader("📊 Métriques du Portfolio")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    avg_sharpe = selected_df["oos_sharpe"].mean()
                    st.metric("Sharpe Moyen", f"{avg_sharpe:.2f}")

                with col2:
                    total_trades = selected_df["oos_trades"].sum()
                    st.metric("Total Trades", int(total_trades))

                with col3:
                    avg_return = selected_df["oos_return"].mean()
                    st.metric("Return Moyen", f"{avg_return:.1f}%")

                with col4:
                    max_dd = selected_df["oos_max_dd"].max()
                    st.metric("Pire DD", f"{max_dd:.1f}%")

    # -------------------------------------------------------------------------
    # TAB 3: Manual Selection
    # -------------------------------------------------------------------------
    with portfolio_tabs[2]:
        st.subheader("✋ Sélection Manuelle du Portfolio")

        # Multi-select assets
        available_assets = scan_df["asset"].tolist()

        selected_assets = st.multiselect(
            "Sélectionnez vos assets",
            available_assets,
            default=available_assets[:3] if len(available_assets) >= 3 else available_assets,
        )

        if selected_assets:
            selected_df = scan_df[scan_df["asset"].isin(selected_assets)].copy()

            st.markdown("---")
            st.subheader("📊 Métriques du Pack Sélectionné")

            # Summary metrics
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Assets", len(selected_df))

            with col2:
                avg_sharpe = selected_df["oos_sharpe"].mean()
                st.metric("Sharpe Moyen", f"{avg_sharpe:.2f}")

            with col3:
                total_trades = selected_df["oos_trades"].sum()
                st.metric("Total Trades", int(total_trades))

            with col4:
                # Estimate combined Profit Factor
                if "oos_pf" in selected_df.columns:
                    avg_pf = selected_df["oos_pf"].mean()
                else:
                    avg_pf = 1.5  # Placeholder
                st.metric("Profit Factor Moy.", f"{avg_pf:.2f}")

            with col5:
                avg_wfe = selected_df["wfe"].mean()
                st.metric("WFE Moyen", f"{avg_wfe:.2f}")

            st.markdown("---")

            # Detailed table
            st.subheader("📋 Détails par Asset")

            display_cols = ["asset", "oos_sharpe", "wfe", "oos_return", "oos_max_dd", "oos_trades"]
            display_cols = [c for c in display_cols if c in selected_df.columns]

            st.dataframe(
                selected_df[display_cols].style.format({
                    "oos_sharpe": "{:.2f}",
                    "wfe": "{:.2f}",
                    "oos_return": "{:.1f}%",
                    "oos_max_dd": "{:.1f}%",
                }),
                use_container_width=True,
            )

            # Correlation heatmap for selected
            if len(selected_df) > 1:
                st.markdown("---")
                st.subheader("🔗 Corrélation du Pack")

                metric_cols = ["oos_sharpe", "wfe", "oos_return", "oos_max_dd"]
                available_metrics = [c for c in metric_cols if c in selected_df.columns]

                if available_metrics:
                    profile_data = selected_df.set_index("asset")[available_metrics].T
                    pack_corr = profile_data.corr()

                    fig = px.imshow(
                        pack_corr,
                        title="Corrélation entre assets sélectionnés",
                        color_continuous_scale="RdBu_r",
                        aspect="auto",
                        text_auto=".2f",
                        zmin=-1, zmax=1,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Average correlation
                    mask = np.triu(np.ones_like(pack_corr, dtype=bool), k=1)
                    upper_corr = pack_corr.where(mask)
                    avg_corr = upper_corr.stack().mean()

                    if avg_corr < 0.3:
                        st.success(f"✅ Excellente diversification (corrélation moyenne: {avg_corr:.2f})")
                    elif avg_corr < 0.6:
                        st.info(f"ℹ️ Bonne diversification (corrélation moyenne: {avg_corr:.2f})")
                    else:
                        st.warning(f"⚠️ Assets trop corrélés (corrélation moyenne: {avg_corr:.2f})")

            # Risk summary
            st.markdown("---")
            st.subheader("⚠️ Analyse de Risque")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Points forts:**")
                strengths = []
                if avg_sharpe >= 1.5:
                    strengths.append(f"- Sharpe élevé ({avg_sharpe:.2f})")
                if avg_wfe >= 0.8:
                    strengths.append(f"- Robustesse validée (WFE {avg_wfe:.2f})")
                if len(selected_df) >= 3:
                    strengths.append(f"- Diversification ({len(selected_df)} assets)")
                if total_trades >= 100:
                    strengths.append(f"- Volume de trades suffisant ({int(total_trades)})")

                if strengths:
                    for s in strengths:
                        st.markdown(s)
                else:
                    st.markdown("- Aucun point fort notable")

            with col2:
                st.markdown("**Points d'attention:**")
                weaknesses = []
                if avg_sharpe < 1.0:
                    weaknesses.append(f"- Sharpe faible ({avg_sharpe:.2f})")
                if avg_wfe < 0.6:
                    weaknesses.append(f"- Risque d'overfit (WFE {avg_wfe:.2f})")
                if len(selected_df) < 3:
                    weaknesses.append(f"- Concentration ({len(selected_df)} assets)")
                max_dd = selected_df["oos_max_dd"].max()
                if max_dd > 10:
                    weaknesses.append(f"- Drawdown élevé ({max_dd:.1f}%)")

                if weaknesses:
                    for w in weaknesses:
                        st.markdown(w)
                else:
                    st.markdown("- Aucun point d'attention majeur")

            # Export
            st.markdown("---")
            csv = selected_df.to_csv(index=False)
            st.download_button(
                "📥 Exporter le portfolio",
                csv,
                file_name="portfolio_selection.csv",
                mime="text/csv",
            )

        else:
            st.info("👆 Sélectionnez des assets pour voir les métriques combinées")


# -----------------------------------------------------------------------------
# VISUALISATION
# -----------------------------------------------------------------------------
elif page == "📉 Visualisation":
    st.title("📉 Visualisation des Résultats")

    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    outputs_dir = Path("outputs")

    st.markdown("""
    Graphiques interactifs pour analyser les performances et les paramètres.
    """)

    # Check data availability
    scan_results = get_scan_results()
    if not scan_results:
        st.warning("Aucun résultat disponible. Lancez d'abord une optimisation.")
        st.stop()

    scan_df = pd.read_csv(scan_results[0])
    guards_df = get_guards_results()

    # Merge data
    if guards_df is not None:
        full_df = scan_df.merge(guards_df, on="asset", how="left")
    else:
        full_df = scan_df.copy()

    # Tabs for different visualizations
    viz_tabs = st.tabs([
        "📊 Performance Overview",
        "🎯 Sharpe vs WFE",
        "📐 Paramètres",
        "🛡️ Guards Heatmap",
        "📈 Rankings",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: Performance Overview
    # -------------------------------------------------------------------------
    with viz_tabs[0]:
        st.subheader("Vue d'ensemble des Performances")

        col1, col2 = st.columns(2)

        with col1:
            # Bar chart: Sharpe by asset
            fig_sharpe = px.bar(
                full_df.sort_values("oos_sharpe", ascending=True),
                x="oos_sharpe",
                y="asset",
                orientation="h",
                title="Sharpe Ratio OOS par Asset",
                color="oos_sharpe",
                color_continuous_scale="RdYlGn",
                labels={"oos_sharpe": "Sharpe OOS", "asset": "Asset"},
            )
            fig_sharpe.add_vline(x=1.0, line_dash="dash", line_color="gray",
                                annotation_text="Seuil PASS (1.0)")
            st.plotly_chart(fig_sharpe, use_container_width=True)

        with col2:
            # Bar chart: WFE by asset
            fig_wfe = px.bar(
                full_df.sort_values("wfe", ascending=True),
                x="wfe",
                y="asset",
                orientation="h",
                title="Walk-Forward Efficiency par Asset",
                color="wfe",
                color_continuous_scale="RdYlGn",
                labels={"wfe": "WFE", "asset": "Asset"},
            )
            fig_wfe.add_vline(x=0.6, line_dash="dash", line_color="gray",
                             annotation_text="Seuil PASS (0.6)")
            st.plotly_chart(fig_wfe, use_container_width=True)

        # Return vs Max Drawdown scatter
        st.subheader("Return vs Max Drawdown")

        if "oos_return" in full_df.columns and "oos_max_dd" in full_df.columns:
            fig_risk = px.scatter(
                full_df,
                x="oos_max_dd",
                y="oos_return",
                text="asset",
                color="oos_sharpe",
                size="oos_trades" if "oos_trades" in full_df.columns else None,
                color_continuous_scale="RdYlGn",
                title="Return vs Max Drawdown (taille = nb trades)",
                labels={
                    "oos_return": "Return OOS (%)",
                    "oos_max_dd": "Max Drawdown (%)",
                    "oos_sharpe": "Sharpe",
                },
            )
            fig_risk.update_traces(textposition="top center")
            st.plotly_chart(fig_risk, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: Sharpe vs WFE
    # -------------------------------------------------------------------------
    with viz_tabs[1]:
        st.subheader("Sharpe OOS vs Walk-Forward Efficiency")

        st.markdown("""
        Ce graphique montre la relation entre la performance (Sharpe) et la robustesse (WFE).
        - **Zone verte** = Assets validés (Sharpe > 1.0 ET WFE > 0.6)
        - Les assets dans le coin supérieur droit sont les meilleurs candidats
        """)

        fig_scatter = px.scatter(
            full_df,
            x="wfe",
            y="oos_sharpe",
            text="asset",
            color="oos_sharpe",
            color_continuous_scale="RdYlGn",
            title="Sharpe OOS vs WFE",
            labels={"wfe": "Walk-Forward Efficiency", "oos_sharpe": "Sharpe OOS"},
        )

        # Add quadrant lines
        fig_scatter.add_hline(y=1.0, line_dash="dash", line_color="gray")
        fig_scatter.add_vline(x=0.6, line_dash="dash", line_color="gray")

        # Add green zone annotation
        fig_scatter.add_shape(
            type="rect",
            x0=0.6, y0=1.0, x1=full_df["wfe"].max() + 0.5, y1=full_df["oos_sharpe"].max() + 0.5,
            fillcolor="green",
            opacity=0.1,
            line_width=0,
        )

        fig_scatter.update_traces(textposition="top center", marker=dict(size=15))
        fig_scatter.update_layout(height=600)
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Quadrant analysis
        st.markdown("### Analyse par Quadrant")

        col1, col2, col3, col4 = st.columns(4)

        pass_mask = (full_df["oos_sharpe"] >= 1.0) & (full_df["wfe"] >= 0.6)
        high_perf_low_robust = (full_df["oos_sharpe"] >= 1.0) & (full_df["wfe"] < 0.6)
        low_perf_high_robust = (full_df["oos_sharpe"] < 1.0) & (full_df["wfe"] >= 0.6)
        fail_mask = (full_df["oos_sharpe"] < 1.0) & (full_df["wfe"] < 0.6)

        with col1:
            st.metric("✅ PASS", pass_mask.sum())
            if pass_mask.any():
                st.caption(", ".join(full_df[pass_mask]["asset"].tolist()))

        with col2:
            st.metric("⚠️ Overfit", high_perf_low_robust.sum())
            if high_perf_low_robust.any():
                st.caption(", ".join(full_df[high_perf_low_robust]["asset"].tolist()))

        with col3:
            st.metric("📉 Low Perf", low_perf_high_robust.sum())
            if low_perf_high_robust.any():
                st.caption(", ".join(full_df[low_perf_high_robust]["asset"].tolist()))

        with col4:
            st.metric("❌ FAIL", fail_mask.sum())
            if fail_mask.any():
                st.caption(", ".join(full_df[fail_mask]["asset"].tolist()))

    # -------------------------------------------------------------------------
    # TAB 3: Parameters
    # -------------------------------------------------------------------------
    with viz_tabs[2]:
        st.subheader("Distribution des Paramètres")

        params_files = sorted(outputs_dir.glob("pine_plan*.csv"), reverse=True)

        if params_files:
            params_df = pd.read_csv(params_files[0])

            # Merge with performance
            params_merged = params_df.merge(
                full_df[["asset", "oos_sharpe", "wfe"]],
                on="asset",
                how="inner"
            )

            param_options = ["sl_mult", "tp1_mult", "tp2_mult", "tp3_mult", "tenkan", "kijun", "tenkan_5", "kijun_5"]
            available_params = [p for p in param_options if p in params_merged.columns]

            if available_params:
                col1, col2 = st.columns(2)

                with col1:
                    # Histogram of selected parameter
                    selected_param = st.selectbox("Paramètre à visualiser", available_params)

                    fig_hist = px.histogram(
                        params_merged,
                        x=selected_param,
                        nbins=15,
                        title=f"Distribution de {selected_param}",
                        color_discrete_sequence=["#636EFA"],
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

                with col2:
                    # Scatter: Parameter vs Sharpe
                    fig_param_sharpe = px.scatter(
                        params_merged,
                        x=selected_param,
                        y="oos_sharpe",
                        text="asset",
                        color="wfe",
                        color_continuous_scale="RdYlGn",
                        title=f"{selected_param} vs Sharpe OOS",
                        labels={"oos_sharpe": "Sharpe OOS"},
                    )
                    fig_param_sharpe.update_traces(textposition="top center")
                    st.plotly_chart(fig_param_sharpe, use_container_width=True)

                # Correlation heatmap of parameters
                st.subheader("Corrélation entre Paramètres et Performance")

                corr_cols = available_params + ["oos_sharpe", "wfe"]
                corr_df = params_merged[corr_cols].corr()

                fig_corr = px.imshow(
                    corr_df,
                    title="Matrice de Corrélation",
                    color_continuous_scale="RdBu_r",
                    aspect="auto",
                    text_auto=".2f",
                )
                st.plotly_chart(fig_corr, use_container_width=True)

        else:
            st.info("Aucun fichier de paramètres disponible")

    # -------------------------------------------------------------------------
    # TAB 4: Guards Heatmap
    # -------------------------------------------------------------------------
    with viz_tabs[3]:
        st.subheader("Heatmap des Guards")

        if guards_df is not None:
            guard_cols = [c for c in guards_df.columns if c.endswith("_pass") and c != "all_pass"]

            if guard_cols:
                # Prepare data for heatmap
                heatmap_data = guards_df[["asset"] + guard_cols].copy()

                # Convert to numeric (True=1, False=0)
                for col in guard_cols:
                    heatmap_data[col] = heatmap_data[col].astype(int)

                # Rename columns for display
                col_names = {
                    "guard001_pass": "Monte Carlo",
                    "guard002_pass": "Sensitivity",
                    "guard003_pass": "Bootstrap CI",
                    "guard005_pass": "Trade Dist",
                    "guard006_pass": "Stress Test",
                    "guard007_pass": "Regime",
                }
                heatmap_data = heatmap_data.rename(columns=col_names)

                # Set asset as index
                heatmap_data = heatmap_data.set_index("asset")

                # Create heatmap
                fig_heatmap = px.imshow(
                    heatmap_data,
                    title="Guards: Vert = PASS, Rouge = FAIL",
                    color_continuous_scale=["#FFB6C1", "#90EE90"],
                    aspect="auto",
                    labels={"color": "Status"},
                )
                fig_heatmap.update_layout(height=400)
                st.plotly_chart(fig_heatmap, use_container_width=True)

                # Summary
                st.subheader("Résumé par Guard")

                guard_summary = []
                for col in heatmap_data.columns:
                    pass_rate = heatmap_data[col].mean() * 100
                    guard_summary.append({
                        "Guard": col,
                        "PASS": heatmap_data[col].sum(),
                        "FAIL": len(heatmap_data) - heatmap_data[col].sum(),
                        "Taux de réussite": f"{pass_rate:.0f}%",
                    })

                st.dataframe(pd.DataFrame(guard_summary), use_container_width=True)

        else:
            st.info("Aucun résultat de guards disponible")

    # -------------------------------------------------------------------------
    # TAB 5: Rankings
    # -------------------------------------------------------------------------
    with viz_tabs[4]:
        st.subheader("Classement des Assets")

        # Multi-criteria ranking
        st.markdown("""
        Classement composite basé sur plusieurs critères:
        - Sharpe OOS (40%)
        - WFE (30%)
        - Return OOS (20%)
        - Max DD inversé (10%)
        """)

        ranking_df = full_df.copy()

        # Normalize metrics (0-1 scale)
        for col in ["oos_sharpe", "wfe", "oos_return"]:
            if col in ranking_df.columns:
                col_min = ranking_df[col].min()
                col_max = ranking_df[col].max()
                if col_max > col_min:
                    ranking_df[f"{col}_norm"] = (ranking_df[col] - col_min) / (col_max - col_min)
                else:
                    ranking_df[f"{col}_norm"] = 0.5

        # Invert max_dd (lower is better)
        if "oos_max_dd" in ranking_df.columns:
            col_min = ranking_df["oos_max_dd"].min()
            col_max = ranking_df["oos_max_dd"].max()
            if col_max > col_min:
                ranking_df["max_dd_norm"] = 1 - (ranking_df["oos_max_dd"] - col_min) / (col_max - col_min)
            else:
                ranking_df["max_dd_norm"] = 0.5

        # Composite score
        ranking_df["score"] = (
            ranking_df.get("oos_sharpe_norm", 0) * 0.4 +
            ranking_df.get("wfe_norm", 0) * 0.3 +
            ranking_df.get("oos_return_norm", 0) * 0.2 +
            ranking_df.get("max_dd_norm", 0) * 0.1
        )

        ranking_df = ranking_df.sort_values("score", ascending=False)

        # Display ranking
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 🥇 Top 10")
            top10 = ranking_df.head(10)[["asset", "score", "oos_sharpe", "wfe"]].reset_index(drop=True)
            top10.index = top10.index + 1  # Start from 1
            st.dataframe(top10, use_container_width=True)

        with col2:
            # Bar chart of scores
            fig_ranking = px.bar(
                ranking_df.head(15),
                x="asset",
                y="score",
                color="score",
                color_continuous_scale="Viridis",
                title="Score Composite (Top 15)",
            )
            st.plotly_chart(fig_ranking, use_container_width=True)

        # Radar chart for top 5
        st.subheader("Profil des Top 5 Assets")

        top5 = ranking_df.head(5)
        categories = ["Sharpe", "WFE", "Return", "Low DD"]

        fig_radar = go.Figure()

        for _, row in top5.iterrows():
            values = [
                row.get("oos_sharpe_norm", 0),
                row.get("wfe_norm", 0),
                row.get("oos_return_norm", 0),
                row.get("max_dd_norm", 0),
            ]
            values.append(values[0])  # Close the polygon

            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill="toself",
                name=row["asset"],
            ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            title="Profil Radar des Top 5",
        )
        st.plotly_chart(fig_radar, use_container_width=True)


# -----------------------------------------------------------------------------
# HISTORIQUE DES SESSIONS
# -----------------------------------------------------------------------------
elif page == "📋 Historique":
    st.title("📋 Historique des Sessions")

    if st.session_state.get("active_session"):
        render_progress_stepper(
            st.session_state.active_session.get("current_step", 1),
            st.session_state.active_session.get("steps_completed", []),
        )

    st.markdown("""
    Parcourez l'historique de toutes vos sessions de backtesting et validation.
    """)

    sessions = list_sessions()

    if not sessions:
        st.info("🔍 Aucune session trouvée. Créez votre première session depuis le Dashboard.")
        if st.button("➕ Créer une session", type="primary"):
            st.session_state.show_new_session_modal = True
            st.rerun()
        st.stop()

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filtrer par statut",
            ["Tous", "En cours", "Guards OK", "Validé", "Déployé"],
        )

    with col2:
        all_assets = set()
        for session in sessions:
            all_assets.update(session.get("assets", []))

        asset_filter = st.multiselect(
            "Filtrer par asset",
            sorted(all_assets),
            default=[],
        )

    with col3:
        sort_by = st.selectbox(
            "Trier par",
            ["Date (récent)", "Date (ancien)", "Nom", "Progression"],
        )

    filtered_sessions = sessions.copy()

    if status_filter != "Tous":
        status_map = {
            "En cours": ["created", "data_loaded", "optimized"],
            "Guards OK": ["guards_complete"],
            "Validé": ["validated"],
            "Déployé": ["deployed"],
        }
        allowed_statuses = status_map.get(status_filter, [])
        filtered_sessions = [
            session for session in filtered_sessions
            if session.get("status") in allowed_statuses
        ]

    if asset_filter:
        filtered_sessions = [
            session for session in filtered_sessions
            if any(asset in session.get("assets", []) for asset in asset_filter)
        ]

    if sort_by == "Date (récent)":
        filtered_sessions.sort(key=lambda x: x.get("created", ""), reverse=True)
    elif sort_by == "Date (ancien)":
        filtered_sessions.sort(key=lambda x: x.get("created", ""))
    elif sort_by == "Nom":
        filtered_sessions.sort(key=lambda x: x.get("name", "").lower())
    elif sort_by == "Progression":
        filtered_sessions.sort(key=lambda x: x.get("current_step", 0), reverse=True)

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Sessions", len(sessions))
    with col2:
        completed = len([s for s in sessions if s.get("current_step", 0) >= 4])
        st.metric("Validées", completed)
    with col3:
        in_progress = len([s for s in sessions if 1 <= s.get("current_step", 0) < 4])
        st.metric("En cours", in_progress)
    with col4:
        st.metric("Assets testés", len(all_assets))

    st.markdown("---")

    if "compare_sessions" not in st.session_state:
        st.session_state.compare_sessions = []

    if "confirm_delete_session" not in st.session_state:
        st.session_state.confirm_delete_session = None

    compare_mode = st.checkbox("🔀 Mode comparaison", value=False)

    if compare_mode and len(st.session_state.compare_sessions) >= 2:
        if st.button("📊 Comparer les sessions sélectionnées", type="primary"):
            st.session_state.show_comparison = True

    st.markdown("---")

    st.subheader(f"📂 Sessions ({len(filtered_sessions)})")

    for session in filtered_sessions:
        session_id = session["id"]
        is_active = (
            st.session_state.get("active_session")
            and st.session_state.active_session.get("id") == session_id
        )

        status_config = {
            "created": {"color": "#4299E1", "icon": "🔵", "label": "Créée"},
            "data_loaded": {"color": "#ECC94B", "icon": "🟡", "label": "Données OK"},
            "optimized": {"color": "#ED8936", "icon": "🟠", "label": "Optimisée"},
            "guards_complete": {"color": "#48BB78", "icon": "🟢", "label": "Guards OK"},
            "validated": {"color": "#38A169", "icon": "✅", "label": "Validée"},
            "deployed": {"color": "#9F7AEA", "icon": "🚀", "label": "Déployée"},
        }
        status = session.get("status", "created")
        status_info = status_config.get(status, status_config["created"])

        border_color = "#00D4FF" if is_active else "#2D3748"
        border_width = "2px" if is_active else "1px"

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
            border: {border_width} solid {border_color};
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <span style="color: #FFFFFF; font-weight: 600; font-size: 1.1rem;">
                        {session['name']}
                    </span>
                    {' <span style="color: #00D4FF; font-size: 0.75rem; padding: 2px 8px; background: rgba(0,212,255,0.2); border-radius: 4px;">ACTIVE</span>' if is_active else ''}
                </div>
                <span style="
                    color: {status_info['color']};
                    font-size: 0.85rem;
                    padding: 4px 10px;
                    background: rgba(255,255,255,0.05);
                    border-radius: 6px;
                ">
                    {status_info['icon']} {status_info['label']}
                </span>
            </div>
            <div style="color: #A0AEC0; font-size: 0.85rem; margin-top: 8px;">
                📊 {', '.join(session.get('assets', [])[:5])}{'...' if len(session.get('assets', [])) > 5 else ''}
            </div>
            <div style="color: #718096; font-size: 0.75rem; margin-top: 4px;">
                📅 {datetime.fromisoformat(session['created']).strftime('%d/%m/%Y %H:%M')} - Étape {session.get('current_step', 1)}/5
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if is_active:
                st.button("✓ Active", key=f"active_{session_id}", disabled=True)
            else:
                if st.button("📂 Charger", key=f"load_{session_id}", use_container_width=True):
                    st.session_state.active_session = session
                    console_log(f"Session chargée: {session['name']}", "OK")
                    st.rerun()

        with col2:
            if st.button("▶️ Continuer", key=f"continue_{session_id}", use_container_width=True):
                st.session_state.active_session = session
                step_pages = {
                    1: "📥 Download OHLCV",
                    2: "⚡ Bayesian",
                    3: "🛡️ Guards",
                    4: "🔄 Comparateur Pine",
                    5: "📊 Dashboard",
                }
                st.session_state.current_page = step_pages.get(
                    session.get("current_step", 1),
                    "📊 Dashboard",
                )
                st.rerun()

        with col3:
            if st.button("📋 Détails", key=f"details_{session_id}", use_container_width=True):
                st.session_state.selected_session_details = session_id

        with col4:
            if compare_mode:
                is_selected = session_id in st.session_state.compare_sessions
                if st.checkbox("", value=is_selected, key=f"cmp_{session_id}"):
                    if session_id not in st.session_state.compare_sessions:
                        st.session_state.compare_sessions.append(session_id)
                else:
                    if session_id in st.session_state.compare_sessions:
                        st.session_state.compare_sessions.remove(session_id)

        with col5:
            if st.session_state.confirm_delete_session == session_id:
                if st.button("Confirmer", key=f"confirm_{session_id}", use_container_width=True):
                    delete_session(session_id)
                    if is_active:
                        st.session_state.active_session = None
                    st.session_state.confirm_delete_session = None
                    console_log(f"Session supprimée: {session['name']}", "WARN")
                    st.rerun()
            else:
                if st.button("🗑️", key=f"del_{session_id}", help="Supprimer", use_container_width=True):
                    st.session_state.confirm_delete_session = session_id

        if st.session_state.get("selected_session_details") == session_id:
            with st.expander("📋 Détails de la session", expanded=True):
                det_col1, det_col2 = st.columns(2)

                with det_col1:
                    st.markdown("**Informations**")
                    st.write(f"- **ID:** `{session['id']}`")
                    st.write(f"- **Créée:** {datetime.fromisoformat(session['created']).strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"- **Assets:** {', '.join(session.get('assets', []))}")
                    st.write(f"- **Étapes complétées:** {session.get('steps_completed', [])}")

                with det_col2:
                    st.markdown("**Notes**")
                    notes = session.get("notes", "")
                    new_notes = st.text_area("", value=notes, key=f"notes_{session_id}", height=100)
                    if new_notes != notes:
                        session["notes"] = new_notes
                        save_session(session)
                        st.success("Notes sauvegardées")

                session_dir = get_session_dir(session_id)
                if session_dir.exists():
                    files = list(session_dir.glob("*.csv"))
                    if files:
                        st.markdown("**Fichiers associés**")
                        for file_path in files[:10]:
                            st.caption(f"📄 {file_path.name}")

                if st.button("Fermer", key=f"close_details_{session_id}"):
                    st.session_state.selected_session_details = None
                    st.rerun()

        st.markdown("")

    if st.session_state.get("show_comparison") and len(st.session_state.compare_sessions) >= 2:
        st.markdown("---")
        st.subheader("🔀 Comparaison de Sessions")

        sessions_to_compare = [
            load_session(session_id)
            for session_id in st.session_state.compare_sessions[:2]
        ]

        if all(sessions_to_compare):
            col1, col2 = st.columns(2)

            for col, sess in zip([col1, col2], sessions_to_compare):
                with col:
                    st.markdown(f"### {sess['name']}")
                    st.write(f"**Status:** {sess.get('status', 'N/A')}")
                    st.write(f"**Assets:** {', '.join(sess.get('assets', []))}")
                    st.write(f"**Étape:** {sess.get('current_step', 1)}/5")
                    st.write(f"**Créée:** {datetime.fromisoformat(sess['created']).strftime('%d/%m/%Y')}")

        if st.button("Fermer la comparaison"):
            st.session_state.show_comparison = False
            st.session_state.compare_sessions = []
            st.rerun()


# =============================================================================
# SIDEBAR FOOTER - Session Stats
# =============================================================================
display_history_sidebar()
st.sidebar.markdown("---")

if st.session_state.get("active_session"):
    session = st.session_state.active_session
    completed = len(session.get("steps_completed", []))

    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1A1F2E 0%, #0E1117 100%);
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    ">
        <div style="color: #A0AEC0; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">
            Progression
        </div>
        <div style="
            background: #2D3748;
            border-radius: 4px;
            height: 8px;
            margin: 8px 0;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, #00D4FF 0%, #00FF88 100%);
                height: 100%;
                width: {completed * 20}%;
                transition: width 0.3s ease;
            "></div>
        </div>
        <div style="color: #718096; font-size: 12px; text-align: center;">
            {completed}/5 étapes complétées
        </div>
    </div>
    """, unsafe_allow_html=True)

render_console_panel()

st.sidebar.caption(f"v2.0 | {datetime.now().strftime('%Y-%m-%d')}")
