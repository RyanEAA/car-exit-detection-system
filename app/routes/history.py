from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.detection import Detection
from app.models.user import User
from app.schemas import DetectionRecordResponse, HistoryResponse

router = APIRouter()


@router.get("/", response_model=HistoryResponse)
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HistoryResponse:
    detections = (
        db.query(Detection)
        .filter(Detection.user_id == current_user.id)
        .order_by(Detection.captured_at.desc())
        .all()
    )

    return HistoryResponse(
        items=[
            DetectionRecordResponse(
                detection=detection,
                image_url=f"/{detection.image_path.replace(os.sep, '/')}",
                media_type=detection.media_type,
            )
            for detection in detections
        ]
    )