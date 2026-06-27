from fastapi import APIRouter, HTTPException
from typing import Optional
from app.database import supabase
from app.models.schemas import ProductOut, ProductCreate

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductOut])
def list_products(
    category_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    trending: Optional[bool] = None,
    ai_recommended: Optional[bool] = None,
    search: Optional[str] = None,
):
    query = supabase.table("products").select("*")
    if category_id:
        query = query.eq("category_id", category_id)
    if min_price is not None:
        query = query.gte("price", min_price)
    if max_price is not None:
        query = query.lte("price", max_price)
    if trending is not None:
        query = query.eq("is_trending", trending)
    if ai_recommended is not None:
        query = query.eq("is_ai_recommended", ai_recommended)
    if search:
        query = query.ilike("name", f"%{search}%")

    res = query.order("created_at", desc=True).execute()
    return res.data


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: str):
    res = supabase.table("products").select("*").eq("id", product_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return res.data


@router.post("/", response_model=ProductOut)
def create_product(payload: ProductCreate):
    """Admin endpoint — wire this behind an admin-only auth check before going live."""
    res = supabase.table("products").insert(payload.model_dump()).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Could not create product")
    return res.data[0]


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: str, payload: ProductCreate):
    res = supabase.table("products").update(payload.model_dump()).eq("id", product_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return res.data[0]


@router.delete("/{product_id}")
def delete_product(product_id: str):
    supabase.table("products").delete().eq("id", product_id).execute()
    return {"success": True}
