from fastapi import APIRouter, UploadFile, File
import numpy as np
import cv2
from app.services.pipeline import process_image

router = APIRouter()

@router.post("/")
async def detect(file: UploadFile = File(...)):
    contents = await file.read()
    
    # convert to OpenCV format
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = process_image(image)

    return result