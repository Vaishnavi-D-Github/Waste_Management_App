import pandas as pd
from sqlalchemy import text

from ..database import SessionLocal

_mined_rules: pd.DataFrame | None = None
_legacy_rules: pd.DataFrame | None = None


def _load_mined() -> pd.DataFrame | None:
    global _mined_rules
    if _mined_rules is not None:
        return _mined_rules

    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT antecedents, consequents, support, confidence, lift
                FROM apriori_rules
                ORDER BY lift DESC, confidence DESC
                """
            )
        ).fetchall()

    if not rows:
        return None

    df = pd.DataFrame(
        rows,
        columns=["antecedents", "consequents", "support", "confidence", "lift"],
    )
    if df.empty or "antecedents" not in df.columns:
        return None
    _mined_rules = df
    return _mined_rules


def _load_legacy() -> pd.DataFrame | None:
    global _legacy_rules
    if _legacy_rules is not None:
        return _legacy_rules

    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT antecedents, consequents
                FROM legacy_rules
                """
            )
        ).fetchall()

    if not rows:
        return None

    _legacy_rules = pd.DataFrame(rows, columns=["antecedents", "consequents"])
    return _legacy_rules


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


def _action_from_consequent(cons: str, waste: int) -> str | None:
    s = str(cons).strip()
    if s in {"Act_WAIT", "Act_MONITOR", "Act_DISPOSE"}:
        return s[4:]
    wi = _clamp_int(waste, 0, 2)
    if "Out_Picked" in s:
        return "WAIT"
    if "Out_NotPicked" in s:
        if wi >= 2:
            return "DISPOSE"
        if wi == 1:
            return "MONITOR"
        return "WAIT"
    return None


def _decision_from_mined(waste: int, delay: int, density: int, area: int) -> str | None:
    df = _load_mined()
    if df is None or df.empty:
        return None

    user_items = _user_itemset(waste, delay, density, area)
    # Prefer more specific matching rules first (larger antecedents),
    # then break ties with stronger association (higher lift) and confidence.
    best_rule_size = -1
    best_lift = -1.0
    best_conf = -1.0
    best_action = None

    for _, row in df.iterrows():
        ants = _parse_itemset(row["antecedents"])
        if not ants or not ants <= user_items:
            continue
        conf = float(row.get("confidence", 0.0))
        lift = float(row.get("lift", 0.0))
        action = _action_from_consequent(str(row["consequents"]), waste)
        if action is None:
            continue
        rule_size = len(ants)
        if rule_size > best_rule_size or (
            rule_size == best_rule_size
            and (lift > best_lift or (lift == best_lift and conf > best_conf))
        ):
            best_rule_size = rule_size
            best_lift = lift
            best_conf = conf
            best_action = action

    return best_action


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
