from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base


class RouteSearch(Base):
    __tablename__ = "route_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_hash: Mapped[str] = mapped_column(String(96), index=True)
    source_lat: Mapped[float] = mapped_column(Float)
    source_lon: Mapped[float] = mapped_column(Float)
    dest_lat: Mapped[float] = mapped_column(Float)
    dest_lon: Mapped[float] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(String(32))
    selected_route_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SegmentObservation(Base):
    __tablename__ = "segment_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_id: Mapped[str] = mapped_column(String(64), index=True)
    avg_speed_kph: Mapped[float] = mapped_column(Float)
    travel_time_seconds: Mapped[float] = mapped_column(Float)
    congestion_index: Mapped[float] = mapped_column(Float)
    sample_count: Mapped[int] = mapped_column(Integer)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

