"""
Lightweight smoke checks for the Waste Management System.

Runs without starting uvicorn:
- verifies DB connectivity and expected tables exist
- exercises key JSON endpoints via FastAPI TestClient

Usage (PowerShell):
  python scripts/smoke_check.py
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path
from dataclasses import dataclass

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    details: str = ""


def _check_db() -> list[CheckResult]:
    results: list[CheckResult] = []
    tables = [
        "users",
        "location_data",
        "waste_data",
        "disposal_locations",
        "legacy_rules",
        "apriori_rules",
    ]

    try:
        with engine.begin() as conn:
            for table in tables:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
                    results.append(CheckResult(f"db.table.{table}", True, f"rows={count}"))
                except Exception as exc:  # pragma: no cover
                    results.append(
                        CheckResult(f"db.table.{table}", False, f"{type(exc).__name__}: {exc}")
                    )
    except Exception as exc:  # pragma: no cover
        results.append(CheckResult("db.connect", False, f"{type(exc).__name__}: {exc}"))

    return results


def _check_api() -> list[CheckResult]:
    client = TestClient(app)
    results: list[CheckResult] = []

    # 1) basic liveness/docs routing
    r = client.get("/docs")
    results.append(CheckResult("api.docs", r.status_code == 200, f"status={r.status_code}"))

    # 2) register -> login
    username = f"smoke_{secrets.token_hex(4)}"
    password = "smoke_password"
    register = client.post(
        "/api/register",
        data={
            "username": username,
            "password": password,
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
    )
    results.append(
        CheckResult(
            "api.register",
            register.status_code in (200, 201),
            f"status={register.status_code}",
        )
    )

    login = client.post("/api/login", data={"username": username, "password": password})
    results.append(CheckResult("api.login", login.status_code == 200, f"status={login.status_code}"))

    # 3) prediction (expect one of known decisions)
    predict = client.post(
        "/api/predict",
        data={
            "waste": 2,
            "delay": 1,
            "density": 2,
            "area": 0,
            "lat": 12.9716,
            "lon": 77.5946,
        },
    )
    ok = predict.status_code == 200
    decision = None
    if ok:
        try:
            decision = predict.json().get("decision")
            ok = decision in ("WAIT", "MONITOR", "DISPOSE")
        except Exception:  # pragma: no cover
            ok = False

    results.append(
        CheckResult(
            "api.predict",
            ok,
            f"status={predict.status_code}, decision={decision!r}",
        )
    )

    return results


def main() -> int:
    results = [*_check_db(), *_check_api()]
    failed = [r for r in results if not r.ok]

    for r in results:
        status = "OK" if r.ok else "FAIL"
        details = f" ({r.details})" if r.details else ""
        print(f"[{status}] {r.name}{details}")

    if failed:
        print(f"\nFAILED: {len(failed)}/{len(results)} checks")
        return 1

    print(f"\nPASSED: {len(results)}/{len(results)} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
