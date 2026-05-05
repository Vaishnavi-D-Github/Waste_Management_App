"""
Fit K-means clustering on merged waste + location features and save model.pkl for ml_engine.

Features (same order as ml_engine.predict_cluster): waste, delay, density, area
  waste:    0=Low, 1=Medium, 2=High
  delay:    Delay_Days (integer)
  density:  0=Low, 1=Medium, 2=High
  area:     0=Residential, 1=Commercial

Cluster IDs are integer labels 0..k-1; scripts/mine_apriori attaches K_<id> per row so Apriori
can relate bins/delay/density/area patterns to clusters.

(This uses K-means: K cluster centers partition the feature space—often what people mean by
“KNN clustering” colloquially; classical K-Nearest Neighbors is supervised, not clustering.)
"""
from __future__ import annotations

import json
import math
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, adjusted_rand_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
MODEL_PATH = ROOT / "model.pkl"
METRICS_PATH = ROOT / "model_metrics.json"
ROUTES_PATH = ROOT / "cluster_routes.json"

WASTE_MAP = {"Low": 0, "Medium": 1, "High": 2}
DENSITY_MAP = {"Low": 0, "Medium": 1, "High": 2}
AREA_MAP = {"Residential": 0, "Commercial": 1}


def load_training_frame() -> pd.DataFrame:
    waste = pd.read_csv(DATASET / "waste_data_realistic.csv")
    loc = pd.read_csv(DATASET / "location_data.csv")
    return waste.merge(loc, on="Location_ID", how="left")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    x = pd.DataFrame(
        {
            "waste": df["Waste_Level"].map(WASTE_MAP),
            "delay": df["Delay_Days"].astype(int),
            "density": df["Population_Density"].map(DENSITY_MAP),
            "area": df["Area_Type"].map(AREA_MAP),
        }
    )
    if x.isnull().any().any():
        raise ValueError("Unexpected null after encoding; check CSV values vs maps.")
    return x


def choose_k(n: int) -> int:
    if n < 4:
        return max(2, min(n - 1, 2))
    return max(3, min(8, int(round(math.sqrt(n)))))


def route_for_cluster(not_picked_rate: float) -> str:
    if not_picked_rate >= 0.5:
        return "DISPOSE"
    if not_picked_rate >= 0.25:
        return "MONITOR"
    return "WAIT"


def _majority_pickup_predictions(cluster_ids: np.ndarray, y_picked: np.ndarray, k: int) -> np.ndarray:
    """Per cluster: predict Pickup_Status as majority vote (Picked=1 vs Not)."""
    out = np.zeros(len(cluster_ids), dtype=int)
    for c in range(k):
        mask = cluster_ids == c
        if not np.any(mask):
            continue
        votes = y_picked[mask]
        out[mask] = 1 if votes.mean() >= 0.5 else 0
    return out


def main() -> None:
    df = load_training_frame()
    X = build_features(df)
    n = len(X)
    if n < 4:
        raise SystemExit("Need at least 4 rows to fit clustering reliably.")

    k = choose_k(n)
    if k >= n:
        k = max(2, n - 1)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X.to_numpy())
    km = KMeans(n_clusters=k, random_state=42, n_init="auto")
    labels = km.fit_predict(Xs)

    inertia = float(km.inertia_)
    sil = None
    if 1 < k < n:
        try:
            sil = float(silhouette_score(Xs, labels))
        except ValueError:
            sil = None

    y_picked = (df["Pickup_Status"] == "Picked").astype(int).to_numpy()
    not_picked = 1.0 - y_picked.astype(float)
    cluster_routes: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for c in range(k):
        mask = labels == c
        sizes[str(c)] = int(mask.sum())
        rate = float(not_picked[mask].mean()) if mask.any() else 0.0
        cluster_routes[str(c)] = route_for_cluster(rate)

    # How well clusters separate pickup outcomes (not intrinsic K-means "accuracy"; see metric notes below).
    preds_full = _majority_pickup_predictions(labels, y_picked, k)
    pickup_alignment_accuracy_train = float(accuracy_score(y_picked, preds_full))
    adjusted_rand_pickup_vs_cluster = float(adjusted_rand_score(y_picked, labels))

    holdout_pickup_alignment_accuracy: float | None = None
    if n >= 10:
        try:
            split_kw: dict = {"test_size": 0.3, "random_state": 42}
            if len(np.unique(y_picked)) >= 2:
                split_kw["stratify"] = y_picked
            X_train, X_test, y_train, y_test = train_test_split(
                X.to_numpy(), y_picked, **split_kw
            )
            scaler_h = StandardScaler().fit(X_train)
            xt = scaler_h.transform(X_train)
            xsv = scaler_h.transform(X_test)
            km_h = KMeans(n_clusters=k, random_state=42, n_init="auto")
            lab_train = km_h.fit_predict(xt)
            lab_test = km_h.predict(xsv)
            majority_per_cluster = np.zeros(k, dtype=int)
            cluster_seen_train = np.zeros(k, dtype=bool)
            for c in range(k):
                m_tr = lab_train == c
                if np.any(m_tr):
                    majority_per_cluster[c] = 1 if y_train[m_tr].mean() >= 0.5 else 0
                    cluster_seen_train[c] = True
            global_majority = 1 if y_train.mean() >= 0.5 else 0
            pred_test = np.array(
                [
                    (
                        int(majority_per_cluster[int(lab_test[i])])
                        if cluster_seen_train[int(lab_test[i])]
                        else global_majority
                    )
                    for i in range(len(lab_test))
                ],
                dtype=int,
            )
            holdout_pickup_alignment_accuracy = float(accuracy_score(y_test, pred_test))
        except ValueError:
            holdout_pickup_alignment_accuracy = None

    bundle = {
        "kind": "kmeans_cluster",
        "scaler": scaler,
        "kmeans": km,
        "n_clusters": k,
        "feature_names": ["waste", "delay", "density", "area"],
        "encodings": {
            "waste": WASTE_MAP,
            "density": DENSITY_MAP,
            "area": AREA_MAP,
        },
    }
    MODEL_PATH.write_bytes(pickle.dumps(bundle))
    ROUTES_PATH.write_text(json.dumps(cluster_routes, indent=2), encoding="utf-8")

    payload = {
        "algorithm": "KMeans clustering (k partitions on scaled features)",
        "note": (
            "Cluster labels K_0..K_{k-1} are mined with Apriori in scripts/mine_apriori.py; "
            "routing defaults use historical not-picked rate per cluster."
        ),
        "metric_notes": (
            "K-means has no supervised accuracy by itself; pickup_alignment_accuracy is the fraction "
            "of rows whose Pickup_Status matches the modal Picked/Not-Picked majority inside their assigned cluster "
            "(train = same data used to fit; holdout fits K-means only on train, then evaluates on held-out rows). "
            "adjusted_rand_score measures agreement between cluster IDs and pickup labels (chance-adjusted)."
        ),
        "n_clusters": k,
        "features": ["waste", "delay", "density", "area"],
        "encodings": bundle["encodings"],
        "n_samples": n,
        "pickup_alignment_accuracy_train": round(pickup_alignment_accuracy_train, 4),
        "pickup_alignment_accuracy_holdout": (
            round(holdout_pickup_alignment_accuracy, 4)
            if holdout_pickup_alignment_accuracy is not None
            else None
        ),
        "adjusted_rand_pickup_vs_cluster": round(adjusted_rand_pickup_vs_cluster, 4),
        "inertia": round(inertia, 4),
        "silhouette_score": round(sil, 4) if sil is not None else None,
        "cluster_sizes": sizes,
        "cluster_routes_file": str(ROUTES_PATH.relative_to(ROOT)),
        "model_file": str(MODEL_PATH.relative_to(ROOT)),
    }
    METRICS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Saved:", MODEL_PATH)
    print("Cluster routes:", ROUTES_PATH)
    print("Metrics:", METRICS_PATH)
    print("k =", k, " inertia =", round(inertia, 4), " silhouette =", payload["silhouette_score"])
    print(
        "Pickup alignment accuracy (train / holdout):",
        payload["pickup_alignment_accuracy_train"],
        "/",
        payload["pickup_alignment_accuracy_holdout"],
    )
    print("Adjusted Rand (pickup vs cluster):", payload["adjusted_rand_pickup_vs_cluster"])
    print("Routes:", cluster_routes)


if __name__ == "__main__":
    main()
