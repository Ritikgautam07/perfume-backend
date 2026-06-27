from typing import List
from app.database import supabase

# Lightweight keyword map used to turn free-text chatbot messages into moods.
# Swap this out for a real LLM call (Anthropic/OpenAI) later for smarter parsing —
# the rest of the recommendation pipeline stays the same either way.
MOOD_KEYWORDS = {
    "powerful": ["powerful", "bold", "strong", "intense", "dominant", "confident"],
    "romantic": ["romantic", "date", "love", "rose", "floral", "valentine", "candle"],
    "fresh": ["fresh", "ocean", "summer", "citrus", "light", "clean", "breezy"],
    "luxury": ["luxury", "premium", "expensive", "rich", "gold", "elite", "special"],
    "daily_wear": ["daily", "office", "everyday", "casual", "work", "regular"],
}


def extract_moods_from_text(message: str) -> List[str]:
    message = message.lower()
    matched = [mood for mood, keywords in MOOD_KEYWORDS.items() if any(k in message for k in keywords)]
    return matched or ["daily_wear"]


def recommend_products(moods: List[str], limit: int = 4) -> dict:
    all_products = supabase.table("products").select("*").execute().data

    scored = []
    for p in all_products:
        tags = p.get("mood_tags") or []
        overlap = len(set(tags) & set(moods))
        if overlap == 0:
            continue
        # Rank by how many requested moods it matches, then by luxury/freshness as tiebreakers
        score = overlap * 100 + p.get("luxury_score", 0) * 0.3 + p.get("freshness_score", 0) * 0.2
        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [p for _, p in scored[:limit]]

    headline = None
    if len(top) >= 2:
        headline = f"{top[0]['name']} + {top[1]['name']}"
    elif top:
        headline = top[0]["name"]

    return {
        "selected_moods": moods,
        "recommendation_headline": headline,
        "products": top,
    }
