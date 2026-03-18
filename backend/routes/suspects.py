# routes/suspects.py
# Handles suspect profiles with photo uploads

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from database.mongo import database
from datetime import datetime
import shutil
import os

router = APIRouter(
    prefix="/api/suspects",
    tags=["Suspects"]
)

# Create folder to store uploaded photos
os.makedirs("suspect_photos", exist_ok=True)

suspects_collection = database["suspects"]

# POST /api/suspects/add
# Add a new suspect with photo
@router.post("/add")
async def add_suspect(
    name: str = Form(...),
    username: str = Form(...),
    platform: str = Form(...),
    notes: str = Form(""),
    photo: UploadFile = File(None)
):
    photo_filename = None

    # Save uploaded photo if provided
    if photo and photo.filename:
        # Make filename safe
        ext = photo.filename.split(".")[-1]
        safe_name = f"{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        photo_path = f"suspect_photos/{safe_name}"

        # Save file to disk
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        photo_filename = safe_name

    # Create suspect document
    suspect = {
        "name": name,
        "username": username,
        "platform": platform,
        "notes": notes,
        "photo_filename": photo_filename,
        "photo_url": f"/api/suspects/photo/{photo_filename}" if photo_filename else None,
        "created_at": datetime.utcnow()
    }

    result = await suspects_collection.insert_one(suspect)

    return {
        "success": True,
        "message": f"Suspect {name} added successfully!",
        "suspect_id": str(result.inserted_id),
        "photo_url": suspect["photo_url"]
    }


# GET /api/suspects/all
# Get all suspects
@router.get("/all")
async def get_all_suspects():
    suspects = []
    async for suspect in suspects_collection.find().sort("created_at", -1):
        suspect["_id"] = str(suspect["_id"])
        suspects.append(suspect)
    return {"success": True, "suspects": suspects}


# GET /api/suspects/photo/{filename}
# Serve a suspect photo
@router.get("/photo/{filename}")
async def get_photo(filename: str):
    from fastapi.responses import FileResponse
    path = f"suspect_photos/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(path)