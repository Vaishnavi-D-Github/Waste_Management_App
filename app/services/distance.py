import math
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
bins = pd.read_csv(_ROOT / "dataset" / "disposal_locations.csv")

def find_nearest_bin(user_lat, user_lon):
    min_dist = float("inf")
    nearest = None

    for _, row in bins.iterrows():
        d = math.sqrt(
            (user_lat - row["Latitude"])**2 +
            (user_lon - row["Longitude"])**2
        )

        if d < min_dist:
            min_dist = d
            nearest = row

    return nearest