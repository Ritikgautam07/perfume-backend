from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import categories, products, scent_finder, pack_builder, discounts, orders, loyalty, payments

app = FastAPI(title="Perfume AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(scent_finder.router)
app.include_router(pack_builder.router)
app.include_router(discounts.router)
app.include_router(orders.router)
app.include_router(loyalty.router)
app.include_router(payments.router)


@app.get("/")
def health_check():
    return {"status": "online", "service": "Perfume AI Backend"}
