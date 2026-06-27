import uuid
from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from app.models.schemas import OrderCreateRequest, OrderVerifyRequest
from app.utils.security import get_current_user
from app.services.razorpay_service import create_razorpay_order, verify_signature
from app.config import settings

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/")
def create_order(payload: OrderCreateRequest, user_id: str = Depends(get_current_user)):
    """
    Builds the order, applies a discount code and/or loyalty points, creates a matching
    Razorpay order, and returns everything the frontend needs to open Razorpay Checkout.
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    product_ids = [item.product_id for item in payload.items]
    products = supabase.table("products").select("*").in_("id", product_ids).execute().data
    product_map = {p["id"]: p for p in products}
    if len(product_map) != len(set(product_ids)):
        raise HTTPException(status_code=404, detail="One or more products not found")

    line_items = []
    subtotal = 0.0
    for item in payload.items:
        product = product_map[item.product_id]
        line_total = product["price"] * item.quantity
        subtotal += line_total
        line_items.append(
            {
                "product_id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": item.quantity,
                "line_total": line_total,
            }
        )

    # --- Discount code ---
    discount_amount = 0.0
    applied_code = None
    prior_orders = supabase.table("orders").select("id").eq("user_id", user_id).eq("status", "paid").limit(1).execute().data

    if payload.discount_code:
        rows = (
            supabase.table("discount_codes")
            .select("*")
            .eq("code", payload.discount_code.upper())
            .eq("active", True)
            .execute()
            .data
        )
        if not rows:
            raise HTTPException(status_code=400, detail="Invalid discount code")
        code_row = rows[0]
        if code_row.get("first_order_only") and prior_orders:
            raise HTTPException(status_code=400, detail="This code is valid only on your first order")

        discount_amount += subtotal * (code_row.get("percent_off", 0) / 100)
        discount_amount += code_row.get("flat_off", 0)
        applied_code = code_row["code"]

    # --- Loyalty points redemption ---
    loyalty_discount = 0.0
    if payload.loyalty_points_to_redeem > 0:
        profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute().data
        available_points = profile.get("loyalty_points", 0) if profile else 0
        if payload.loyalty_points_to_redeem > available_points:
            raise HTTPException(status_code=400, detail="Not enough loyalty points")
        loyalty_discount = payload.loyalty_points_to_redeem * settings.LOYALTY_POINT_VALUE_INR

    total_discount = discount_amount + loyalty_discount
    total = max(subtotal - total_discount, 0)

    order_row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "items": line_items,
        "subtotal": subtotal,
        "discount_code": applied_code,
        "discount_amount": total_discount,
        "total": total,
        "status": "created",
    }
    supabase.table("orders").insert(order_row).execute()

    razorpay_order = create_razorpay_order(amount_inr=total, receipt=order_row["id"])

    return {
        "order_id": order_row["id"],
        "subtotal": subtotal,
        "discount_amount": total_discount,
        "total": total,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount_paise": razorpay_order["amount"],
        "currency": "INR",
    }


@router.post("/verify")
def verify_order(payload: OrderVerifyRequest, user_id: str = Depends(get_current_user)):
    """Call this right after Razorpay Checkout's success callback fires on the frontend."""
    order = supabase.table("orders").select("*").eq("id", payload.order_id).single().execute().data
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your order")

    if not verify_signature(payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature):
        supabase.table("orders").update({"status": "failed"}).eq("id", order["id"]).execute()
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    points_earned = int(order["total"] * settings.LOYALTY_POINTS_PER_RUPEE)

    supabase.table("orders").update(
        {
            "status": "paid",
            "razorpay_order_id": payload.razorpay_order_id,
            "razorpay_payment_id": payload.razorpay_payment_id,
            "loyalty_points_earned": points_earned,
        }
    ).eq("id", order["id"]).execute()

    profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute().data
    current_points = profile.get("loyalty_points", 0) if profile else 0
    supabase.table("profiles").update(
        {"loyalty_points": current_points + points_earned, "has_used_first_order_discount": True}
    ).eq("id", user_id).execute()

    supabase.table("loyalty_transactions").insert(
        {"user_id": user_id, "points": points_earned, "type": "earn", "order_id": order["id"]}
    ).execute()

    return {"success": True, "status": "paid", "loyalty_points_earned": points_earned}


@router.get("/{order_id}")
def get_order(order_id: str, user_id: str = Depends(get_current_user)):
    order = supabase.table("orders").select("*").eq("id", order_id).single().execute().data
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your order")
    return order


@router.get("/")
def list_my_orders(user_id: str = Depends(get_current_user)):
    res = supabase.table("orders").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data
