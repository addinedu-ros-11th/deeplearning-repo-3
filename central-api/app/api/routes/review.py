from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import Review, ReviewStatus
from app.schemas.review import ReviewOut, ReviewUpdate

router = APIRouter(dependencies=[Depends(require_admin_key)])

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(status: ReviewStatus | None = ReviewStatus.OPEN, db: Session = Depends(get_db)):
    q = db.query(Review)
    if status:
        q = q.filter(Review.status == status)
    return q.order_by(Review.created_at.desc()).all()

@router.get("/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.review_id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="review not found")
    return r

@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, body: ReviewUpdate, db: Session = Depends(get_db)):
    r = db.query(Review).filter(Review.review_id == review_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="review not found")

    if r.status == ReviewStatus.RESOLVED and body.status == ReviewStatus.OPEN:
        raise HTTPException(status_code=400, detail="cannot reopen resolved review")

    r.status = body.status
    if body.status == ReviewStatus.RESOLVED:
        r.resolved_at = utcnow()
        r.resolved_by = body.resolved_by
        r.confirmed_items_json = body.confirmed_items_json

    db.commit()
    db.refresh(r)
    return r
