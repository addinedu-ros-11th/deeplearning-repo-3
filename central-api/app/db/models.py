import enum
from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime, Boolean, ForeignKey,
    Enum, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

# -----------------------
# Enums (DBML 그대로)
# -----------------------
class DeviceType(str, enum.Enum):
    CHECKOUT = "CHECKOUT"
    CCTV = "CCTV"

class DeviceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class TraySessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"

class DecisionState(str, enum.Enum):
    AUTO = "AUTO"
    REVIEW = "REVIEW"
    UNKNOWN = "UNKNOWN"

class ReviewStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"

class OrderStatus(str, enum.Enum):
    PAID = "PAID"
    FAILED = "FAILED"

class PrototypeSetStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class CctvEventType(str, enum.Enum):
    VANDALISM = "VANDALISM"
    VIOLENCE = "VIOLENCE"
    FALL = "FALL"
    WHEELCHAIR = "WHEELCHAIR"

class CctvEventStatus(str, enum.Enum):
    OPEN = "OPEN"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"

# -----------------------
# Inference Job
# -----------------------
class InferenceJobType(str, enum.Enum):
    TRAY = "TRAY"
    CCTV = "CCTV"

class InferenceJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    DONE = "DONE"
    FAILED = "FAILED"

# -----------------------
# Master
# -----------------------
class Store(Base):
    __tablename__ = "store"

    store_id = Column(Integer, primary_key=True, autoincrement=True)
    store_code = Column(String(32), nullable=False, unique=True)
    name = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False)

    devices = relationship("Device", back_populates="store")
    tray_sessions = relationship("TraySession", back_populates="store")
    orders = relationship("OrderHdr", back_populates="store")
    cctv_events = relationship("CctvEvent", back_populates="store")

class Device(Base):
    __tablename__ = "device"

    device_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("store.store_id"), nullable=False)
    device_code = Column(String(32), nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    status = Column(Enum(DeviceStatus), nullable=False)
    stream_uri = Column(String(512))
    config_json = Column(JSON)
    created_at = Column(DateTime, nullable=False)

    store = relationship("Store", back_populates="devices")

    __table_args__ = (
        UniqueConstraint("store_id", "device_code", name="uq_device_store_code"),
        Index("ix_device_store_type", "store_id", "device_type"),
    )

class MenuItem(Base):
    __tablename__ = "menu_item"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    name_eng = Column(String(128), nullable=False)
    name_kor = Column(String(128), nullable=False)
    category_id = Column(Integer, ForeignKey('category.category_id'))
    price_won = Column(Integer, nullable=False)
    weight_grams = Column(Integer)
    active = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)

    prototypes = relationship("MenuItemPrototype", back_populates="menu_item")
    order_lines = relationship("OrderLine", back_populates="menu_item")

    category = relationship("Category", back_populates="menu_items")
    __table_args__ = (
        Index("ix_menu_item_active_category_id", "active", "category_id"),
    )

class Category(Base):
    __tablename__ = 'category'
    
    category_id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, nullable=False)
    
    menu_items = relationship("MenuItem", back_populates="category")

class PrototypeSet(Base):
    __tablename__ = "prototype_set"

    prototype_set_id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(PrototypeSetStatus), nullable=False)  # ACTIVE/INACTIVE
    notes = Column(String(256))
    created_at = Column(DateTime, nullable=False)

    # ✅ 통합 인덱스(25개 전체) 아티팩트 위치
    index_npy_gcs_uri = Column(String(512), nullable=False)
    index_meta_gcs_uri = Column(String(512), nullable=False)

# -----------------------
# Tray / Checkout
# -----------------------
class TraySession(Base):
    __tablename__ = "tray_session"

    session_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_uuid = Column(String(36), nullable=False, unique=True)
    store_id = Column(Integer, ForeignKey("store.store_id"), nullable=False)
    checkout_device_id = Column(Integer, ForeignKey("device.device_id"), nullable=False)
    status = Column(Enum(TraySessionStatus), nullable=False)
    attempt_limit = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    end_reason = Column(String(64))
    created_at = Column(DateTime, nullable=False)

    store = relationship("Store", back_populates="tray_sessions")
    runs = relationship("RecognitionRun", back_populates="tray_session")
    reviews = relationship("Review", back_populates="tray_session")
    order = relationship("OrderHdr", back_populates="tray_session", uselist=False)

    __table_args__ = (
        Index("ix_tray_session_checkout_started", "checkout_device_id", "started_at"),
        Index("ix_tray_session_store_status_started", "store_id", "status", "started_at"),
    )

class RecognitionRun(Base):
    __tablename__ = "recognition_run"

    run_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("tray_session.session_id"), nullable=False)
    attempt_no = Column(Integer, nullable=False)
    overlap_score = Column(Numeric(8, 6))
    decision = Column(Enum(DecisionState), nullable=False)
    result_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)

    tray_session = relationship("TraySession", back_populates="runs")
    reviews = relationship("Review", back_populates="recognition_run")

    __table_args__ = (
        UniqueConstraint("session_id", "attempt_no", name="uq_run_session_attempt"),
        Index("ix_run_session_created", "session_id", "created_at"),
    )

class InferenceJob(Base):
    __tablename__ = "inference_job"

    job_id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_type = Column(Enum(InferenceJobType), nullable=False)
    status = Column(Enum(InferenceJobStatus), nullable=False)

    store_id = Column(Integer, ForeignKey("store.store_id"), nullable=False)
    device_id = Column(Integer, ForeignKey("device.device_id"), nullable=False)

    # TRAY job에 사용
    session_id = Column(BigInteger, ForeignKey("tray_session.session_id"))
    attempt_no = Column(Integer)  # TRAY: 1..attempt_limit
    frame_gcs_uri = Column(String(512))

    # 결과(선택): job 레벨에서도 보관
    decision = Column(Enum(DecisionState))
    run_id = Column(BigInteger, ForeignKey("recognition_run.run_id"))
    result_json = Column(JSON)
    error = Column(String(512))

    # 워커 클레임 정보
    worker_id = Column(String(64))
    created_at = Column(DateTime, nullable=False)
    claimed_at = Column(DateTime)
    completed_at = Column(DateTime)

    store = relationship("Store")
    device = relationship("Device")
    tray_session = relationship("TraySession")
    recognition_run = relationship("RecognitionRun")

    __table_args__ = (
        Index("ix_job_status_created", "status", "created_at"),
        Index("ix_job_session", "session_id"),
        Index("ix_job_store_created", "store_id", "created_at"),
    )

class Review(Base):
    __tablename__ = "review"

    review_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("tray_session.session_id"), nullable=False)
    run_id = Column(BigInteger, ForeignKey("recognition_run.run_id"))
    status = Column(Enum(ReviewStatus), nullable=False)
    reason = Column(String(64), nullable=False)
    top_k_json = Column(JSON)
    confirmed_items_json = Column(JSON)
    created_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(64))

    tray_session = relationship("TraySession", back_populates="reviews")
    recognition_run = relationship("RecognitionRun", back_populates="reviews")

    __table_args__ = (
        Index("ix_review_status_created", "status", "created_at"),
        Index("ix_review_session", "session_id"),
    )

class OrderHdr(Base):
    __tablename__ = "order_hdr"

    order_id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("store.store_id"), nullable=False)
    session_id = Column(BigInteger, ForeignKey("tray_session.session_id"), nullable=False)
    total_amount_won = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    created_at = Column(DateTime, nullable=False)

    store = relationship("Store", back_populates="orders")
    tray_session = relationship("TraySession", back_populates="order")
    lines = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("session_id", name="uq_order_session"),
        Index("ix_order_store_created", "store_id", "created_at"),
    )

class OrderLine(Base):
    __tablename__ = "order_line"

    order_line_id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("order_hdr.order_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("menu_item.item_id"), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price_won = Column(Integer, nullable=False)
    line_amount_won = Column(Integer, nullable=False)

    order = relationship("OrderHdr", back_populates="lines")
    menu_item = relationship("MenuItem", back_populates="order_lines")

    __table_args__ = (
        Index("ix_order_line_order", "order_id"),
        Index("ix_order_line_item", "item_id"),
    )

# -----------------------
# CCTV
# -----------------------
class CctvEvent(Base):
    __tablename__ = "cctv_event"

    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("store.store_id"), nullable=False)
    cctv_device_id = Column(Integer, ForeignKey("device.device_id"), nullable=False)
    event_type = Column(Enum(CctvEventType), nullable=False)
    confidence = Column(Numeric(8, 6), nullable=False)
    status = Column(Enum(CctvEventStatus), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    meta_json = Column(JSON)
    created_at = Column(DateTime, nullable=False)

    store = relationship("Store", back_populates="cctv_events")
    clips = relationship("CctvEventClip", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cctv_event_device_started", "cctv_device_id", "started_at"),
        Index("ix_cctv_event_type_status", "event_type", "status"),
    )

class CctvEventClip(Base):
    __tablename__ = "cctv_event_clip"

    clip_id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(BigInteger, ForeignKey("cctv_event.event_id"), nullable=False)
    clip_gcs_uri = Column(String(512), nullable=False)
    clip_start_at = Column(DateTime, nullable=False)
    clip_end_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)

    event = relationship("CctvEvent", back_populates="clips")

    __table_args__ = (
        Index("ix_cctv_clip_event", "event_id"),
    )
