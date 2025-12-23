from datetime import datetime
from typing import Any
from app.schemas.common import ORMBase
from app.db.models import DeviceType, DeviceStatus

class DeviceOut(ORMBase):
    device_id: int
    store_id: int
    device_code: str
    device_type: DeviceType
    status: DeviceStatus
    stream_uri: str | None = None
    config_json: Any | None = None
    created_at: datetime
