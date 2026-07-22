"""差旅值对象：不可变、无身份标识的业务概念。"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Money:
    """金额值对象：禁止浮点数，精确到分。"""

    amount: str  # 使用字符串避免浮点精度问题
    currency: str = "CNY"

    def __post_init__(self) -> None:
        try:
            Decimal(self.amount)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid money amount: {self.amount}") from exc

    def to_decimal(self) -> Decimal:
        return Decimal(self.amount)

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add money of different currencies")
        return Money(amount=str(self.to_decimal() + other.to_decimal()), currency=self.currency)


@dataclass(frozen=True)
class TravelDateRange:
    """出行日期范围。"""

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("Start date must not be after end date")

    def days(self) -> int:
        """出行天数（含首尾）。"""
        return (self.end_date - self.start_date).days + 1
