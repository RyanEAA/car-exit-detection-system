from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.detect import router as detect_router

app = FastAPI(title="Car Detection API")

# ✅ ADD CORS HERE (right after app is created)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routes
app.include_router(detect_router, prefix="/detect")

@app.get("/")
def root():
    return {"message": "API is running"}