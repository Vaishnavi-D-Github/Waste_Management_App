from fastapi import APIRouter, Depends, Form
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .. import models, database, auth
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register Page
@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"request": request})

# Register Logic
@router.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: Session = Depends(get_db)
):
    hashed = auth.hash_password(password)

    user = models.User(
        username=username,
        password=hashed,
        latitude=latitude,
        longitude=longitude
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"error": "Username already taken. Choose another."}

    return {"message": "User registered successfully"}

# Login Page
@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

# Login Logic
@router.post("/")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or not auth.verify_password(password, user.password):
        return {"error": "Invalid credentials"}

    return {"message": "Login successful"}

@router.get("/map", response_class=HTMLResponse)
def map_page(request: Request):
    return templates.TemplateResponse(request, "map.html", {"request": request})
