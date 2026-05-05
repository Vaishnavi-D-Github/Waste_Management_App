"""
Mine association rules from merged waste + location data (Apriori via mlxtend).

Loads model.pkl from scripts/train_model.py (K-means bundle). Each transaction includes the
same feature items as before plus a cluster label K_<id> predicted by that model for that row.

Writes dataset/apriori_rules_mined.csv used by app.services.apriori_engine.

Rules relate bins like W_High, Del_3p, density, area type to cluster labels K_0, K_1, ...
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"
MODEL_PATH = ROOT / "model.pkl"
OUTPUT_CSV = DATASET / "apriori_rules_mined.csv"
META_JSON = DATASET / "apriori_meta.json"

WASTE_MAP = {"Low": 0, "Medium": 1, "High": 2}
DENSITY_MAP = {"Low": 0, "Medium": 1, "High": 2}
AREA_MAP = {"Residential": 0, "Commercial": 1}


def load_merged() -> pd.DataFrame:
    waste = pd.read_csv(DATASET / "waste_data_realistic.csv")
    loc = pd.read_csv(DATASET / "location_data.csv")
    return waste.merge(loc, on="Location_ID", how="left")


def load_cluster_bundle():
    if not MODEL_PATH.is_file():
        raise SystemExit(f"Missing {MODEL_PATH}; run scripts/train_model.py first.")
    with MODEL_PATH.open("rb") as f:
        bundle = pickle.load(f)
    if not isinstance(bundle, dict) or bundle.get("kind") != "kmeans_cluster":
        raise SystemExit("model.pkl must be a K-means bundle from scripts/train_model.py.")
    return bundle


def delay_bin(days: int) -> str:
    d = int(days)
    if d <= 0:
        return "Del_0"
    if d <= 2:
        return "Del_12"
    return "Del_3p"


def row_cluster_id(bundle: dict, row: pd.Series) -> int:
    scaler = bundle["scaler"]
    km = bundle["kmeans"]
    vec = [
        float(WASTE_MAP[row["Waste_Level"]]),
        float(row["Delay_Days"]),
        float(DENSITY_MAP[row["Population_Density"]]),
        float(AREA_MAP[row["Area_Type"]]),
    ]
    xs = scaler.transform([vec])
    return int(km.predict(xs)[0])


def row_to_items(bundle: dict, row: pd.Series) -> list[str]:
    cid = row_cluster_id(bundle, row)
    wl = row["Waste_Level"]
    items = [
        f"W_{wl}",
        delay_bin(row["Delay_Days"]),
        f"D_{row['Population_Density']}",
        "A_Res" if row["Area_Type"] == "Residential" else "A_Com",
        f"K_{cid}",
    ]
    return items


def _frozenset_to_str(fs: frozenset) -> str:
    return "|".join(sorted(fs, key=lambda x: str(x)))


def _cluster_consequent_rule(row) -> bool:
    cons = row["consequents"]
    if len(cons) != 1:
        return False
    c = list(cons)[0]
    return str(c).startswith("K_")


def main() -> None:
    bundle = load_cluster_bundle()
    df = load_merged()
    transactions = [row_to_items(bundle, row) for _, row in df.iterrows()]
    n = len(transactions)
    if n < 3:
        raise SystemExit("Need at least 3 rows for Apriori.")

    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    ohe = pd.DataFrame(te_ary, columns=te.columns_)

    min_sup = max(0.12, 2 / n)
    freq = apriori(ohe, min_support=min_sup, use_colnames=True)
    if freq.empty:
        min_sup = max(0.08, 1 / n)
        freq = apriori(ohe, min_support=min_sup, use_colnames=True)

    if freq.empty:
        OUTPUT_CSV.write_text("antecedents,consequents,support,confidence,lift\n", encoding="utf-8")
        META_JSON.write_text(
            json.dumps({"n_transactions": n, "note": "no frequent itemsets at min_support"}, indent=2),
            encoding="utf-8",
        )
        print("No frequent itemsets; wrote empty rules file.")
        return

    rules = association_rules(freq, metric="confidence", min_threshold=0.35)
    if rules.empty:
        rules = association_rules(freq, metric="confidence", min_threshold=0.25)
    if rules.empty:
        rules = association_rules(freq, metric="confidence", min_threshold=0.15)

    cluster_rules = rules[rules.apply(_cluster_consequent_rule, axis=1)].copy()
    if not cluster_rules.empty:
        rules = cluster_rules
    rules = rules.sort_values(["lift", "confidence"], ascending=False)

    out_rows = []
    for _, row in rules.iterrows():
        out_rows.append(
            {
                "antecedents": _frozenset_to_str(row["antecedents"]),
                "consequents": _frozenset_to_str(row["consequents"]),
                "support": round(float(row["support"]), 6),
                "confidence": round(float(row["confidence"]), 6),
                "lift": round(float(row["lift"]), 6),
            }
        )

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(OUTPUT_CSV, index=False)

    meta = {
        "n_transactions": n,
        "min_support_used": min_sup,
        "n_rules_exported": len(out_df),
        "rules_file": str(OUTPUT_CSV.relative_to(ROOT)),
        "cluster_item_prefix": "K_",
        "n_clusters_in_model": bundle.get("n_clusters"),
    }
    META_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("Saved:", OUTPUT_CSV)
    print("Meta:", META_JSON)
    print("Rules:", len(out_df))


if __name__ == "__main__":
    main()
