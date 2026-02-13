"""
FastAPI 의존성 주입 모듈.
데이터베이스 세션 및 공통 의존성을 제공합니다.
"""
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Store


def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션을 생성하고 반환합니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_store_by_code(
    store_code: Annotated[str, Query(description="매장 코드 식별자")],
    db: Session = Depends(get_db),
) -> Store:
    """
    store_code로 매장을 조회하는 의존성.
    매장을 찾을 수 없으면 404 에러를 발생시킵니다.
    """
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")
    return store


# 쉬운 사용을 위한 타입 별칭
StoreDep = Annotated[Store, Depends(get_store_by_code)]
