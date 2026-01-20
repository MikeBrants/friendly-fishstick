"""
FINAL TRIGGER v2 - Backtest Dashboard
Interface visuelle pour piloter les backtests crypto

Usage:
    streamlit run app.py
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from crypto_backtest.config.scan_assets import (
    ALL_ASSETS,
    SCAN_ASSETS,
    VALIDATED_ASSETS,
    PASS_CRITERIA,
)

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
# SIDEBAR
# =============================================================================
st.sidebar.title("🎯 FINAL TRIGGER v2")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📥 Download Data", "⚡ Optimization", "🛡️ Guards", "📈 Results"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Assets Validés")
st.sidebar.success("BTC, ETH, AVAX, UNI, SEI")

st.sidebar.markdown("### Critères de Validation")
st.sidebar.info(f"""
- OOS Sharpe > {PASS_CRITERIA['oos_sharpe_min']}
- WFE > {PASS_CRITERIA['wfe_min']}
- Max DD < {PASS_CRITERIA['max_dd_max']*100:.0f}%
- Trades > {PASS_CRITERIA['oos_trades_min']}
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


def get_guards_results():
    """Get guards summary if exists."""
    path = Path("outputs/multiasset_guards_summary.csv")
    if path.exists():
        return pd.read_csv(path)
    return None


def run_command(cmd: list, placeholder):
    """Run a command and stream output to Streamlit."""
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

    process.wait()
    return process.returncode, "".join(output_lines)


# =============================================================================
# PAGES
# =============================================================================

# -----------------------------------------------------------------------------
# DASHBOARD
# -----------------------------------------------------------------------------
if page == "📊 Dashboard":
    st.title("📊 Dashboard Principal")

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

        except Exception as e:
            st.error(f"Erreur lecture scan: {e}")


# -----------------------------------------------------------------------------
# DOWNLOAD DATA
# -----------------------------------------------------------------------------
elif page == "📥 Download Data":
    st.title("📥 Télécharger les Données OHLCV")

    st.markdown("""
    Télécharge les données historiques depuis les exchanges (Binance, Bybit).
    Les données sont sauvegardées en format Parquet dans le dossier `data/`.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")

        asset_option = st.radio(
            "Assets à télécharger",
            ["Tous les assets", "Assets validés (BTC/ETH/XRP)", "Nouveaux alts (scan)", "Sélection manuelle"],
        )

        if asset_option == "Sélection manuelle":
            selected_assets = st.multiselect(
                "Choisir les assets",
                ALL_ASSETS,
                default=["BTC", "ETH"],
            )
        elif asset_option == "Assets validés (BTC/ETH/XRP)":
            selected_assets = VALIDATED_ASSETS
        elif asset_option == "Nouveaux alts (scan)":
            selected_assets = SCAN_ASSETS
        else:
            selected_assets = ALL_ASSETS

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
            else:
                st.error(f"❌ Erreur (code {returncode})")


# -----------------------------------------------------------------------------
# OPTIMIZATION
# -----------------------------------------------------------------------------
elif page == "⚡ Optimization":
    st.title("⚡ Optimisation Bayésienne")

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

        selected_assets = st.multiselect(
            "Assets à optimiser",
            available_data,
            default=[a for a in SCAN_ASSETS if a in available_data][:3],
        )

        trials_atr = st.slider("Trials ATR", 20, 200, 100)
        trials_ichi = st.slider("Trials Ichimoku", 20, 200, 100)

        import os
        max_workers = os.cpu_count() or 4
        workers = st.slider("Workers (parallélisme)", 1, max_workers, min(4, max_workers))

        skip_download = st.checkbox("Skip download (données déjà présentes)", value=True)

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

    st.markdown("---")

    if not selected_assets:
        st.warning("Sélectionnez au moins un asset")
    else:
        if st.button("🚀 Lancer l'optimisation", type="primary", use_container_width=True):
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

                returncode, output = run_command(cmd, output_placeholder)

                if returncode == 0:
                    st.success("✅ Optimisation terminée!")
                    st.balloons()

                    # Show latest results
                    scan_results = get_scan_results()
                    if scan_results:
                        st.subheader("Résultats")
                        df = pd.read_csv(scan_results[0])
                        st.dataframe(df, use_container_width=True)
                else:
                    st.error(f"❌ Erreur (code {returncode})")


# -----------------------------------------------------------------------------
# GUARDS
# -----------------------------------------------------------------------------
elif page == "🛡️ Guards":
    st.title("🛡️ Tests de Robustesse (Guards)")

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

        selected_assets = st.multiselect(
            "Assets à valider",
            available_assets,
            default=available_assets,
        )

        import os
        max_workers = os.cpu_count() or 4
        workers = st.slider("Workers", 1, max_workers, min(4, max_workers))

    with col2:
        st.subheader("Résultats précédents")
        guards_df = get_guards_results()
        if guards_df is not None:
            st.dataframe(
                guards_df[["asset", "all_pass", "guard001_pass", "guard002_pass",
                          "guard003_pass", "guard005_pass", "guard006_pass", "guard007_pass"]],
                use_container_width=True,
            )
        else:
            st.info("Aucun résultat précédent")

    st.markdown("---")

    if not selected_assets:
        st.warning("Sélectionnez au moins un asset")
    else:
        if st.button("🚀 Lancer les Guards", type="primary", use_container_width=True):
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
elif page == "📈 Results":
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
                "Monte Carlo": f"{selected_asset}_montecarlo.csv",
                "Sensitivity": f"{selected_asset}_sensitivity.csv",
                "Bootstrap": f"{selected_asset}_bootstrap.csv",
                "Trade Dist": f"{selected_asset}_tradedist.csv",
                "Stress Test": f"{selected_asset}_stresstest.csv",
                "Regime": f"{selected_asset}_regime.csv",
            }

            for name, filename in guard_files.items():
                filepath = outputs_dir / filename
                if filepath.exists():
                    with st.expander(f"📋 {name}"):
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


# =============================================================================
# FOOTER
# =============================================================================
st.sidebar.markdown("---")
st.sidebar.caption(f"v1.0 | {datetime.now().strftime('%Y-%m-%d')}")
