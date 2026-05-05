"""
Mine association rules from merged waste + location data (Apriori via mlxtend).

Each transaction includes the feature items plus a direct routing action label:
Act_WAIT, Act_MONITOR, or Act_DISPOSE.

Writes mined rules into MySQL table `apriori_rules`.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal

DATASET = ROOT / "dataset"
META_JSON = DATASET / "apriori_meta.json"


def load_merged() -> pd.DataFrame:
    with SessionLocal() as db:
        waste_rows = db.execute(
            text(
                """
                SELECT
                    location_id AS Location_ID,
                    date AS Date,
                    waste_level AS Waste_Level,
                    pickup_status AS Pickup_Status,
                    delay_days AS Delay_Days
                FROM waste_data
                """
            )
        ).fetchall()
        loc_rows = db.execute(
            text(
                """
                SELECT
                    location_id AS Location_ID,
                    latitude AS Latitude,
                    longitude AS Longitude,
                    area_type AS Area_Type,
                    population_density AS Population_Density
                FROM location_data
                """
            )
        ).fetchall()

    waste = pd.DataFrame(
        waste_rows,
        columns=["Location_ID", "Date", "Waste_Level", "Pickup_Status", "Delay_Days"],
    )
    loc = pd.DataFrame(
        loc_rows,
        columns=["Location_ID", "Latitude", "Longitude", "Area_Type", "Population_Density"],
    )
    return waste.merge(loc, on="Location_ID", how="left")


def delay_bin(days: int) -> str:
    d = int(days)
    if d <= 0:
        return "Del_0"
    if d <= 2:
        return "Del_12"
    return "Del_3p"


def row_action(row: pd.Series) -> str:
    if row["Pickup_Status"] == "Picked":
        return "WAIT"
    if row["Waste_Level"] == "High":
        return "DISPOSE"
    if row["Waste_Level"] == "Medium":
        return "MONITOR"
    return "WAIT"


def row_to_items(row: pd.Series) -> list[str]:
    wl = row["Waste_Level"]
    items = [
        f"W_{wl}",
        delay_bin(row["Delay_Days"]),
        f"D_{row['Population_Density']}",
        "A_Res" if row["Area_Type"] == "Residential" else "A_Com",
        f"Act_{row_action(row)}",
    ]
    return items


def _frozenset_to_str(fs: frozenset) -> str:
    return "|".join(sorted(fs, key=lambda x: str(x)))


def _action_consequent_rule(row) -> bool:
    cons = row["consequents"]
    if len(cons) != 1:
        return False
    c = list(cons)[0]
    return str(c).startswith("Act_")


def save_rules_to_db(out_df: pd.DataFrame) -> None:
    with SessionLocal() as db:
        db.execute(text("DELETE FROM apriori_rules"))
        for _, row in out_df.iterrows():
            db.execute(
                text(
                    """
                    INSERT INTO apriori_rules
                    (antecedents, consequents, support, confidence, lift)
                    VALUES (:antecedents, :consequents, :support, :confidence, :lift)
                    """
                ),
                {
                    "antecedents": str(row["antecedents"]),
                    "consequents": str(row["consequents"]),
                    "support": float(row["support"]),
                    "confidence": float(row["confidence"]),
                    "lift": float(row["lift"]),
                },
            )
        db.commit()


def main() -> None:
    df = load_merged()
    transactions = [row_to_items(row) for _, row in df.iterrows()]
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
        save_rules_to_db(
            pd.DataFrame(columns=["antecedents", "consequents", "support", "confidence", "lift"])
        )
        META_JSON.write_text(
            json.dumps({"n_transactions": n, "note": "no frequent itemsets at min_support"}, indent=2),
            encoding="utf-8",
        )
        print("No frequent itemsets; cleared apriori_rules table.")
        return

    rules = association_rules(freq, metric="confidence", min_threshold=0.35)
    if rules.empty:
        rules = association_rules(freq, metric="confidence", min_threshold=0.25)
    if rules.empty:
        rules = association_rules(freq, metric="confidence", min_threshold=0.15)

    action_rules = rules[rules.apply(_action_consequent_rule, axis=1)].copy()
    if not action_rules.empty:
        rules = action_rules
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
    save_rules_to_db(out_df)

    meta = {
        "n_transactions": n,
        "min_support_used": min_sup,
        "n_rules_exported": len(out_df),
        "rules_table": "apriori_rules",
        "action_item_prefix": "Act_",
    }
    META_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("Saved to table: apriori_rules")
    print("Meta:", META_JSON)
    print("Rules:", len(out_df))


if __name__ == "__main__":
    main()
