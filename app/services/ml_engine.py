import json
import pickle
from pathlib import Path

_bundle = None


def _get_bundle():
    global _bundle
    if _bundle is None:
        path = Path(__file__).resolve().parents[2] / "model.pkl"
        if not path.is_file():
            raise FileNotFoundError(
                "model.pkl not found at project root. Run scripts/train_model.py to fit clustering."
            )
        with path.open("rb") as f:
            raw = pickle.load(f)
        if isinstance(raw, dict) and raw.get("kind") == "kmeans_cluster":
            _bundle = raw
        else:
            raise ValueError(
                "model.pkl is not a K-means clustering bundle. Re-run scripts/train_model.py."
            )
    return _bundle


def predict_cluster(waste, delay, density, area):
    b = _get_bundle()
    scaler = b["scaler"]
    km = b["kmeans"]
    row = scaler.transform([[float(waste), float(delay), float(density), float(area)]])
    return int(km.predict(row)[0])


def predict_risk(waste, delay, density, area):
    """Backward-compatible alias: returns cluster id (not pickup probability)."""
    return predict_cluster(waste, delay, density, area)


def load_training_metrics():
    """model_metrics.json from scripts/train_model.py (accuracy aligned with pickup labels, etc.)."""
    path = Path(__file__).resolve().parents[2] / "model_metrics.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
