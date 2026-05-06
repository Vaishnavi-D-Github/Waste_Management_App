from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..services.apriori_engine import apriori_decision
from ..services.distance import find_nearest_bin

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def run_prediction(
    waste: int,
    delay: int,
    density: int,
    area: int,
    lat: float,
    lon: float,
) -> tuple[str, float | None, float | None]:
    decision = apriori_decision(waste, delay, density, area)
    bin_lat = None
    bin_lon = None

    if decision == "DISPOSE":
        bin_data = find_nearest_bin(lat, lon)
        if bin_data is not None:
            bin_lat = float(bin_data["Latitude"])
            bin_lon = float(bin_data["Longitude"])

    return decision, bin_lat, bin_lon


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
    decision, bin_lat, bin_lon = run_prediction(waste, delay, density, area, lat, lon)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "decision": decision,
            "bin_lat": bin_lat,
            "bin_lon": bin_lon,
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
    decision, bin_lat, bin_lon = run_prediction(waste, delay, density, area, lat, lon)
    return {"decision": decision, "bin_lat": bin_lat, "bin_lon": bin_lon}
