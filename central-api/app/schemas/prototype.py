from datetime import datetime
from pydantic import BaseModel, Field

class PrototypeSetCreate(BaseModel):
    status: str = Field(..., description="ACTIVE/INACTIVE")
    notes: str | None = None

class PrototypeSetOut(BaseModel):
    prototype_set_id: int
    status: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class MenuItemPrototypeCreate(BaseModel):
    item_id: int
    prototype_set_id: int
    image_gcs_uri: str
    embedding_gcs_uri: str
    is_active: bool = True

class MenuItemPrototypeOut(BaseModel):
    prototype_id: int
    item_id: int
    prototype_set_id: int
    image_gcs_uri: str
    embedding_gcs_uri: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ActivatePrototypeSetIn(BaseModel):
    prototype_set_id: int

class ActivePrototypeRow(BaseModel):
    item_id: int
    embedding_gcs_uri: str
