"""
Cluster Analysis for Multi-Asset Parameters
Finds groups of assets with similar optimized parameters to minimize config complexity
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# Parameter columns for clustering
PARAM_COLS = [
    "sl_mult", "tp1_mult", "tp2_mult", "tp3_mult",
    "tenkan", "kijun", "tenkan_5", "kijun_5"
]


def load_scan_results(filepath: str) -> pd.DataFrame:
    """Load scan results CSV and filter successful assets."""
    df = pd.read_csv(filepath)
    # Keep only successful scans
    success_mask = df["status"].str.contains("SUCCESS", na=False)
    return df[success_mask].copy()


def extract_param_vectors(df: pd.DataFrame) -> Tuple[np.ndarray, list, StandardScaler, list]:
    """Extract normalized parameter vectors for clustering."""
    X = df[PARAM_COLS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    assets = df["asset"].tolist()
    return X_scaled, assets, scaler, PARAM_COLS


def find_optimal_clusters(X: np.ndarray, k_range: Tuple[int, int] = (2, 5)) -> int:
    """Find optimal number of clusters using silhouette score."""
    scores = {}

    for k in range(k_range[0], k_range[1] + 1):
        if k >= len(X):
            continue
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        score = silhouette_score(X, labels)
        scores[k] = score
        print(f"  k={k}: silhouette={score:.3f}")

    if not scores:
        return 2

    best_k = max(scores, key=scores.get)
    print(f"  -> Optimal k={best_k}")
    return best_k


def run_clustering(df: pd.DataFrame, n_clusters: int = None) -> Dict:
    """Run K-means clustering on parameter vectors."""
    print("\n[1] Extracting parameter vectors...")
    X_scaled, assets, scaler, param_cols = extract_param_vectors(df)

    print(f"[2] Finding optimal clusters...")
    if n_clusters is None:
        n_clusters = find_optimal_clusters(X_scaled)

    print(f"[3] Running K-means with k={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Add cluster labels to dataframe
    df = df.copy()
    df["cluster"] = labels

    # Get cluster centers in original scale
    centers_scaled = kmeans.cluster_centers_
    centers = scaler.inverse_transform(centers_scaled)

    # Build cluster info
    clusters = {}
    for i in range(n_clusters):
        cluster_df = df[df["cluster"] == i]
        cluster_assets = cluster_df["asset"].tolist()
        cluster_params = dict(zip(param_cols, centers[i]))

        # Round params appropriately
        cluster_params["sl_mult"] = round(cluster_params["sl_mult"] * 4) / 4
        cluster_params["tp1_mult"] = round(cluster_params["tp1_mult"] * 4) / 4
        cluster_params["tp2_mult"] = round(cluster_params["tp2_mult"] * 2) / 2
        cluster_params["tp3_mult"] = round(cluster_params["tp3_mult"] * 2) / 2
        cluster_params["tenkan"] = int(round(cluster_params["tenkan"]))
        cluster_params["kijun"] = int(round(cluster_params["kijun"]))
        cluster_params["tenkan_5"] = int(round(cluster_params["tenkan_5"]))
        cluster_params["kijun_5"] = int(round(cluster_params["kijun_5"]))

        clusters[f"cluster_{i}"] = {
            "assets": cluster_assets,
            "size": len(cluster_assets),
            "params": cluster_params,
            "avg_oos_sharpe": float(cluster_df["oos_sharpe"].mean()),
            "avg_oos_trades": float(cluster_df["oos_trades"].mean()),
            "avg_wfe": float(cluster_df["wfe"].mean()),
        }

    return {
        "n_clusters": n_clusters,
        "clusters": clusters,
        "asset_assignments": dict(zip(assets, [int(l) for l in labels])),
        "silhouette_score": float(silhouette_score(X_scaled, labels)),
    }


def calculate_param_loss(
    df: pd.DataFrame,
    cluster_info: Dict,
) -> pd.DataFrame:
    """Calculate performance loss when using cluster params vs individual params."""
    rows = []

    for cluster_name, cluster_data in cluster_info["clusters"].items():
        cluster_params = cluster_data["params"]

        for asset in cluster_data["assets"]:
            asset_row = df[df["asset"] == asset].iloc[0]

            # Individual OOS Sharpe
            individual_sharpe = asset_row["oos_sharpe"]

            # Calculate distance from cluster center
            individual_params = {col: asset_row[col] for col in PARAM_COLS}

            param_diff = sum(
                (individual_params[col] - cluster_params[col]) ** 2
                for col in PARAM_COLS
            ) ** 0.5

            rows.append({
                "asset": asset,
                "cluster": cluster_name,
                "individual_sharpe": individual_sharpe,
                "cluster_avg_sharpe": cluster_data["avg_oos_sharpe"],
                "param_distance": param_diff,
            })

    return pd.DataFrame(rows)


def generate_cluster_config(cluster_info: Dict) -> str:
    """Generate Python config from cluster analysis."""
    lines = [
        '"""',
        'Auto-generated Cluster Configuration',
        f'Generated: {datetime.now().isoformat()}',
        'Clusters found via K-means on optimized parameters',
        '"""',
        '',
        'CLUSTER_PARAMS = {'
    ]

    for cluster_name, data in cluster_info["clusters"].items():
        p = data["params"]
        lines.append(f'    "{cluster_name}": {{')
        lines.append(f'        "assets": {data["assets"]},')
        lines.append(f'        "atr": {{')
        lines.append(f'            "sl_mult": {p["sl_mult"]},')
        lines.append(f'            "tp1_mult": {p["tp1_mult"]},')
        lines.append(f'            "tp2_mult": {p["tp2_mult"]},')
        lines.append(f'            "tp3_mult": {p["tp3_mult"]},')
        lines.append(f'        }},')
        lines.append(f'        "ichimoku": {{"tenkan": {p["tenkan"]}, "kijun": {p["kijun"]}}},')
        lines.append(f'        "five_in_one": {{"tenkan_5": {p["tenkan_5"]}, "kijun_5": {p["kijun_5"]}}},')
        lines.append(f'        "displacement": 52,')
        lines.append(f'        "avg_sharpe": {data["avg_oos_sharpe"]:.2f},')
        lines.append(f'        "avg_trades": {data["avg_oos_trades"]:.0f},')
        lines.append(f'    }},')

    lines.append('}')
    lines.append('')
    lines.append('# Asset to cluster mapping')
    lines.append('ASSET_CLUSTER = {')
    for asset, cluster_id in cluster_info["asset_assignments"].items():
        lines.append(f'    "{asset}": "cluster_{cluster_id}",')
    lines.append('}')
    lines.append('')
    lines.append('')
    lines.append('def get_params_for_asset(asset: str) -> dict:')
    lines.append('    """Get cluster parameters for a given asset."""')
    lines.append('    cluster_name = ASSET_CLUSTER.get(asset)')
    lines.append('    if cluster_name is None:')
    lines.append('        raise ValueError(f"Unknown asset: {asset}")')
    lines.append('    return CLUSTER_PARAMS[cluster_name]')

    return '\n'.join(lines)


def run_full_analysis(scan_results_path: str, n_clusters: int = None) -> Dict:
    """Run complete cluster analysis pipeline."""
    print("=" * 60)
    print("CLUSTER ANALYSIS")
    print("=" * 60)

    # Load data
    df = load_scan_results(scan_results_path)
    print(f"\nLoaded {len(df)} successful assets")

    if len(df) < 3:
        print("Not enough assets for clustering (minimum 3)")
        return {}

    # Run clustering
    cluster_info = run_clustering(df, n_clusters)

    # Print results
    print("\n" + "=" * 60)
    print("CLUSTER RESULTS")
    print("=" * 60)

    for name, data in cluster_info["clusters"].items():
        print(f"\n{name.upper()} ({data['size']} assets)")
        print(f"  Assets: {data['assets']}")
        print(f"  Avg OOS Sharpe: {data['avg_oos_sharpe']:.2f}")
        print(f"  Avg OOS Trades: {data['avg_oos_trades']:.0f}")
        print(f"  Avg WFE: {data['avg_wfe']:.2f}")
        p = data['params']
        print(f"  ATR: SL={p['sl_mult']}, TP1={p['tp1_mult']}, TP2={p['tp2_mult']}, TP3={p['tp3_mult']}")
        print(f"  Ichi: tenkan={p['tenkan']}, kijun={p['kijun']}")
        print(f"  5in1: tenkan_5={p['tenkan_5']}, kijun_5={p['kijun_5']}")

    print(f"\nOverall Silhouette Score: {cluster_info['silhouette_score']:.3f}")

    # Calculate param loss
    loss_df = calculate_param_loss(df, cluster_info)
    print("\nParameter Distance from Cluster Centers:")
    print(loss_df.to_string(index=False))

    # Export files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    Path("outputs").mkdir(exist_ok=True)
    Path("crypto_backtest/config").mkdir(exist_ok=True)

    # Export JSON
    json_path = f"outputs/cluster_analysis_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(cluster_info, f, indent=2)

    # Export Python config
    config_code = generate_cluster_config(cluster_info)
    config_path = f"crypto_backtest/config/cluster_params_{timestamp}.py"
    with open(config_path, "w") as f:
        f.write(config_code)

    # Also save as latest
    latest_config_path = "crypto_backtest/config/cluster_params.py"
    with open(latest_config_path, "w") as f:
        f.write(config_code)

    # Export loss analysis
    loss_path = f"outputs/cluster_param_loss_{timestamp}.csv"
    loss_df.to_csv(loss_path, index=False)

    print(f"\n✓ Exported: {json_path}")
    print(f"✓ Exported: {config_path}")
    print(f"✓ Exported: {latest_config_path}")
    print(f"✓ Exported: {loss_path}")

    return cluster_info


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Cluster Analysis for Multi-Asset Parameters")
    parser.add_argument("--input", required=True, help="Path to scan results CSV")
    parser.add_argument("--clusters", type=int, default=None, help="Force number of clusters")
    args = parser.parse_args()

    run_full_analysis(args.input, args.clusters)


if __name__ == "__main__":
    main()
