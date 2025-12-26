# from datetime import datetime, timezone
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.api.deps import get_db
# from app.core.security import require_admin_key
# from app.db.models import PrototypeSet, PrototypeSetStatus, MenuItem, MenuItemPrototype
# from app.schemas.prototype import (
#     PrototypeSetCreate, PrototypeSetOut,
#     MenuItemPrototypeCreate, MenuItemPrototypeOut,
#     ActivatePrototypeSetIn, ActivePrototypeRow
# )

# router = APIRouter(dependencies=[Depends(require_admin_key)])

# def utcnow():
#     return datetime.now(timezone.utc).replace(tzinfo=None)

# @router.get("/prototype-sets", response_model=list[PrototypeSetOut])
# def list_sets(db: Session = Depends(get_db)):
#     return db.query(PrototypeSet).order_by(PrototypeSet.prototype_set_id.desc()).all()

# @router.post("/prototype-sets", response_model=PrototypeSetOut)
# def create_set(body: PrototypeSetCreate, db: Session = Depends(get_db)):
#     s = PrototypeSet(status=PrototypeSetStatus(body.status), notes=body.notes, created_at=utcnow())
#     db.add(s)
#     db.commit()
#     db.refresh(s)
#     return s

# @router.post("/prototype-sets/activate")
# def activate_set(body: ActivatePrototypeSetIn, db: Session = Depends(get_db)):
#     target = db.query(PrototypeSet).filter(PrototypeSet.prototype_set_id == body.prototype_set_id).first()
#     if not target:
#         raise HTTPException(status_code=404, detail="prototype_set not found")

#     db.query(PrototypeSet).update({PrototypeSet.status: PrototypeSetStatus.INACTIVE})
#     target.status = PrototypeSetStatus.ACTIVE

#     db.query(MenuItemPrototype).update({MenuItemPrototype.is_active: False})
#     db.query(MenuItemPrototype).filter(MenuItemPrototype.prototype_set_id == target.prototype_set_id).update(
#         {MenuItemPrototype.is_active: True}
#     )

#     db.commit()
#     return {"ok": True, "active_prototype_set_id": target.prototype_set_id}

# @router.post("/menu-item-prototypes", response_model=list[MenuItemPrototypeOut])
# def create_prototypes(items: list[MenuItemPrototypeCreate], db: Session = Depends(get_db)):
#     out = []
#     for it in items:
#         if not db.query(MenuItem).filter(MenuItem.item_id == it.item_id).first():
#             raise HTTPException(status_code=400, detail=f"menu_item not found: {it.item_id}")
#         if not db.query(PrototypeSet).filter(PrototypeSet.prototype_set_id == it.prototype_set_id).first():
#             raise HTTPException(status_code=400, detail=f"prototype_set not found: {it.prototype_set_id}")

#         p = MenuItemPrototype(
#             item_id=it.item_id,
#             prototype_set_id=it.prototype_set_id,
#             image_gcs_uri=it.image_gcs_uri,
#             embedding_gcs_uri=it.embedding_gcs_uri,
#             is_active=bool(it.is_active),
#             created_at=utcnow(),
#         )
#         db.add(p)
#         out.append(p)

#     db.commit()
#     for p in out:
#         db.refresh(p)
#     return out

# @router.get("/prototypes/active", response_model=list[ActivePrototypeRow])
# def list_active_prototypes(db: Session = Depends(get_db)):
#     active_set = db.query(PrototypeSet).filter(PrototypeSet.status == PrototypeSetStatus.ACTIVE).first()
#     if not active_set:
#         return []
#     rows = (
#         db.query(MenuItemPrototype.item_id, MenuItemPrototype.embedding_gcs_uri)
#         .filter(MenuItemPrototype.prototype_set_id == active_set.prototype_set_id)
#         .filter(MenuItemPrototype.is_active == True)  # noqa
#         .all()
#     )
#     return [ActivePrototypeRow(item_id=r[0], embedding_gcs_uri=r[1]) for r in rows]
