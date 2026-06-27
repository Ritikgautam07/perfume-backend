from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from app.models.schemas import DiscountValidateRequest
from app.utils.security import get_current_user

router = APIRouter(prefix="/discounts", tags=["Discounts"])


def _has_ordered_before(user_id: str) -> bool:
    res = supabase.table("orders").select("id").eq("user_id", user_id).eq("status", "paid").limit(1).execute()
    return len(res.data) > 0


@router.get("/welcome")
def get_welcome_offer(user_id: str = Depends(get_current_user)):
    """Tells the frontend whether to show the '🎁 First order → 15% OFF' banner/wheel for this user."""
    if _has_ordered_before(user_id):
        return {"eligible": False, "message": "Welcome discount is only available on your first order."}

    code_row = supabase.table("discount_codes").select("*").eq("code", "WELCOME15").single().execute().data
    return {"eligible": True, "code": code_row["code"], "percent_off": code_row["percent_off"]}


@router.post("/validate")
def validate_discount(payload: DiscountValidateRequest, user_id: str = Depends(get_current_user)):
    rows = (
        supabase.table("discount_codes")
        .select("*")
        .eq("code", payload.code.upper())
        .eq("active", True)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Invalid or inactive discount code")

    code_row = rows[0]

    if code_row.get("max_uses") is not None and code_row["used_count"] >= code_row["max_uses"]:
        raise HTTPException(status_code=400, detail="This discount code has reached its usage limit")

    if code_row.get("first_order_only") and _has_ordered_before(user_id):
        raise HTTPException(status_code=400, detail="This code is valid only on your first order")

    return {
        "valid": True,
        "code": code_row["code"],
        "percent_off": code_row.get("percent_off", 0),
        "flat_off": code_row.get("flat_off", 0),
    }
