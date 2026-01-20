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
    EXCLUDED_ASSETS,
    TOP50_ASSETS,
    TIER1_ASSETS,
    TIER2_ASSETS,
    TIER3_ASSETS,
    TIER4_ASSETS,
    BONUS_ASSETS,
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
    ["📊 Dashboard", "📥 Download Data", "⚡ Optimization", "🛡️ Guards", "📈 Results", "🏆 Comparaison", "📉 Visualisation"],
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
            [
                "Top 50 complet",
                "Tier 1 - Blue chips (Top 10)",
                "Tier 2 - Large caps (11-25)",
                "Tier 3 - Mid caps (26-40)",
                "Tier 4 - Small caps (41-50)",
                "Bonus - Trending",
                "Assets validés (production)",
                "Nouveaux à scanner",
                "Sélection manuelle",
            ],
        )

        if asset_option == "Sélection manuelle":
            selected_assets = st.multiselect(
                "Choisir les assets",
                sorted(ALL_ASSETS),
                default=["BTC", "ETH"],
            )
        elif asset_option == "Top 50 complet":
            selected_assets = TOP50_ASSETS
        elif asset_option == "Tier 1 - Blue chips (Top 10)":
            selected_assets = TIER1_ASSETS
        elif asset_option == "Tier 2 - Large caps (11-25)":
            selected_assets = TIER2_ASSETS
        elif asset_option == "Tier 3 - Mid caps (26-40)":
            selected_assets = TIER3_ASSETS
        elif asset_option == "Tier 4 - Small caps (41-50)":
            selected_assets = TIER4_ASSETS
        elif asset_option == "Bonus - Trending":
            selected_assets = BONUS_ASSETS
        elif asset_option == "Assets validés (production)":
            selected_assets = VALIDATED_ASSETS
        elif asset_option == "Nouveaux à scanner":
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


# -----------------------------------------------------------------------------
# COMPARAISON
# -----------------------------------------------------------------------------
elif page == "🏆 Comparaison":
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
        merged_df = scan_df.merge(
            guards_df[["asset", "all_pass", "guard001_pass", "guard002_pass",
                      "guard003_pass", "guard005_pass", "guard006_pass", "guard007_pass"]],
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


# =============================================================================
# FOOTER
# =============================================================================
st.sidebar.markdown("---")
st.sidebar.caption(f"v1.2 | {datetime.now().strftime('%Y-%m-%d')}")
