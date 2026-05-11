from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas

router = APIRouter(prefix="/api/municipal", tags=["municipal"])

ALLOWED_STATUSES = {"PENDING", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "SKIPPED"}


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/requests")
def list_requests(
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[schemas.MunicipalRequestOut]:
    capped_limit = max(1, min(int(limit), 200))
    query = db.query(models.MunicipalRequest).order_by(models.MunicipalRequest.id.desc())
    if status:
        query = query.filter(models.MunicipalRequest.status == status.upper())

    rows = query.limit(capped_limit).all()
    return [
        schemas.MunicipalRequestOut(
            id=row.id,
            decision=row.decision,
            waste=row.waste,
            delay=row.delay,
            density=row.density,
            area=row.area,
            lat=row.lat,
            lon=row.lon,
            bin_lat=row.bin_lat,
            bin_lon=row.bin_lon,
            status=row.status,
            priority=row.priority,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.post("/requests/{request_id}/status")
def update_request_status(
    request_id: int,
    status: str = Form(...),
    notes: str | None = Form(None),
    db: Session = Depends(get_db),
):
    normalized = status.strip().upper()
    if normalized not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use one of: {sorted(ALLOWED_STATUSES)}")

    row = db.query(models.MunicipalRequest).filter(models.MunicipalRequest.id == request_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Municipal request not found.")

    row.status = normalized
    row.notes = notes
    db.commit()
    db.refresh(row)

    return {
        "message": "Request status updated",
        "request_id": row.id,
        "status": row.status,
        "notes": row.notes,
    }
