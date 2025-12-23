from fastapi import APIRouter
from app.api.routes import menu, tray, review, order, cctv, dashboard, store, device, prototype, inference

api_router = APIRouter()
api_router.include_router(store.router, tags=["store"])
api_router.include_router(device.router, tags=["device"])
api_router.include_router(menu.router, tags=["menu"])
api_router.include_router(tray.router, tags=["tray"])
api_router.include_router(review.router, tags=["review"])
api_router.include_router(order.router, tags=["order"])
api_router.include_router(cctv.router, tags=["cctv"])
api_router.include_router(dashboard.router, tags=["dashboard"])

api_router.include_router(prototype.router, tags=["prototype"])
api_router.include_router(inference.router, tags=["inference"])