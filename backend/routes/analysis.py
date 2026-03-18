# routes/analysis.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.nlp_service import analyze_text_full
from services.risk_engine import calculate_risk_score

router = APIRouter(
    prefix="/api/analyze",
    tags=["Analysis"]
)

class TextInput(BaseModel):
    text: str
    username: str = "unknown"

@router.post("/text")
async def analyze_text(input: TextInput):
    if not input.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if len(input.text) < 3:
        raise HTTPException(status_code=400, detail="Text too short to analyze")

    # Step 1: Run AI analysis
    result = analyze_text_full(input.text)

    # Step 2: Calculate risk score using AI results
    risk = calculate_risk_score(
        text=input.text,
        sentiment_label=result["sentiment"]["label"],
        sentiment_score=result["sentiment"]["score"],
        entities=result["entities"]
    )

    # Step 3: Combine everything
    result["username"] = input.username
    result["risk"] = risk

    return {
        "success": True,
        "data": result
    }

@router.get("/test")
async def test_route():
    return {"message": "Analysis route is working!"}