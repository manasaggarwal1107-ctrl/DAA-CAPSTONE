"""Pydantic models: the shared data structures used by every module."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["pending", "delivered", "cancelled"]
DEADLINE_FORMAT = "%Y-%m-%dT%H:%M"


def normalise_deadline(value: object) -> str:
    """Accept ``YYYY-MM-DD`` or ``YYYY-MM-DD[T ]HH:MM[:SS]`` and return ``YYYY-MM-DDTHH:MM``."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Deadline is required (e.g. 2026-12-03 or 2026-12-03T17:30)")
    text = value.strip().replace(" ", "T")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).strftime(DEADLINE_FORMAT)
        except ValueError:
            continue
    raise ValueError(f"'{value}' is not a valid date/time. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM")


def _whole_number(v: object, label: str) -> int:
    """Weights and values must be whole numbers (the DP table is indexed by integers)."""
    if isinstance(v, bool):
        raise ValueError(f"{label} must be a whole number")
    if isinstance(v, str):
        try:
            v = float(v.strip())
        except ValueError:
            raise ValueError(f"{label} must be a whole number") from None
    if isinstance(v, float):
        if v != int(v):
            raise ValueError(f"{label} must be a whole number (got {v})")
        v = int(v)
    if not isinstance(v, int):
        raise ValueError(f"{label} must be a whole number")
    return v


class Parcel(BaseModel):
    """A delivery parcel.  ``weight`` is whole kg; ``value`` is whole currency units."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    id: str = Field(min_length=1, max_length=40)
    destination: str = Field(min_length=1, max_length=80)
    weight: int = Field(ge=1, le=10_000, description="kg, whole number")
    priority: int = Field(ge=1, le=5, description="5 = most urgent")
    deadline: str
    value: int = Field(ge=0, le=100_000_000)
    status: Status = "pending"

    @field_validator("weight", mode="before")
    @classmethod
    def _weight(cls, v: object) -> int:
        return _whole_number(v, "Weight")

    @field_validator("value", mode="before")
    @classmethod
    def _value(cls, v: object) -> int:
        return _whole_number(v, "Delivery value")

    @field_validator("priority", mode="before")
    @classmethod
    def _priority(cls, v: object) -> int:
        return _whole_number(v, "Priority")

    @field_validator("deadline", mode="before")
    @classmethod
    def _deadline(cls, v: object) -> str:
        return normalise_deadline(v)

    @field_validator("status", mode="before")
    @classmethod
    def _status(cls, v: object) -> object:
        return "pending" if v in (None, "") else (v.lower() if isinstance(v, str) else v)


class ParcelDraft(Parcel):
    """Create payload: ``id`` may be omitted and is then generated."""
    id: str = Field(default="", max_length=40)


class Location(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=60)
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)


class Road(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    a: str = Field(min_length=1)
    b: str = Field(min_length=1)
    weight: float = Field(description="distance in km; must not be negative")
    bidirectional: bool = True


class RoadRef(BaseModel):
    a: str
    b: str
    bidirectional: bool = True


class Settings(BaseModel):
    capacity: int = Field(ge=0, le=100_000, description="vehicle capacity in kg")
    depot: str = Field(min_length=1)
    dispatch_time: str = "2026-12-01T09:00"
    speed_kmph: float = Field(default=30.0, gt=0, le=200)
    service_minutes: int = Field(default=5, ge=0, le=240)

    @field_validator("dispatch_time", mode="before")
    @classmethod
    def _dispatch(cls, v: object) -> str:
        return normalise_deadline(v)


class SettingsPatch(BaseModel):
    capacity: Optional[int] = Field(default=None, ge=0, le=100_000)
    depot: Optional[str] = None
    dispatch_time: Optional[str] = None
    speed_kmph: Optional[float] = Field(default=None, gt=0, le=200)
    service_minutes: Optional[int] = Field(default=None, ge=0, le=240)


class PathRequest(BaseModel):
    source: str
    target: str


class OptimiseRequest(BaseModel):
    capacity: Optional[int] = Field(default=None, ge=0, le=100_000)
    depot: Optional[str] = None
    sorter: str = "merge"


class ImportRequest(BaseModel):
    format: Literal["json", "csv"]
    content: str
    mode: Literal["append", "replace"] = "append"


class BenchmarkRequest(BaseModel):
    sizes: list[int] = Field(default_factory=lambda: [10, 50, 100, 500, 1000, 5000])
    repeats: int = Field(default=5, ge=1, le=15)
    seed: int = 42

    @field_validator("sizes")
    @classmethod
    def _sizes(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("Select at least one dataset size")
        if any(s < 1 or s > 10_000 for s in v):
            raise ValueError("Dataset sizes must be between 1 and 10,000 parcels")
        return sorted(set(v))


class DatasetRequest(BaseModel):
    size: int = Field(default=24, ge=0, le=5000)
    seed: int = 2026


class LearnSortRequest(BaseModel):
    values: list[int] = Field(min_length=1, max_length=16)


class LearnKnapsackRequest(BaseModel):
    weights: list[int] = Field(min_length=1, max_length=8)
    values: list[int] = Field(min_length=1, max_length=8)
    capacity: int = Field(ge=0, le=30)


class LearnGraphRequest(BaseModel):
    source: str = "A"
    target: str = "F"
    stops: list[str] = Field(default_factory=lambda: ["B", "D", "F"])
