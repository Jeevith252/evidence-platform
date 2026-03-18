# models/evidence.py
# This defines the STRUCTURE of evidence we save to database
# Think of this like designing the columns of a spreadsheet

from datetime import datetime

def create_evidence_document(
    text: str,
    username: str,
    sentiment: dict,
    entities: list,
    risk: dict,
    source: str = "manual"
) -> dict:
    """
    Creates a structured evidence document ready to save to MongoDB
    """
    return {
        "source": source,
        "content_type": "text",
        "raw_text": text,
        "author_username": username,
        "timestamp": datetime.utcnow(),
        "sentiment": {
            "label": sentiment.get("label"),
            "score": sentiment.get("score"),
            "interpretation": sentiment.get("interpretation")
        },
        "entities": entities,
        "risk": {
            "score": risk.get("score"),
            "risk_level": risk.get("risk_level"),
            "risk_color": risk.get("risk_color"),
            "reasons": risk.get("reasons"),
            "keywords_found": risk.get("keywords_found")
        },
        "flagged": risk.get("score", 0) >= 50,
        "created_at": datetime.utcnow()
    }
