# routes/evidence.py
# API endpoints for saving and retrieving evidence

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.nlp_service import analyze_text_full
from services.risk_engine import calculate_risk_score
from models.evidence import create_evidence_document
from database.mongo import evidence_collection
from datetime import datetime

router = APIRouter(
    prefix="/api/evidence",
    tags=["Evidence"]
)

class EvidenceInput(BaseModel):
    text: str
    username: str = "unknown"
    source: str = "manual"

# POST /api/evidence/submit
# Analyze text AND save it to database in one step
@router.post("/submit")
async def submit_evidence(input: EvidenceInput):
    """
    This endpoint does everything in one go:
    1. Analyzes the text with AI
    2. Calculates risk score
    3. Saves everything to MongoDB
    4. Returns the saved evidence with its ID
    """
    if not input.text or len(input.text) < 3:
        raise HTTPException(status_code=400, detail="Text too short")

    # Step 1: Run AI analysis
    analysis = analyze_text_full(input.text)

    # Step 2: Calculate risk
    risk = calculate_risk_score(
        text=input.text,
        sentiment_label=analysis["sentiment"]["label"],
        sentiment_score=analysis["sentiment"]["score"],
        entities=analysis["entities"]
    )

    # Step 3: Create evidence document
    evidence_doc = create_evidence_document(
        text=input.text,
        username=input.username,
        sentiment=analysis["sentiment"],
        entities=analysis["entities"],
        risk=risk,
        source=input.source
    )

    # Step 4: Save to MongoDB
    result = await evidence_collection.insert_one(evidence_doc)

    return {
        "success": True,
        "message": "Evidence saved successfully!",
        "evidence_id": str(result.inserted_id),
        "risk_level": risk["risk_level"],
        "risk_score": risk["score"],
        "flagged": evidence_doc["flagged"]
    }


# GET /api/evidence/all
# Get all saved evidence from database
@router.get("/all")
async def get_all_evidence():
    """
    Retrieves all saved evidence from MongoDB
    """
    evidence_list = []

    # Loop through all documents in database
    async for evidence in evidence_collection.find().sort("created_at", -1):
        evidence["_id"] = str(evidence["_id"])  # Convert ID to string
        evidence_list.append(evidence)

    return {
        "success": True,
        "count": len(evidence_list),
        "evidence": evidence_list
    }


# GET /api/evidence/flagged
# Get only HIGH and CRITICAL risk evidence
@router.get("/flagged")
async def get_flagged_evidence():
    """
    Returns only evidence that was flagged as high risk
    """
    flagged_list = []

    async for evidence in evidence_collection.find(
        {"flagged": True}
    ).sort("risk.score", -1):
        evidence["_id"] = str(evidence["_id"])
        flagged_list.append(evidence)

    return {
        "success": True,
        "count": len(flagged_list),
        "flagged_evidence": flagged_list
    }