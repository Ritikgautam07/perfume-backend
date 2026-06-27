from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

Mood = Literal["powerful", "romantic", "fresh", "luxury", "daily_wear"]


# ---------- Categories ----------
class CategoryBase(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    price_min: float
    price_max: float
    description: Optional[str] = None


class CategoryOut(CategoryBase):
    id: str
    created_at: Optional[datetime] = None


# ---------- Products ----------
class ProductBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    category_id: str
    mood_tags: List[Mood] = []
    luxury_score: int = Field(ge=0, le=100, default=50)
    freshness_score: int = Field(ge=0, le=100, default=50)
    longevity_hours: int = Field(ge=0, default=6)
    image_url: Optional[str] = None
    stock: int = 100
    is_trending: bool = False
    is_ai_recommended: bool = False


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: str
    created_at: Optional[datetime] = None


# ---------- AI Scent Finder ----------
class ScentFinderRequest(BaseModel):
    moods: List[Mood]
    limit: int = 4


class ChatbotRequest(BaseModel):
    message: str


# ---------- Pack Builder ----------
class PackBuilderRequest(BaseModel):
    product_ids: List[str]


class PackTierOut(BaseModel):
    id: str
    name: str
    num_items: int
    flat_price: float
    description: Optional[str] = None


# ---------- Orders ----------
class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, default=1)


class OrderCreateRequest(BaseModel):
    items: List[OrderItem]
    discount_code: Optional[str] = None
    loyalty_points_to_redeem: int = 0


class OrderVerifyRequest(BaseModel):
    order_id: str  # our internal order id
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ---------- Discounts ----------
class DiscountValidateRequest(BaseModel):
    code: str


# ---------- Loyalty ----------
class LoyaltyRedeemRequest(BaseModel):
    points: int = Field(gt=0)
