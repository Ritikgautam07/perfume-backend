from supabase import create_client, Client
from app.config import settings


def _build_client() -> Client | None:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        # Allows the app to import/boot even before .env is filled in (e.g. for local docs preview)
        return None
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


supabase: Client = _build_client()
