from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")

router = APIRouter()

# Enable CORS for frontend


@router.get("/get-card-image")
def get_card_image(type: str = Query(...)):
    type = type.lower()
    for filename in os.listdir(UPLOAD_FOLDER):
        if type in filename.lower():
            return JSONResponse(content={"image_url": f"http://localhost:8000/show-image/{filename}"})
    return JSONResponse(content={"image_url": None})


@router.get("/show-image/{filename}")
def show_image(filename: str):
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    return JSONResponse(content={"error": "File not found"}, status_code=404)
