import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Loyalty program: how many points are earned per ₹1 spent, and what each point is worth at redemption
    LOYALTY_POINTS_PER_RUPEE: float = float(os.getenv("LOYALTY_POINTS_PER_RUPEE", "0.05"))  # 5 pts per ₹100
    LOYALTY_POINT_VALUE_INR: float = float(os.getenv("LOYALTY_POINT_VALUE_INR", "1"))  # 1 point = ₹1


settings = Settings()
