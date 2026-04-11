from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.detection import Detection
from app.models.user import User
from app.services.pipeline import process_image

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
SUPPORTED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"}


def save_upload(contents: bytes, filename: str | None, user_id: int, content_type: str | None) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(filename or "")[1]
    if not extension:
        if content_type in SUPPORTED_VIDEO_TYPES:
            extension = ".mp4"
        else:
            extension = ".jpg"
    user_folder = os.path.join(UPLOAD_DIR, f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)
    stored_name = f"{uuid4().hex}{extension}"
    absolute_path = os.path.join(user_folder, stored_name)
    with open(absolute_path, "wb") as image_file:
        image_file.write(contents)
    return os.path.relpath(absolute_path, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def save_frame_image(frame: np.ndarray, user_id: int) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    user_folder = os.path.join(UPLOAD_DIR, f"user_{user_id}")
    os.makedirs(user_folder, exist_ok=True)
    stored_name = f"{uuid4().hex}.jpg"
    absolute_path = os.path.join(user_folder, stored_name)
    cv2.imwrite(absolute_path, frame)
    return os.path.relpath(absolute_path, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def process_video(video_path: str, frame_stride: int = 10, max_frames: int = 180) -> tuple[dict, np.ndarray | None]:
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return {"is_car": False}, None

    frame_index = 0

    try:
        while frame_index < max_frames:
            success, frame = capture.read()
            if not success:
                break

            if frame_index % frame_stride == 0:
                frame_result = process_image(frame)
                if frame_result.get("is_car") and frame_result.get("view") == "rear":
                    frame_result["frame_index"] = frame_index
                    return frame_result, frame

            frame_index += 1
    finally:
        capture.release()

    return {
        "is_car": False,
        "view": None,
        "license_plate": None,
        "message": "No rear car detection found in video",
    }, None


def build_detection_response(detection: Detection) -> dict:
    return {
        "id": detection.id,
        "image_url": f"/{detection.image_path.replace(os.sep, '/')}",
        "media_type": detection.media_type,
        "captured_at": detection.captured_at.isoformat(),
        "exit_date": detection.exit_date.isoformat(),
        "exit_time": detection.exit_time.isoformat(),
    }

@router.post("/")
async def detect(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in SUPPORTED_IMAGE_TYPES | SUPPORTED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image or video",
        )

    contents = await file.read()
    media_type = "video" if file.content_type in SUPPORTED_VIDEO_TYPES else "image"

    result: dict
    saved_path: str | None = None

    if media_type == "video":
        extension = os.path.splitext(file.filename or "")[1] or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_video:
            temp_video.write(contents)
            temp_video_path = temp_video.name

        try:
            result, rear_frame = process_video(temp_video_path)
        finally:
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

        if rear_frame is None:
            return {
                **result,
                "record": None,
                "media_type": "video",
            }

        saved_path = save_frame_image(rear_frame, current_user.id)
        media_type = "image"
    else:
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid image",
            )

        result = process_image(image)
        saved_path = save_upload(contents, file.filename, current_user.id, file.content_type)

    now = datetime.now(timezone.utc)

    detection = Detection(
        user_id=current_user.id,
        image_path=saved_path,
        original_filename=file.filename,
        media_type=media_type,
        is_car=bool(result.get("is_car", False)),
        view=result.get("view"),
        license_plate=result.get("license_plate"),
        exit_date=now.date(),
        exit_time=now.time().replace(microsecond=0),
        captured_at=now.replace(microsecond=0),
    )

    db.add(detection)
    db.commit()
    db.refresh(detection)

    return {
        **result,
        "record": build_detection_response(detection),
        "media_type": media_type,
    }