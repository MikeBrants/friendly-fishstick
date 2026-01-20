# CODEX MULTI-ASSET-005: Scan 10 Alts + Clustering

**Date**: 2026-01-20  
**Status**: À implémenter  
**Objectif**: Scanner 10 alts, trouver clusters de params similaires, minimiser différenciations

---

## 1. CONTEXTE

### Assets Validés (référence)
| Asset | OOS Sharpe | WFE | Status |
|-------|------------|-----|--------|
| BTC | 2.63 | 1.23 | ✅ Production |
| ETH | 5.31 | 2.46 | ✅ Production |
| XRP | 2.90 | 0.80 | ✅ Production |

### Assets Exclus
| Asset | Raison |
|-------|--------|
| SOL | Params ATR incompatibles (TP1=1.5 vs 5.0 pour ETH/XRP) |
| AAVE | Overfitting sévère (WFE=0.44) |

### Nouveaux Assets à Scanner
| # | Asset | Catégorie | Exchange |
|---|-------|-----------|----------|
| 1 | HYPE | DEX Perp (Hyperliquid) | Bybit |
| 2 | AVAX | L1 | Binance |
| 3 | ATOM | Cosmos/IBC | Binance |
| 4 | ARB | L2 ETH | Binance |
| 5 | LINK | Oracle | Binance |
| 6 | UNI | DeFi | Binance |
| 7 | SUI | L1 Move | Binance |
| 8 | INJ | DeFi/Perp | Binance |
| 9 | TIA | Modular (Celestia) | Binance |
| 10 | SEI | L1 Fast | Binance |

---

## 2. ARCHITECTURE FICHIERS

```
crypto_backtest/
├── config/
│   ├── assets.py              # Config existante (BTC/ETH/XRP)
│   └── scan_assets.py         # NEW: Config scan 10 alts
├── scripts/
│   ├── download_data.py       # NEW: Download OHLCV via CCXT
│   └── run_full_pipeline.py   # NEW: Main entry point
├── optimization/
│   ├── bayesian.py            # Existant
│   └── parallel_optimizer.py  # NEW: Pool-based parallel
├── analysis/
│   ├── metrics.py             # Existant
│   └── cluster_params.py      # NEW: K-means clustering
└── outputs/
    ├── multiasset_scan_{ts}.csv
    └── cluster_analysis_{ts}.json
```

---

## 3. FICHIER: config/scan_assets.py

```python
"""
Multi-Asset Scan Configuration
Generated: 2026-01-20
"""

# Assets à scanner
SCAN_ASSETS = [
    "HYPE",   # Hyperliquid - DEX Perp
    "AVAX",   # Avalanche - L1
    "ATOM",   # Cosmos - IBC
    "ARB",    # Arbitrum - L2
    "LINK",   # Chainlink - Oracle
    "UNI",    # Uniswap - DeFi
    "SUI",    # Sui - L1 Move
    "INJ",    # Injective - DeFi/Perp
    "TIA",    # Celestia - Modular
    "SEI",    # Sei - L1 Fast
]

# Assets déjà validés (pour comparaison clustering)
VALIDATED_ASSETS = ["BTC", "ETH", "XRP"]

# Tous les assets
ALL_ASSETS = VALIDATED_ASSETS + SCAN_ASSETS

# Exchanges par asset
EXCHANGE_MAP = {
    "BTC": "binance", "ETH": "binance", "XRP": "binance",
    "HYPE": "bybit",
    "AVAX": "binance", "ATOM": "binance", "ARB": "binance",
    "LINK": "binance", "UNI": "binance", "SUI": "binance",
    "INJ": "binance", "TIA": "binance", "SEI": "binance",
}

# Optimization params
OPTIM_CONFIG = {
    "n_trials_atr": 100,
    "n_trials_ichi": 100,
    "validation_split": (0.6, 0.2, 0.2),  # IS/VAL/OOS
    "warmup_bars": 200,
    "min_trades": 50,
}

# ATR search space
ATR_SEARCH_SPACE = {
    "sl_mult": (1.5, 5.0),
    "tp1_mult": (1.5, 5.0),
    "tp2_mult": (3.0, 12.0),
    "tp3_mult": (2.0, 10.0),
}

# Ichimoku search space
ICHI_SEARCH_SPACE = {
    "tenkan": (5, 20),
    "kijun": (20, 40),
    "tenkan_5": (8, 16),
    "kijun_5": (15, 30),
}

# Clustering params
CLUSTER_CONFIG = {
    "n_clusters_range": (2, 5),
    "max_param_loss": 0.15,
    "min_cluster_size": 3,
}
```

---

## 4. FICHIER: scripts/download_data.py

```python
"""
Download OHLCV data for all scan assets
"""
import ccxt
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time

from config.scan_assets import ALL_ASSETS, EXCHANGE_MAP


def download_asset(asset: str, timeframe: str = "1h", 
                   days_back: int = 730) -> pd.DataFrame:
    """Download OHLCV data for a single asset"""

    exchange_id = EXCHANGE_MAP.get(asset, "binance")
    exchange = getattr(ccxt, exchange_id)({
        "enableRateLimit": True,
    })

    symbol = f"{asset}/USDT"
    since = exchange.parse8601(
        (datetime.utcnow() - timedelta(days=days_back)).isoformat()
    )

    all_ohlcv = []
    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
        if not ohlcv:
            break
        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        if len(ohlcv) < 1000:
            break
        time.sleep(exchange.rateLimit / 1000)

    df = pd.DataFrame(all_ohlcv, 
                      columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    return df


def download_all(output_dir: str = "data"):
    """Download data for all assets"""
    Path(output_dir).mkdir(exist_ok=True)

    for asset in ALL_ASSETS:
        print(f"Downloading {asset}...")
        try:
            df = download_asset(asset)
            df.to_parquet(f"{output_dir}/{asset}_1H.parquet")
            print(f"  ✓ {asset}: {len(df)} bars")
        except Exception as e:
            print(f"  ✗ {asset}: {e}")

    print("\nDownload complete!")


if __name__ == "__main__":
    download_all()
```

---

## 5. FICHIER: optimization/parallel_optimizer.py

```python
"""
Parallel Multi-Asset Optimizer
Uses multiprocessing Pool for parallel execution
"""
import optuna
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

from config.scan_assets import (
    SCAN_ASSETS, OPTIM_CONFIG, ATR_SEARCH_SPACE, ICHI_SEARCH_SPACE
)
from engine.backtest import run_backtest

optuna.logging.set_verbosity(optuna.logging.WARNING)


def load_data(asset: str) -> pd.DataFrame:
    """Load OHLCV data for asset"""
    return pd.read_parquet(f"data/{asset}_1H.parquet")


def split_data(df: pd.DataFrame, splits=(0.6, 0.2, 0.2)):
    """Split data into IS/VAL/OOS"""
    n = len(df)
    is_end = int(n * splits[0])
    val_end = int(n * (splits[0] + splits[1]))
    return df.iloc[:is_end], df.iloc[is_end:val_end], df.iloc[val_end:]


def objective_atr(trial, df_is: pd.DataFrame):
    """Optuna objective for ATR params"""
    params = {
        "sl_mult": trial.suggest_float("sl_mult", *ATR_SEARCH_SPACE["sl_mult"], step=0.25),
        "tp1_mult": trial.suggest_float("tp1_mult", *ATR_SEARCH_SPACE["tp1_mult"], step=0.25),
        "tp2_mult": trial.suggest_float("tp2_mult", *ATR_SEARCH_SPACE["tp2_mult"], step=0.5),
        "tp3_mult": trial.suggest_float("tp3_mult", *ATR_SEARCH_SPACE["tp3_mult"], step=0.5),
    }

    results = run_backtest(df_is, atr_params=params)

    if results["trades"] < OPTIM_CONFIG["min_trades"]:
        return -10.0

    return results["sharpe"]


def objective_ichi(trial, df_is: pd.DataFrame, atr_params: dict):
    """Optuna objective for Ichimoku params"""
    params = {
        "tenkan": trial.suggest_int("tenkan", *ICHI_SEARCH_SPACE["tenkan"]),
        "kijun": trial.suggest_int("kijun", *ICHI_SEARCH_SPACE["kijun"]),
        "tenkan_5": trial.suggest_int("tenkan_5", *ICHI_SEARCH_SPACE["tenkan_5"]),
        "kijun_5": trial.suggest_int("kijun_5", *ICHI_SEARCH_SPACE["kijun_5"]),
    }

    results = run_backtest(df_is, atr_params=atr_params, ichi_params=params)

    if results["trades"] < OPTIM_CONFIG["min_trades"]:
        return -10.0

    return results["sharpe"]


def optimize_single_asset(asset: str) -> dict:
    """Full optimization pipeline for one asset"""
    print(f"[{asset}] Starting optimization...")

    try:
        # 1. Load and split data
        df = load_data(asset)
        df_is, df_val, df_oos = split_data(df)

        print(f"[{asset}] Data: IS={len(df_is)}, VAL={len(df_val)}, OOS={len(df_oos)} bars")

        # 2. ATR Optimization
        study_atr = optuna.create_study(direction="maximize")
        study_atr.optimize(
            lambda trial: objective_atr(trial, df_is),
            n_trials=OPTIM_CONFIG["n_trials_atr"],
            n_jobs=-1,
            show_progress_bar=False
        )
        atr_params = study_atr.best_params
        print(f"[{asset}] ATR done: Sharpe={study_atr.best_value:.2f}")

        # 3. Ichimoku Optimization
        study_ichi = optuna.create_study(direction="maximize")
        study_ichi.optimize(
            lambda trial: objective_ichi(trial, df_is, atr_params),
            n_trials=OPTIM_CONFIG["n_trials_ichi"],
            n_jobs=-1,
            show_progress_bar=False
        )
        ichi_params = study_ichi.best_params
        print(f"[{asset}] Ichi done: Sharpe={study_ichi.best_value:.2f}")

        # 4. Validation sur les 3 segments
        is_results = run_backtest(df_is, atr_params=atr_params, ichi_params=ichi_params)
        val_results = run_backtest(df_val, atr_params=atr_params, ichi_params=ichi_params)
        oos_results = run_backtest(df_oos, atr_params=atr_params, ichi_params=ichi_params)

        # 5. Calculate WFE
        wfe = oos_results["sharpe"] / is_results["sharpe"] if is_results["sharpe"] > 0 else 0

        result = {
            "asset": asset,
            "status": "SUCCESS",
            # ATR params
            "sl_mult": atr_params["sl_mult"],
            "tp1_mult": atr_params["tp1_mult"],
            "tp2_mult": atr_params["tp2_mult"],
            "tp3_mult": atr_params["tp3_mult"],
            # Ichi params
            "tenkan": ichi_params["tenkan"],
            "kijun": ichi_params["kijun"],
            "tenkan_5": ichi_params["tenkan_5"],
            "kijun_5": ichi_params["kijun_5"],
            # IS metrics
            "is_sharpe": is_results["sharpe"],
            "is_return": is_results["total_return"],
            "is_trades": is_results["trades"],
            # VAL metrics
            "val_sharpe": val_results["sharpe"],
            "val_return": val_results["total_return"],
            "val_trades": val_results["trades"],
            # OOS metrics
            "oos_sharpe": oos_results["sharpe"],
            "oos_return": oos_results["total_return"],
            "oos_trades": oos_results["trades"],
            "oos_max_dd": oos_results["max_drawdown"],
            "oos_pf": oos_results["profit_factor"],
            # Validation
            "wfe": wfe,
        }

        print(f"[{asset}] ✓ Complete: OOS Sharpe={oos_results['sharpe']:.2f}, WFE={wfe:.2f}")
        return result

    except Exception as e:
        print(f"[{asset}] ✗ Error: {e}")
        return {"asset": asset, "status": "FAILED", "error": str(e)}


def run_parallel_scan(assets: list = None, n_workers: int = None) -> pd.DataFrame:
    """Run optimization for all assets in parallel"""
    assets = assets or SCAN_ASSETS
    n_workers = n_workers or min(cpu_count(), len(assets))

    print("="*60)
    print(f"MULTI-ASSET PARALLEL SCAN")
    print(f"Assets: {assets}")
    print(f"Workers: {n_workers}")
    print("="*60)

    with Pool(n_workers) as pool:
        results = pool.map(optimize_single_asset, assets)

    df = pd.DataFrame(results)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    Path("outputs").mkdir(exist_ok=True)
    df.to_csv(f"outputs/multiasset_scan_{timestamp}.csv", index=False)

    print("\n" + "="*60)
    print("SCAN COMPLETE")
    print("="*60)

    success_df = df[df["status"] == "SUCCESS"]
    if len(success_df) > 0:
        print(success_df[["asset", "oos_sharpe", "oos_trades", "wfe"]].to_string(index=False))

    failed = df[df["status"] == "FAILED"]["asset"].tolist()
    if failed:
        print(f"\nFailed: {failed}")

    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--assets", nargs="+", default=None)
    args = parser.parse_args()

    run_parallel_scan(assets=args.assets, n_workers=args.workers)
```

---

## 6. FICHIER: analysis/cluster_params.py

```python
"""
Cluster Analysis for Multi-Asset Params
Trouve des groupes d'assets avec params similaires
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from typing import Dict, List, Tuple
import json
from datetime import datetime
from pathlib import Path


def load_scan_results(filepath: str) -> pd.DataFrame:
    """Load scan results CSV"""
    df = pd.read_csv(filepath)
    return df[df["status"] == "SUCCESS"].copy()


def extract_param_vectors(df: pd.DataFrame):
    """Extract normalized parameter vectors for clustering"""

    param_cols = [
        "sl_mult", "tp1_mult", "tp2_mult", "tp3_mult",
        "tenkan", "kijun", "tenkan_5", "kijun_5"
    ]

    X = df[param_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    assets = df["asset"].tolist()

    return X_scaled, assets, scaler, param_cols


def find_optimal_clusters(X: np.ndarray, k_range: Tuple[int, int] = (2, 5)) -> int:
    """Find optimal number of clusters using silhouette score"""
    scores = {}
    for k in range(k_range[0], k_range[1] + 1):
        if k >= len(X):
            continue
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        score = silhouette_score(X, labels)
        scores[k] = score
        print(f"  k={k}: silhouette={score:.3f}")

    best_k = max(scores, key=scores.get)
    print(f"  -> Optimal k={best_k}")
    return best_k


def run_clustering(df: pd.DataFrame, n_clusters: int = None) -> Dict:
    """Run K-means clustering on param vectors"""

    print("\n[1] Extracting param vectors...")
    X_scaled, assets, scaler, param_cols = extract_param_vectors(df)

    print(f"[2] Finding optimal clusters...")
    if n_clusters is None:
        n_clusters = find_optimal_clusters(X_scaled)

    print(f"[3] Running K-means with k={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    df["cluster"] = labels
    centers_scaled = kmeans.cluster_centers_
    centers = scaler.inverse_transform(centers_scaled)

    clusters = {}
    for i in range(n_clusters):
        cluster_assets = df[df["cluster"] == i]["asset"].tolist()
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
            "avg_oos_sharpe": float(df[df["cluster"] == i]["oos_sharpe"].mean()),
            "avg_oos_trades": float(df[df["cluster"] == i]["oos_trades"].mean()),
            "avg_wfe": float(df[df["cluster"] == i]["wfe"].mean()),
        }

    return {
        "n_clusters": n_clusters,
        "clusters": clusters,
        "asset_assignments": dict(zip(assets, [int(l) for l in labels])),
        "silhouette_score": float(silhouette_score(X_scaled, labels)),
    }


def generate_cluster_config(cluster_info: Dict) -> str:
    """Generate Python config from cluster analysis"""

    lines = [
        '"""',
        'Auto-generated Cluster Config',
        f'Generated: {datetime.now().isoformat()}',
        '"""',
        '',
        'CLUSTER_PARAMS = {'
    ]

    for cluster_name, data in cluster_info["clusters"].items():
        p = data["params"]
        lines.append(f'    "{cluster_name}": {{')
        lines.append(f'        "assets": {data["assets"]},')
        lines.append(f'        "atr": {{"sl_mult": {p["sl_mult"]}, "tp1_mult": {p["tp1_mult"]}, "tp2_mult": {p["tp2_mult"]}, "tp3_mult": {p["tp3_mult"]}}},')
        lines.append(f'        "ichimoku": {{"tenkan": {p["tenkan"]}, "kijun": {p["kijun"]}}},')
        lines.append(f'        "five_in_one": {{"tenkan_5": {p["tenkan_5"]}, "kijun_5": {p["kijun_5"]}}},')
        lines.append(f'        "avg_sharpe": {data["avg_oos_sharpe"]:.2f},')
        lines.append(f'        "avg_trades": {data["avg_oos_trades"]:.0f},')
        lines.append('    },')

    lines.append('}')
    lines.append('')
    lines.append('# Asset to cluster mapping')
    lines.append('ASSET_CLUSTER = {')
    for asset, cluster_id in cluster_info["asset_assignments"].items():
        lines.append(f'    "{asset}": "cluster_{cluster_id}",')
    lines.append('}')

    return '\n'.join(lines)


def run_full_analysis(scan_results_path: str):
    """Run complete cluster analysis pipeline"""

    print("="*60)
    print("CLUSTER ANALYSIS")
    print("="*60)

    df = load_scan_results(scan_results_path)
    print(f"\nLoaded {len(df)} successful assets")

    cluster_info = run_clustering(df)

    print("\n" + "="*60)
    print("CLUSTER RESULTS")
    print("="*60)

    for name, data in cluster_info["clusters"].items():
        print(f"\n{name.upper()} ({data['size']} assets)")
        print(f"  Assets: {data['assets']}")
        print(f"  Avg OOS Sharpe: {data['avg_oos_sharpe']:.2f}")
        print(f"  Avg OOS Trades: {data['avg_oos_trades']:.0f}")
        print(f"  Params: SL={data['params']['sl_mult']}, TP1={data['params']['tp1_mult']}, "
              f"TP2={data['params']['tp2_mult']}, TP3={data['params']['tp3_mult']}")
        print(f"          Tenkan={data['params']['tenkan']}, Kijun={data['params']['kijun']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    Path("outputs").mkdir(exist_ok=True)
    Path("config").mkdir(exist_ok=True)

    # Export JSON
    with open(f"outputs/cluster_analysis_{timestamp}.json", "w") as f:
        json.dump(cluster_info, f, indent=2)

    # Export Python config
    config_code = generate_cluster_config(cluster_info)
    with open(f"config/cluster_params_{timestamp}.py", "w") as f:
        f.write(config_code)

    print(f"\n✓ Exported: outputs/cluster_analysis_{timestamp}.json")
    print(f"✓ Exported: config/cluster_params_{timestamp}.py")

    return cluster_info


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to scan results CSV")
    args = parser.parse_args()

    run_full_analysis(args.input)
```

---

## 7. FICHIER: scripts/run_full_pipeline.py

```python
"""
Full Pipeline: Download -> Optimize -> Cluster -> Export
One command to rule them all
"""
import argparse
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Multi-Asset Scan Pipeline")
    parser.add_argument("--skip-download", action="store_true", help="Skip data download")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel workers")
    parser.add_argument("--assets", nargs="+", default=None, help="Specific assets to scan")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    print("="*70)
    print("MULTI-ASSET SCAN PIPELINE")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*70)

    # Step 1: Download data
    if not args.skip_download:
        print("\n[STEP 1/3] Downloading OHLCV data...")
        from scripts.download_data import download_all
        download_all()
    else:
        print("\n[STEP 1/3] Skipping download (--skip-download)")

    # Step 2: Parallel optimization
    print("\n[STEP 2/3] Running parallel optimization...")
    from optimization.parallel_optimizer import run_parallel_scan
    scan_df = run_parallel_scan(assets=args.assets, n_workers=args.workers)
    scan_path = f"outputs/multiasset_scan_{timestamp}.csv"

    # Step 3: Cluster analysis
    print("\n[STEP 3/3] Running cluster analysis...")
    from analysis.cluster_params import run_full_analysis
    cluster_info = run_full_analysis(scan_path)

    # Final summary
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)
    print(f"\nOutputs:")
    print(f"  - outputs/multiasset_scan_{timestamp}.csv")
    print(f"  - outputs/cluster_analysis_{timestamp}.json")
    print(f"  - config/cluster_params_{timestamp}.py")

    success_count = len(scan_df[scan_df["status"] == "SUCCESS"])
    cluster_count = cluster_info["n_clusters"]
    print(f"\nStats:")
    print(f"  - Assets scanned: {success_count}")
    print(f"  - Clusters found: {cluster_count}")
    print(f"  - Silhouette score: {cluster_info['silhouette_score']:.3f}")


if __name__ == "__main__":
    main()
```

---

## 8. USAGE

### Installation dépendances
```bash
pip install ccxt optuna scikit-learn pandas numpy pyarrow
```

### Commandes

```bash
# Full pipeline (download + optimize + cluster)
python scripts/run_full_pipeline.py --workers 8

# Skip download si data déjà présente
python scripts/run_full_pipeline.py --skip-download --workers 8

# Assets spécifiques seulement
python scripts/run_full_pipeline.py --assets HYPE AVAX SUI --workers 4

# Download seul
python scripts/download_data.py

# Optimization seule
python -m optimization.parallel_optimizer --workers 8

# Clustering seul (sur résultats existants)
python -m analysis.cluster_params --input outputs/multiasset_scan_20260120_1530.csv
```

---

## 9. OUTPUTS ATTENDUS

### multiasset_scan_{timestamp}.csv
```
asset,status,sl_mult,tp1_mult,tp2_mult,tp3_mult,tenkan,kijun,tenkan_5,kijun_5,is_sharpe,val_sharpe,oos_sharpe,oos_trades,wfe
HYPE,SUCCESS,4.0,5.0,3.0,6.0,8,28,12,22,2.45,2.10,1.95,85,0.80
AVAX,SUCCESS,4.5,4.75,3.5,7.0,10,30,11,24,2.80,2.40,2.20,92,0.79
...
```

### cluster_analysis_{timestamp}.json
```json
{
  "n_clusters": 3,
  "clusters": {
    "cluster_0": {
      "assets": ["HYPE", "INJ", "SEI"],
      "size": 3,
      "params": {"sl_mult": 4.0, "tp1_mult": 5.0, ...},
      "avg_oos_sharpe": 2.15,
      "avg_oos_trades": 88
    },
    ...
  },
  "silhouette_score": 0.72
}
```

### config/cluster_params_{timestamp}.py
```python
CLUSTER_PARAMS = {
    "cluster_0": {
        "assets": ["HYPE", "INJ", "SEI"],
        "atr": {"sl_mult": 4.0, "tp1_mult": 5.0, "tp2_mult": 3.0, "tp3_mult": 6.0},
        "ichimoku": {"tenkan": 8, "kijun": 28},
        "five_in_one": {"tenkan_5": 12, "kijun_5": 22},
    },
    ...
}

ASSET_CLUSTER = {
    "HYPE": "cluster_0",
    "INJ": "cluster_0",
    ...
}
```

---

## 10. CRITÈRES DE SUCCÈS

| Critère | Seuil | Description |
|---------|-------|-------------|
| OOS Sharpe | > 1.0 | Minimum pour considérer l'asset |
| WFE | > 0.6 | Walk-Forward Efficiency |
| OOS Trades | > 50 | Significativité statistique |
| Cluster Size | >= 3 | Min assets par cluster |
| Param Loss | < 15% | Perte max vs optimal individuel |
| Silhouette | > 0.5 | Qualité des clusters |

---

## 11. TEMPS ESTIMÉ

| Config | 10 Assets |
|--------|-----------|
| Séquentiel (1 core) | ~5h |
| 4 cores | ~1h15 |
| 8 cores | ~40 min |
| 10 cores | ~30 min |

---

## 12. PROCHAINES ÉTAPES POST-SCAN

1. [ ] Analyser résultats scan
2. [ ] Valider clusters (test params cluster sur chaque membre)
3. [ ] Mesurer perte perf vs optimal individuel
4. [ ] Décider config finale: N clusters vs N assets
5. [ ] Mettre à jour ASSET_CONFIG production
6. [ ] Backtest portfolio combiné (13 assets max)
7. [ ] Stress test portfolio
