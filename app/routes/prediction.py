from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .. import models
from ..database import SessionLocal
from ..services.apriori_engine import apriori_decision
from ..services.distance import find_nearest_bin
from ..services.recommendations import generate_recommendations

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _should_create_municipal_request(decision: str) -> bool:
    return decision == "DISPOSE"


def _priority_for_request(decision: str, waste: int, delay: int, density: int) -> str:
    score = 0
    if decision == "DISPOSE":
        score += 2
    if int(waste) >= 2:
        score += 1
    if int(delay) >= 3:
        score += 1
    if int(density) >= 2:
        score += 1
    if score >= 4:
        return "HIGH"
    if score >= 2:
        return "MEDIUM"
    return "LOW"


def _create_municipal_request(
    decision: str,
    waste: int,
    delay: int,
    density: int,
    area: int,
    lat: float,
    lon: float,
    bin_lat: float | None,
    bin_lon: float | None,
) -> int | None:
    if not _should_create_municipal_request(decision):
        return None

    priority = _priority_for_request(decision, waste, delay, density)
    with SessionLocal() as db:
        req = models.MunicipalRequest(
            decision=decision,
            waste=int(waste),
            delay=int(delay),
            density=int(density),
            area=int(area),
            lat=float(lat),
            lon=float(lon),
            bin_lat=bin_lat,
            bin_lon=bin_lon,
            status="PENDING",
            priority=priority,
            notes="Auto-created from DISPOSE prediction output.",
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return int(req.id)


def run_prediction(
    waste: int,
    delay: int,
    density: int,
    area: int,
    lat: float,
    lon: float,
) -> tuple[str, float | None, float | None, list[dict[str, str]], int | None]:
    decision = apriori_decision(waste, delay, density, area)
    bin_lat = None
    bin_lon = None

    if decision == "DISPOSE":
        bin_data = find_nearest_bin(lat, lon)
        if bin_data is not None:
            bin_lat = float(bin_data["Latitude"])
            bin_lon = float(bin_data["Longitude"])

    recommendations = generate_recommendations(decision, waste, delay, density, area)
    municipal_request_id = _create_municipal_request(
        decision, waste, delay, density, area, lat, lon, bin_lat, bin_lon
    )
    return decision, bin_lat, bin_lon, recommendations, municipal_request_id


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "decision": None,
            "bin_lat": None,
            "bin_lon": None,
            "recommendations": [],
        },
    )


@router.post("/predict", response_class=HTMLResponse)
def predict(
    request: Request,
    waste: int = Form(...),
    delay: int = Form(...),
    density: int = Form(...),
    area: int = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
):
    decision, bin_lat, bin_lon, recommendations, municipal_request_id = run_prediction(
        waste, delay, density, area, lat, lon
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "decision": decision,
            "bin_lat": bin_lat,
            "bin_lon": bin_lon,
            "recommendations": recommendations,
            "municipal_request_id": municipal_request_id,
        },
    )


@router.post("/api/predict")
def api_predict(
    waste: int = Form(...),
    delay: int = Form(...),
    density: int = Form(...),
    area: int = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
):
    decision, bin_lat, bin_lon, recommendations, municipal_request_id = run_prediction(
        waste, delay, density, area, lat, lon
    )
    return {
        "decision": decision,
        "bin_lat": bin_lat,
        "bin_lon": bin_lon,
        "recommendations": recommendations,
        "municipal_request_id": municipal_request_id,
    }
