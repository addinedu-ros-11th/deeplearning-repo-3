from fastapi import Header, HTTPException, status
from app.core.config import settings

def require_admin_key(x_admin_key: str = Header(default="", alias="X-ADMIN-KEY")) -> None:
    if not x_admin_key or x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )
