import hmac
import hashlib
import razorpay
from app.config import settings

_client: razorpay.Client | None = None


def get_client() -> razorpay.Client:
    global _client
    if _client is None:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise RuntimeError("Razorpay credentials are not configured in .env")
        _client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    return _client


def create_razorpay_order(amount_inr: float, receipt: str) -> dict:
    client = get_client()
    amount_paise = int(round(amount_inr * 100))
    return client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        }
    )


def verify_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Used by the /orders/verify endpoint right after Razorpay Checkout succeeds on the frontend."""
    body = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated_signature, razorpay_signature)
