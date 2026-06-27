from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.models.schemas import PackBuilderRequest, PackTierOut

router = APIRouter(prefix="/pack-builder", tags=["Pack Builder"])


@router.get("/tiers", response_model=list[PackTierOut])
def list_pack_tiers():
    res = supabase.table("pack_tiers").select("*").order("num_items").execute()
    return res.data


@router.post("/calculate")
def calculate_pack(payload: PackBuilderRequest):
    """
    User picks N products (e.g. 1 Floral + 1 Fresh + 1 Luxury) and this returns the flat
    pack price if a matching tier exists (e.g. any 3 items -> ₹500), otherwise falls back
    to the sum of individual prices.
    """
    if not payload.product_ids:
        raise HTTPException(status_code=400, detail="Select at least one product")

    products = supabase.table("products").select("*").in_("id", payload.product_ids).execute().data
    if len(products) != len(payload.product_ids):
        raise HTTPException(status_code=404, detail="One or more products not found")

    individual_total = sum(p["price"] for p in products)

    tiers = supabase.table("pack_tiers").select("*").eq("num_items", len(products)).execute().data
    pack_price = tiers[0]["flat_price"] if tiers else individual_total
    savings = max(individual_total - pack_price, 0)

    return {
        "products": products,
        "individual_total": individual_total,
        "pack_price": pack_price,
        "you_save": savings,
        "matched_tier": tiers[0]["name"] if tiers else None,
    }
