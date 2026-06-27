from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from app.models.schemas import LoyaltyRedeemRequest
from app.utils.security import get_current_user
from app.config import settings

router = APIRouter(prefix="/loyalty", tags=["Loyalty"])


@router.get("/")
def get_loyalty_balance(user_id: str = Depends(get_current_user)):
    profile = supabase.table("profiles").select("loyalty_points").eq("id", user_id).single().execute().data
    transactions = (
        supabase.table("loyalty_transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    return {
        "points_balance": profile.get("loyalty_points", 0) if profile else 0,
        "point_value_inr": settings.LOYALTY_POINT_VALUE_INR,
        "transactions": transactions,
    }


@router.post("/redeem-preview")
def preview_redeem(payload: LoyaltyRedeemRequest, user_id: str = Depends(get_current_user)):
    """Lets the frontend show 'Redeem 200 points -> ₹200 off' before checkout. Actual redemption
    happens inside POST /orders via loyalty_points_to_redeem."""
    profile = supabase.table("profiles").select("loyalty_points").eq("id", user_id).single().execute().data
    available = profile.get("loyalty_points", 0) if profile else 0
    if payload.points > available:
        raise HTTPException(status_code=400, detail="Not enough loyalty points")
    return {"points_to_redeem": payload.points, "discount_value_inr": payload.points * settings.LOYALTY_POINT_VALUE_INR}
