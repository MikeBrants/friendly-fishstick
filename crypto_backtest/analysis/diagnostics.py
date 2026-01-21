"""Detailed diagnostics for failed/warning assets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass
class DiagnosticResult:
    """Single diagnostic check result."""

    name: str
    status: str  # "PASS", "WARN", "FAIL"
    value: Any
    threshold: Any
    explanation: str
    recommendation: str


@dataclass
class AssetDiagnostics:
    """Complete diagnostics for an asset."""

    asset: str
    overall_status: str  # "PASS", "WARN", "FAIL"
    checks: list[DiagnosticResult]
    recommended_settings: dict[str, Any]


def diagnose_asset(
    asset: str,
    scan_row: pd.Series,
    guards_row: Optional[pd.Series] = None,
) -> AssetDiagnostics:
    """
    Run detailed diagnostics on an asset and provide recommendations.

    Args:
        asset: Asset symbol
        scan_row: Row from scan results DataFrame
        guards_row: Row from guards summary DataFrame (optional)

    Returns:
        AssetDiagnostics with detailed checks and recommendations
    """
    checks = []
    recommendations = {}

    # =========================================================================
    # 1. SHARPE RATIO CHECK
    # =========================================================================
    oos_sharpe = scan_row.get("oos_sharpe", 0)
    is_sharpe = scan_row.get("is_sharpe", 0)

    if oos_sharpe >= 2.0:
        sharpe_status = "PASS"
        sharpe_explanation = "Excellent Sharpe OOS, strategie performante."
        sharpe_recommendation = "Aucune modification necessaire."
    elif oos_sharpe >= 1.0:
        sharpe_status = "PASS"
        sharpe_explanation = "Sharpe OOS acceptable, au-dessus du seuil minimum."
        sharpe_recommendation = "Envisager d'augmenter les trials pour potentiellement ameliorer."
    elif oos_sharpe >= 0.5:
        sharpe_status = "WARN"
        sharpe_explanation = "Sharpe OOS faible. La strategie genere peu de profit ajuste au risque."
        sharpe_recommendation = "Augmenter trials_atr a 150+, tester displacement grid [26, 39, 52, 65, 78]."
        recommendations["trials_atr"] = 150
        recommendations["trials_ichi"] = 150
        recommendations["test_displacement"] = True
    else:
        sharpe_status = "FAIL"
        sharpe_explanation = f"Sharpe OOS tres faible ({oos_sharpe:.2f}). Strategie non rentable ou trop volatile."
        sharpe_recommendation = "Asset probablement inadapte a la strategie FINAL TRIGGER. Verifier si l'asset a suffisamment de tendances claires."
        recommendations["exclude_asset"] = True

    checks.append(
        DiagnosticResult(
            name="Sharpe Ratio OOS",
            status=sharpe_status,
            value=f"{oos_sharpe:.2f}",
            threshold=">= 1.0 (target >= 2.0)",
            explanation=sharpe_explanation,
            recommendation=sharpe_recommendation,
        )
    )

    # =========================================================================
    # 2. WALK-FORWARD EFFICIENCY CHECK
    # =========================================================================
    wfe = scan_row.get("wfe", 0)

    if wfe >= 1.0:
        wfe_status = "PASS"
        wfe_explanation = "WFE excellent. OOS performe mieux ou egal a IS, pas d'overfit."
        wfe_recommendation = "Parametres robustes, continuer vers guards."
    elif wfe >= 0.6:
        wfe_status = "PASS"
        wfe_explanation = "WFE acceptable. Legere degradation IS->OOS mais dans les normes."
        wfe_recommendation = "Valider avec Monte Carlo pour confirmer significativite."
    elif wfe >= 0.3:
        wfe_status = "WARN"
        wfe_explanation = f"WFE faible ({wfe:.2f}). Degradation significative IS->OOS, possible overfit."
        wfe_recommendation = "Reduire l'espace de recherche, utiliser moins de trials, ou simplifier la strategie."
        recommendations["trials_atr"] = 80
        recommendations["trials_ichi"] = 80
        recommendations["reduce_search_space"] = True
    else:
        wfe_status = "FAIL"
        wfe_explanation = f"WFE tres faible ({wfe:.2f}). Fort overfit probable, les params IS ne generalisent pas."
        wfe_recommendation = "Reduire drastiquement les trials (50), fixer certains params (displacement=52), ou exclure l'asset."
        recommendations["trials_atr"] = 50
        recommendations["trials_ichi"] = 50
        recommendations["fix_displacement"] = 52

    checks.append(
        DiagnosticResult(
            name="Walk-Forward Efficiency",
            status=wfe_status,
            value=f"{wfe:.2f}",
            threshold=">= 0.6 (target >= 1.0)",
            explanation=wfe_explanation,
            recommendation=wfe_recommendation,
        )
    )

    # =========================================================================
    # 3. MAX DRAWDOWN CHECK
    # =========================================================================
    max_dd = abs(scan_row.get("oos_max_dd", 0))

    if max_dd <= 5:
        dd_status = "PASS"
        dd_explanation = "Drawdown tres contenu, excellent risk management."
        dd_recommendation = "Parametres ATR bien calibres."
    elif max_dd <= 10:
        dd_status = "PASS"
        dd_explanation = "Drawdown acceptable pour une strategie crypto."
        dd_recommendation = "Envisager de reduire sl_mult si trop de volatilite."
    elif max_dd <= 15:
        dd_status = "WARN"
        dd_explanation = f"Drawdown eleve ({max_dd:.1f}%). Periodes de pertes significatives."
        dd_recommendation = "Reduire sl_mult (2.5-3.0), augmenter tp1_mult pour securiser les profits."
        recommendations["sl_mult_max"] = 3.0
        recommendations["tp1_mult_min"] = 2.0
    else:
        dd_status = "FAIL"
        dd_explanation = f"Drawdown excessif ({max_dd:.1f}%). Risque de ruine eleve."
        dd_recommendation = "Stop-loss trop large ou strategie inadaptee a cet asset."
        recommendations["sl_mult_max"] = 2.5
        recommendations["review_strategy"] = True

    checks.append(
        DiagnosticResult(
            name="Max Drawdown OOS",
            status=dd_status,
            value=f"{max_dd:.1f}%",
            threshold="<= 15% (target <= 10%)",
            explanation=dd_explanation,
            recommendation=dd_recommendation,
        )
    )

    # =========================================================================
    # 4. TRADE COUNT CHECK
    # =========================================================================
    trades = scan_row.get("oos_trades", 0)

    if trades >= 100:
        trades_status = "PASS"
        trades_explanation = "Nombre de trades suffisant pour significativite statistique."
        trades_recommendation = "Echantillon robuste pour les guards."
    elif trades >= 50:
        trades_status = "WARN"
        trades_explanation = f"Nombre de trades limite ({trades}). Resultats moins fiables."
        trades_recommendation = "Augmenter la periode de donnees (days_back) ou reduire les filtres."
        recommendations["days_back"] = 1095  # 3 years
    else:
        trades_status = "FAIL"
        trades_explanation = f"Trop peu de trades ({trades}). Resultats non significatifs."
        trades_recommendation = "Strategie trop restrictive ou donnees insuffisantes. Besoin de 100+ trades minimum."
        recommendations["days_back"] = 1095
        recommendations["relax_filters"] = True

    checks.append(
        DiagnosticResult(
            name="Nombre de Trades",
            status=trades_status,
            value=str(int(trades)),
            threshold=">= 100 (minimum 50)",
            explanation=trades_explanation,
            recommendation=trades_recommendation,
        )
    )

    # =========================================================================
    # 5. IS vs OOS CONSISTENCY CHECK
    # =========================================================================
    if is_sharpe > 0 and oos_sharpe > 0:
        degradation = (is_sharpe - oos_sharpe) / is_sharpe * 100

        if degradation <= 20:
            consist_status = "PASS"
            consist_explanation = f"Degradation IS->OOS faible ({degradation:.0f}%). Bonne generalisation."
            consist_recommendation = "Parametres stables."
        elif degradation <= 40:
            consist_status = "WARN"
            consist_explanation = f"Degradation IS->OOS moderee ({degradation:.0f}%). Possible overfit leger."
            consist_recommendation = "Surveiller les guards, notamment sensitivity et bootstrap."
        else:
            consist_status = "FAIL"
            consist_explanation = f"Degradation IS->OOS forte ({degradation:.0f}%). Overfit probable."
            consist_recommendation = "Reduire la complexite de l'optimisation."
            recommendations["simplify"] = True

        checks.append(
            DiagnosticResult(
                name="Consistance IS/OOS",
                status=consist_status,
                value=f"-{degradation:.0f}%",
                threshold="<= 40% degradation",
                explanation=consist_explanation,
                recommendation=consist_recommendation,
            )
        )

    # =========================================================================
    # 6. GUARDS CHECKS (if available)
    # =========================================================================
    if guards_row is not None:
        # Monte Carlo
        mc_pass = guards_row.get("guard001_pass", None)
        mc_pvalue = guards_row.get("guard001_p_value", None)
        if mc_pass is not None:
            if mc_pass:
                mc_status = "PASS"
                mc_explanation = f"Monte Carlo significatif (p={mc_pvalue:.3f}). Performance non due au hasard."
                mc_recommendation = "Strategie validee statistiquement."
            else:
                mc_status = "FAIL"
                mc_explanation = f"Monte Carlo non significatif (p={mc_pvalue:.3f}). Performance possiblement due au hasard."
                mc_recommendation = "Augmenter le nombre de trades ou revoir la strategie."
                recommendations["need_more_trades"] = True

            checks.append(
                DiagnosticResult(
                    name="Monte Carlo (GUARD-001)",
                    status=mc_status,
                    value=f"p={mc_pvalue:.3f}" if mc_pvalue else "N/A",
                    threshold="p < 0.05",
                    explanation=mc_explanation,
                    recommendation=mc_recommendation,
                )
            )

        # Sensitivity
        sens_pass = guards_row.get("guard002_pass", None)
        sens_var = guards_row.get("guard002_variance_pct", None)
        if sens_pass is not None:
            if sens_pass:
                sens_status = "PASS"
                sens_explanation = f"Sensibilite faible ({sens_var:.1f}%). Parametres robustes aux perturbations."
                sens_recommendation = "Pas de changement necessaire."
            else:
                sens_status = "FAIL"
                sens_explanation = f"Sensibilite elevee ({sens_var:.1f}%). Petits changements de params = gros impact."
                sens_recommendation = "Reduire l'espace de recherche, fixer certains params."
                recommendations["fix_some_params"] = True

            checks.append(
                DiagnosticResult(
                    name="Sensitivity (GUARD-002)",
                    status=sens_status,
                    value=f"{sens_var:.1f}%" if sens_var else "N/A",
                    threshold="< 20%",
                    explanation=sens_explanation,
                    recommendation=sens_recommendation,
                )
            )

        # Bootstrap CI
        boot_pass = guards_row.get("guard003_pass", None)
        boot_ci = guards_row.get("guard003_sharpe_ci_lower", None)
        if boot_pass is not None:
            if boot_pass:
                boot_status = "PASS"
                boot_explanation = f"Intervalle de confiance OK (CI lower={boot_ci:.2f}). Sharpe fiable."
                boot_recommendation = "Performance stable."
            else:
                boot_status = "FAIL"
                boot_explanation = f"Intervalle de confiance trop large (CI lower={boot_ci:.2f}). Sharpe instable."
                boot_recommendation = "Besoin de plus de trades pour reduire l'incertitude."

            checks.append(
                DiagnosticResult(
                    name="Bootstrap CI (GUARD-003)",
                    status=boot_status,
                    value=f"CI={boot_ci:.2f}" if boot_ci else "N/A",
                    threshold="CI lower > 1.0",
                    explanation=boot_explanation,
                    recommendation=boot_recommendation,
                )
            )

    # =========================================================================
    # OVERALL STATUS
    # =========================================================================
    fail_count = sum(1 for c in checks if c.status == "FAIL")
    warn_count = sum(1 for c in checks if c.status == "WARN")

    if fail_count > 0:
        overall_status = "FAIL"
    elif warn_count >= 2:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    # Build recommended settings
    recommended_settings = {
        "asset": asset,
        "trials_atr": recommendations.get("trials_atr", 100),
        "trials_ichi": recommendations.get("trials_ichi", 100),
        "days_back": recommendations.get("days_back", 730),
        "test_displacement": recommendations.get("test_displacement", False),
        "fix_displacement": recommendations.get("fix_displacement", None),
        "exclude_asset": recommendations.get("exclude_asset", False),
    }

    return AssetDiagnostics(
        asset=asset,
        overall_status=overall_status,
        checks=checks,
        recommended_settings=recommended_settings,
    )


def render_diagnostics_markdown(diag: AssetDiagnostics) -> str:
    """Render diagnostics as markdown string."""
    status_emoji = {"PASS": "OK", "WARN": "WARN", "FAIL": "FAIL"}

    lines = [
        f"## {status_emoji[diag.overall_status]} Diagnostic: {diag.asset}",
        "",
        "| Check | Status | Valeur | Seuil |",
        "|-------|--------|--------|-------|",
    ]

    for check in diag.checks:
        lines.append(f"| {check.name} | {check.status} | {check.value} | {check.threshold} |")

    lines.extend(["", "### Details", ""])

    for check in diag.checks:
        lines.append(f"**{check.name}**")
        lines.append(f"- {check.explanation}")
        lines.append(f"- Recommendation: *{check.recommendation}*")
        lines.append("")

    return "\n".join(lines)
