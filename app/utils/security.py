import jwt
from fastapi import Header, HTTPException, status
from app.config import settings


def get_current_user(authorization: str = Header(None)) -> str:
    """
    Verifies a Supabase Auth JWT sent from the frontend and returns the user's id (the `sub` claim).

    Frontend usage:
        const { data } = await supabase.auth.getSession()
        fetch(url, { headers: { Authorization: `Bearer ${data.session.access_token}` } })
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject claim")

    return user_id


def get_current_user_optional(authorization: str = Header(None)):
    """Same as get_current_user but returns None instead of raising — useful for guest-friendly endpoints."""
    if not authorization:
        return None
    try:
        return get_current_user(authorization)
    except HTTPException:
        return None
