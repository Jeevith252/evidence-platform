# routes/image_analysis.py
# API endpoint for uploading and analyzing images

from fastapi import APIRouter, UploadFile, File, HTTPException
from services.image_service import extract_metadata
import shutil
import os

router = APIRouter(
    prefix="/api/image",
    tags=["Image Analysis"]
)

# Create temp folder for uploaded images
os.makedirs("temp_images", exist_ok=True)


# POST /api/image/analyze
# Upload an image and extract its metadata
@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Upload any image and get back:
    - GPS coordinates (if available)
    - Device info (phone/camera model)
    - Date and time taken
    - Software used
    - Full EXIF data
    """

    # Check it's an image file
    allowed = ["image/jpeg", "image/jpg", "image/png",
               "image/tiff", "image/heic"]

    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File must be an image. Got: {file.content_type}"
        )

    # Save uploaded file temporarily
    temp_path = f"temp_images/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Extract metadata
        metadata = extract_metadata(temp_path)

        return {
            "success": True,
            "filename": file.filename,
            "metadata": metadata,
            "investigation_notes": get_investigation_notes(metadata)
        }

    finally:
        # Delete temp file after analysis
        if os.path.exists(temp_path):
            os.remove(temp_path)


def get_investigation_notes(metadata: dict) -> list:
    """
    Generates investigation notes based on what was found
    """
    notes = []
    summary = metadata.get("summary", {})

    if summary.get("has_gps"):
        notes.append(
            "IMPORTANT: GPS data found! "
            "This image contains location information. "
            "Check the Google Maps URL to see exactly where it was taken."
        )

    if summary.get("has_device_info"):
        device = metadata.get("device", {})
        notes.append(
            f"Device identified: {device.get('brand', '')} "
            f"{device.get('model', '')}. "
            "This can help identify the type of device used."
        )

    if summary.get("has_timestamp"):
        notes.append(
            f"Timestamp found: {metadata.get('datetime')}. "
            "This establishes when the image was created."
        )

    if not summary.get("has_gps"):
        notes.append(
            "No GPS data found. The image may have been "
            "shared through a platform that strips metadata "
            "(WhatsApp, Instagram, Twitter)."
        )

    if not notes:
        notes.append(
            "No significant metadata found. "
            "The image metadata may have been completely stripped."
        )

    return notes