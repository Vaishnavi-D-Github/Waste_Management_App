import math

import pandas as pd
from sqlalchemy import text

from ..database import SessionLocal

bins: pd.DataFrame | None = None


def _load_bins() -> pd.DataFrame:
    global bins
    if bins is not None:
        return bins

    with SessionLocal() as db:
        rows = db.execute(
            text(
                """
                SELECT latitude AS Latitude, longitude AS Longitude
                FROM disposal_locations
                """
            )
        ).fetchall()

    bins = pd.DataFrame(rows, columns=["Latitude", "Longitude"])
    return bins

def find_nearest_bin(user_lat, user_lon):
    bin_df = _load_bins()
    if bin_df.empty:
        return None

    min_dist = float("inf")
    nearest = None

    for _, row in bin_df.iterrows():
        d = math.sqrt(
            (user_lat - row["Latitude"])**2 +
            (user_lon - row["Longitude"])**2
        )

        if d < min_dist:
            min_dist = d
            nearest = row

    return nearest