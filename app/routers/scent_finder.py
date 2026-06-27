from fastapi import APIRouter
from app.models.schemas import ScentFinderRequest, ChatbotRequest
from app.services.recommendation import recommend_products, extract_moods_from_text

router = APIRouter(prefix="/scent-finder", tags=["AI Scent Finder"])


@router.post("/")
def scent_finder(payload: ScentFinderRequest):
    """
    Powers the 'How do you want to feel?' quiz.
    e.g. moods=["fresh", "luxury"] -> recommendation_headline: "Ocean Mist + Silver Noir"
    """
    return recommend_products(payload.moods, payload.limit)


@router.post("/chatbot")
def chatbot_find_my_scent(payload: ChatbotRequest):
    """Backs the 'Find my scent' chatbot widget — takes free text instead of quiz buttons."""
    moods = extract_moods_from_text(payload.message)
    result = recommend_products(moods, limit=4)
    result["interpreted_moods"] = moods
    return result
