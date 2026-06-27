import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.database import supabase

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """
    Configure this URL in your Razorpay Dashboard (Settings -> Webhooks) so order status
    stays correct even if the user closes the browser before /orders/verify gets called.
    """
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")

    if event == "payment.captured":
        razorpay_order_id = payload["payload"]["payment"]["entity"]["order_id"]
        supabase.table("orders").update({"status": "paid"}).eq("razorpay_order_id", razorpay_order_id).execute()
    elif event == "payment.failed":
        razorpay_order_id = payload["payload"]["payment"]["entity"]["order_id"]
        supabase.table("orders").update({"status": "failed"}).eq("razorpay_order_id", razorpay_order_id).execute()

    return {"status": "ok"}
