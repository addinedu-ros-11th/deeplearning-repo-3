from pydantic import BaseModel
from typing import Literal, Optional

class TopMenuRow(BaseModel):
    item_id: int
    name_kor: str
    name_eng: str
    qty: int
    amount_won: int


class KPIRow(BaseModel):
    icon: str
    title: str
    value: str
    subtitle: str
    trend: Literal["up", "down", "neutral"]
    variant: Literal["revenue", "customers", "occupancy", "alerts"]


class HourlyRevenueRow(BaseModel):
    time: str
    revenue: int


# Analytics 스키마
class WeeklyDataRow(BaseModel):
    day: str
    revenue: int
    customers: int


class HourlyCustomersRow(BaseModel):
    hour: str
    customers: int


class CategoryDataRow(BaseModel):
    name: str
    value: int
    color: str


class AnalyticsStatRow(BaseModel):
    label: str
    value: str
    change: str
    trend: Literal["up", "down"]
    iconType: Literal["trending", "users", "shopping", "clock"]
