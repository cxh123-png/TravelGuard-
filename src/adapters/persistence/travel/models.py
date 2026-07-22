"""差旅数据库 ORM 模型：继承 M1 提供的 Base。"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class TravelRequestModel(Base):
    """差旅申请数据库模型。"""

    __tablename__ = "travel_requests"
    __mapper_args__ = {"version_id_col": "version"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    version: Mapped[int] = mapped_column(default=1)

    # 关联行程
    itineraries: Mapped[list["TravelItineraryModel"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class TravelItineraryModel(Base):
    """行程明细数据库模型。"""

    __tablename__ = "travel_itineraries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(
        ForeignKey("travel_requests.id", ondelete="CASCADE"), index=True
    )
    city: Mapped[str] = mapped_column(String(64))
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    estimated_hotel_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    estimated_transport_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    purpose: Mapped[str] = mapped_column(String(256), default="")

    request: Mapped[TravelRequestModel] = relationship(back_populates="itineraries")
