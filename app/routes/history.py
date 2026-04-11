from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.detection import Detection
from app.models.user import User
from app.schemas import DetectionRecordResponse, DetectionUpdateRequest, HistoryResponse

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


@router.patch("/{detection_id}", response_model=DetectionRecordResponse)
def update_detection_license_plate(
    detection_id: int,
    payload: DetectionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DetectionRecordResponse:
    detection = (
        db.query(Detection)
        .filter(Detection.id == detection_id, Detection.user_id == current_user.id)
        .first()
    )

    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection record not found",
        )

    next_plate = (payload.license_plate or "").strip()
    detection.license_plate = next_plate or None

    db.add(detection)
    db.commit()
    db.refresh(detection)

    return DetectionRecordResponse(
        detection=detection,
        image_url=f"/{detection.image_path.replace(os.sep, '/')}",
        media_type=detection.media_type,
    )


@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_detection_record(
    detection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    detection = (
        db.query(Detection)
        .filter(Detection.id == detection_id, Detection.user_id == current_user.id)
        .first()
    )

    if detection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection record not found",
        )

    absolute_media_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        detection.image_path,
    )

    db.delete(detection)
    db.commit()

    if os.path.exists(absolute_media_path):
        os.remove(absolute_media_path)