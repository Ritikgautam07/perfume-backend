from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.models.schemas import CategoryOut, CategoryBase

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[CategoryOut])
def list_categories():
    """Powers the 'Smart Categories' section: Daily, Premium, Combo, Trending, AI Recommended."""
    res = supabase.table("categories").select("*").order("price_min").execute()
    return res.data


@router.post("/", response_model=CategoryOut)
def create_category(payload: CategoryBase):
    res = supabase.table("categories").insert(payload.model_dump()).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Could not create category")
    return res.data[0]
