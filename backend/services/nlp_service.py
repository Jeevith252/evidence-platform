# services/nlp_service.py
# This is the AI brain of our platform
# It analyzes text and extracts useful information

from transformers import pipeline
import re

print("Loading AI models... please wait...")

# Sentiment Analysis Model
# This tells us if text is POSITIVE, NEGATIVE, or NEUTRAL
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
)

# Named Entity Recognition Model
# This finds NAMES, PLACES, ORGANIZATIONS in text
ner_analyzer = pipeline(
    "ner",
    model="dbmdz/bert-large-cased-finetuned-conll03-english",
    aggregation_strategy="simple"
)

print("AI models loaded successfully!")


def analyze_sentiment(text: str) -> dict:
    """
    Analyzes the sentiment of given text.
    Returns: positive, negative, or neutral with a confidence score
    """
    try:
        # Trim text to 512 characters (model limit)
        text = text[:512]
        result = sentiment_analyzer(text)[0]

        return {
            "label": result["label"].lower(),
            "score": round(result["score"], 4),
            "interpretation": get_sentiment_interpretation(result["label"])
        }
    except Exception as e:
        return {"label": "unknown", "score": 0, "error": str(e)}


def extract_entities(text: str) -> list:
    """
    Finds named entities in text.
    Example: 'Barack Obama visited Paris' 
    Returns: [{entity: 'Barack Obama', type: 'PERSON'}, {entity: 'Paris', type: 'LOCATION'}]
    """
    try:
        text = text[:512]
        results = ner_analyzer(text)
        entities = []

        for entity in results:
            entities.append({
                "text": entity["word"],
                "type": entity["entity_group"],
                "confidence": round(entity["score"], 4)
            })

        return entities
    except Exception as e:
        return [{"error": str(e)}]


def get_sentiment_interpretation(label: str) -> str:
    """
    Converts raw label to human readable interpretation
    """
    interpretations = {
        "positive": "This text appears supportive or friendly",
        "negative": "This text appears hostile or threatening",
        "neutral": "This text appears factual or neutral",
        "label_0": "This text appears negative",
        "label_1": "This text appears neutral",
        "label_2": "This text appears positive"
    }
    return interpretations.get(label.lower(), "Unable to interpret sentiment")


def analyze_text_full(text: str) -> dict:
    """
    Runs BOTH sentiment analysis AND entity extraction
    Returns everything combined in one result
    """
    sentiment = analyze_sentiment(text)
    entities = extract_entities(text)

    return {
        "original_text": text,
        "sentiment": sentiment,
        "entities": entities,
        "word_count": len(text.split()),
        "character_count": len(text)
    }