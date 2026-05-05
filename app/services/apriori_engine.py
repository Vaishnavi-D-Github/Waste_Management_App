import json
from pathlib import Path

import pandas as pd

from .ml_engine import predict_cluster

_ROOT = Path(__file__).resolve().parents[2]
_MINED_PATH = _ROOT / "dataset" / "apriori_rules_mined.csv"
_LEGACY_PATH = _ROOT / "dataset" / "rules.csv"
_ROUTES_PATH = _ROOT / "cluster_routes.json"

_mined_rules: pd.DataFrame | None = None
_legacy_rules: pd.DataFrame | None = None
_cluster_routes_loaded: bool = False
_cluster_routes: dict[str, str] | None = None


def _load_mined() -> pd.DataFrame | None:
    global _mined_rules
    if _mined_rules is not None:
        return _mined_rules
    if not _MINED_PATH.exists():
        return None
    df = pd.read_csv(_MINED_PATH)
    if df.empty or "antecedents" not in df.columns:
        return None
    _mined_rules = df
    return _mined_rules


def _load_legacy() -> pd.DataFrame | None:
    global _legacy_rules
    if _legacy_rules is not None:
        return _legacy_rules
    if not _LEGACY_PATH.exists():
        return None
    _legacy_rules = pd.read_csv(_LEGACY_PATH)
    return _legacy_rules


def _load_cluster_routes() -> dict[str, str]:
    global _cluster_routes_loaded, _cluster_routes
    if _cluster_routes_loaded:
        return _cluster_routes or {}
    _cluster_routes_loaded = True
    if not _ROUTES_PATH.exists():
        _cluster_routes = {}
        return {}
    try:
        _cluster_routes = json.loads(_ROUTES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        _cluster_routes = {}
    return _cluster_routes or {}


def _clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(int(v), hi))


def _delay_bin(delay: int) -> str:
    d = int(delay)
    if d <= 0:
        return "Del_0"
    if d <= 2:
        return "Del_12"
    return "Del_3p"


def _user_itemset(waste: int, delay: int, density: int, area: int) -> set[str]:
    waste_labels = ["Low", "Medium", "High"]
    density_labels = ["Low", "Medium", "High"]
    wi = _clamp_int(waste, 0, 2)
    di = _clamp_int(density, 0, 2)
    area_flag = "A_Res" if int(area) == 0 else "A_Com"
    return {
        f"W_{waste_labels[wi]}",
        _delay_bin(delay),
        f"D_{density_labels[di]}",
        area_flag,
    }


def _parse_itemset(s: str) -> set[str]:
    if pd.isna(s) or not str(s).strip():
        return set()
    return {x.strip() for x in str(s).split("|") if x.strip()}


def _route_from_outcome(consequent: str, waste: int) -> str:
    wi = _clamp_int(waste, 0, 2)
    if "Out_Picked" in consequent:
        return "WAIT"
    if "Out_NotPicked" in consequent:
        if wi >= 2:
            return "DISPOSE"
        if wi == 1:
            return "MONITOR"
        return "WAIT"
    return "WAIT"


def _cluster_id_from_consequent(cons: str) -> str | None:
    s = str(cons).strip()
    if "|" in s:
        return None
    if not s.startswith("K_"):
        return None
    tail = s[2:]
    return tail if tail.isdigit() else None


def _decision_from_mined(waste: int, delay: int, density: int, area: int) -> str | None:
    df = _load_mined()
    if df is None or df.empty:
        return None

    user_items = _user_itemset(waste, delay, density, area)
    routes = _load_cluster_routes()

    best_cluster_conf = -1.0
    best_cluster_row = None
    best_out_conf = -1.0
    best_out_row = None

    for _, row in df.iterrows():
        ants = _parse_itemset(row["antecedents"])
        if not ants or not ants <= user_items:
            continue
        conf = float(row.get("confidence", 0.0))
        cons = str(row["consequents"])
        cid = _cluster_id_from_consequent(cons)
        if cid is not None:
            if routes and cid not in routes:
                continue
            if conf > best_cluster_conf:
                best_cluster_conf = conf
                best_cluster_row = row
        elif "Out_" in cons:
            if conf > best_out_conf:
                best_out_conf = conf
                best_out_row = row

    if best_cluster_row is not None:
        cid = _cluster_id_from_consequent(str(best_cluster_row["consequents"]))
        if cid is not None:
            if routes:
                action = routes.get(cid)
                if action:
                    return action

    if best_out_row is not None:
        return _route_from_outcome(str(best_out_row["consequents"]), waste)

    return None


def _decision_from_legacy(waste: int, density: int) -> str:
    df = _load_legacy()
    if df is None or df.empty:
        return "WAIT"

    waste_map = ["Low", "Medium", "High"]
    density_map = ["Low", "Medium", "High"]
    wi = _clamp_int(waste, 0, 2)
    di = _clamp_int(density, 0, 2)
    w_key = f"W:{waste_map[wi]}"
    d_key = f"D:{density_map[di]}"

    for _, row in df.iterrows():
        antecedents = str(row["antecedents"])
        if w_key in antecedents and d_key in antecedents:
            cons = str(row["consequents"])
            if "Dispose" in cons:
                return "DISPOSE"
            if "Monitor" in cons:
                return "MONITOR"

    return "WAIT"


def apriori_decision(waste: int, delay: int, density: int, area: int) -> str:
    mined = _decision_from_mined(waste, delay, density, area)
    if mined is not None:
        return mined
    routes = _load_cluster_routes()
    if routes:
        try:
            cid = predict_cluster(waste, delay, density, area)
            action = routes.get(str(cid))
            if action:
                return action
        except (FileNotFoundError, ValueError):
            pass
    return _decision_from_legacy(waste, density)


def top_association_patterns(limit: int = 6) -> list[str]:
    df = _load_mined()
    if df is None or df.empty:
        return []

    sort_cols = [c for c in ("lift", "confidence") if c in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols, ascending=False)

    lines: list[str] = []
    for _, row in df.head(limit).iterrows():
        a = row.get("antecedents", "")
        c = row.get("consequents", "")
        conf = row.get("confidence", "")
        sup = row.get("support", "")
        lines.append(
            f"{a} -> {c} (support={sup}, confidence={conf})"
        )
    return lines
