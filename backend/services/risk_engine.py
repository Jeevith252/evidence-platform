# services/risk_engine.py
# This is the RISK SCORING ENGINE
# It takes AI analysis results and calculates a threat score 0-100

# These are words that increase the risk score
# The more of these found in text, the higher the score
THREAT_KEYWORDS = [
    "kill", "destroy", "attack", "bomb", "weapon", "threat",
    "hurt", "harm", "violence", "murder", "shoot", "explode",
    "hack", "steal", "fraud", "scam", "illegal", "criminal",
    "terrorist", "extremist", "revenge", "punish", "eliminate"
]

SUSPICIOUS_KEYWORDS = [
    "secret", "hidden", "anonymous", "untraceable", "encrypted",
    "dark web", "fake", "identity", "infiltrate", "expose",
    "leak", "classified", "corrupt", "bribe", "blackmail"
]

URGENCY_KEYWORDS = [
    "urgent", "immediately", "now", "tonight", "today",
    "deadline", "last chance", "final warning", "act now"
]


def calculate_risk_score(
    text: str,
    sentiment_label: str,
    sentiment_score: float,
    entities: list
) -> dict:
    """
    Calculates a risk score from 0 to 100 based on:
    1. Sentiment (negative = higher risk)
    2. Threat keywords found in text
    3. Suspicious keywords found in text
    4. Urgency keywords found in text
    5. Number of entities mentioned
    """

    score = 0
    reasons = []
    text_lower = text.lower()

    # --- FACTOR 1: Sentiment Score (max 40 points) ---
    if sentiment_label == "negative":
        sentiment_points = int(sentiment_score * 40)
        score += sentiment_points
        reasons.append(f"Negative sentiment detected (+{sentiment_points} points)")

    elif sentiment_label == "neutral":
        score += 5
        reasons.append("Neutral sentiment (+5 points)")

    else:  # positive
        score += 0
        reasons.append("Positive sentiment (no risk points)")

    # --- FACTOR 2: Threat Keywords (max 30 points) ---
    found_threats = []
    for keyword in THREAT_KEYWORDS:
        if keyword in text_lower:
            found_threats.append(keyword)

    if found_threats:
        threat_points = min(len(found_threats) * 10, 30)
        score += threat_points
        reasons.append(f"Threat keywords found: {', '.join(found_threats)} (+{threat_points} points)")

    # --- FACTOR 3: Suspicious Keywords (max 20 points) ---
    found_suspicious = []
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in text_lower:
            found_suspicious.append(keyword)

    if found_suspicious:
        suspicious_points = min(len(found_suspicious) * 5, 20)
        score += suspicious_points
        reasons.append(f"Suspicious keywords: {', '.join(found_suspicious)} (+{suspicious_points} points)")

    # --- FACTOR 4: Urgency Keywords (max 10 points) ---
    found_urgency = []
    for keyword in URGENCY_KEYWORDS:
        if keyword in text_lower:
            found_urgency.append(keyword)

    if found_urgency:
        urgency_points = min(len(found_urgency) * 5, 10)
        score += urgency_points
        reasons.append(f"Urgency indicators: {', '.join(found_urgency)} (+{urgency_points} points)")

    # --- Cap score at 100 ---
    score = min(score, 100)

    # --- Determine Risk Level ---
    risk_level = get_risk_level(score)

    return {
        "score": score,
        "risk_level": risk_level["level"],
        "risk_color": risk_level["color"],
        "reasons": reasons,
        "keywords_found": {
            "threats": found_threats,
            "suspicious": found_suspicious,
            "urgency": found_urgency
        }
    }


def get_risk_level(score: int) -> dict:
    """
    Converts numeric score to human readable risk level
    """
    if score <= 20:
        return {"level": "LOW", "color": "green"}
    elif score <= 50:
        return {"level": "MEDIUM", "color": "yellow"}
    elif score <= 80:
        return {"level": "HIGH", "color": "orange"}
    else:
        return {"level": "CRITICAL", "color": "red"}