# routes/reports.py
# API endpoints for generating PDF reports

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.pdf_service import generate_report
from database.mongo import evidence_collection
import os

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"]
)

class ReportInput(BaseModel):
    title: str = "Social Media Investigation Report"
    investigator: str = "System Analyst"
    include_flagged_only: bool = False

# POST /api/reports/generate
# Generate a PDF report from all saved evidence
@router.post("/generate")
async def create_report(input: ReportInput):
    """
    Fetches evidence from database and generates a PDF report
    """
    # Fetch evidence from database
    evidence_list = []
    query = {"flagged": True} if input.include_flagged_only else {}

    async for evidence in evidence_collection.find(query).sort("created_at", -1):
        evidence["_id"] = str(evidence["_id"])
        evidence_list.append(evidence)

    if not evidence_list:
        raise HTTPException(
            status_code=404,
            detail="No evidence found in database. Submit some evidence first!"
        )

    # Generate PDF
    pdf_path = generate_report(
        title=input.title,
        evidence_list=evidence_list,
        investigator=input.investigator
    )

    return {
        "success": True,
        "message": "Report generated successfully!",
        "pdf_path": pdf_path,
        "evidence_count": len(evidence_list),
        "download_url": f"/api/reports/download/{os.path.basename(pdf_path)}"
    }


# GET /api/reports/download/{filename}
# Download a generated PDF report
@router.get("/download/{filename}")
async def download_report(filename: str):
    """
    Downloads a generated PDF report
    """
    file_path = f"reports/{filename}"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )