from fastapi import Header, HTTPException, status
from app.core.config import settings

def require_ai_key(x_ai_key: str | None = Header(default=None, alias="X-AI-KEY")) -> None:
    if not x_ai_key or x_ai_key != settings.AI_ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid AI key")
