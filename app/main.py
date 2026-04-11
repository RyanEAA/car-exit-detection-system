import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes.auth import router as auth_router
from app.routes.detect import router as detect_router
from app.routes.history import router as history_router

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

app = FastAPI(title="Car Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def startup() -> None:
    init_db()

# routes
app.include_router(auth_router, prefix="/auth")
app.include_router(detect_router, prefix="/detect")
app.include_router(history_router, prefix="/history")

@app.get("/")
def root():
    return {"message": "API is running"}