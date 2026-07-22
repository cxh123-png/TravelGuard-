"""Budget value objects."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Self

MONEY_SCALE = Decimal("0.01")


@dataclass(frozen=True)
class Money:
    """Money stored as Decimal with a currency code."""

    amount: Decimal
    currency: str = "CNY"

    @classmethod
    def from_value(cls, amount: Decimal | int | str, currency: str = "CNY") -> Self:
        try:
            decimal_amount = Decimal(str(amount)).quantize(MONEY_SCALE, rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid money amount: {amount}") from exc
        return cls(amount=decimal_amount, currency=currency)

    def __post_init__(self) -> None:
        if not self.currency:
            raise ValueError("Currency is required")
        object.__setattr__(self, "amount", self.amount.quantize(MONEY_SCALE, rounding=ROUND_HALF_UP))

    def ensure_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError("Money currency mismatch")

    def add(self, other: "Money") -> "Money":
        self.ensure_same_currency(other)
        return Money.from_value(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        self.ensure_same_currency(other)
        return Money.from_value(self.amount - other.amount, self.currency)

    def require_positive(self) -> None:
        if self.amount <= Decimal("0"):
            raise ValueError("Money amount must be positive")

    def to_string(self) -> str:
        return f"{self.amount:.2f}"
