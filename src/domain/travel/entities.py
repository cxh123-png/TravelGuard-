"""差旅领域实体：核心业务对象，不依赖任何框架。"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Self

from src.domain.travel.value_objects import Money


class TravelStatus(StrEnum):
    """差旅申请状态机。"""

    DRAFT = "DRAFT"
    RULE_CHECKING = "RULE_CHECKING"
    NEED_MORE_INFO = "NEED_MORE_INFO"
    AGENT_REVIEWING = "AGENT_REVIEWING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED_BY_POLICY = "REJECTED_BY_POLICY"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    APPROVED = "APPROVED"


@dataclass
class TravelItinerary:
    """行程明细（值对象/子实体）。"""

    city: str
    check_in: date
    check_out: date
    estimated_hotel_amount: Money
    estimated_transport_amount: Money
    purpose: str = ""


@dataclass
class TravelRequest:
    """差旅申请单：领域根实体。"""

    id: str
    tenant_id: str
    user_id: str
    status: TravelStatus = TravelStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    itineraries: list[TravelItinerary] = field(default_factory=list)
    version: int = 1  # 乐观锁版本号

    def add_itinerary(self, itinerary: TravelItinerary) -> Self:
        """添加行程明细。"""
        self.itineraries.append(itinerary)
        self.updated_at = datetime.utcnow()
        return self

    def submit(self) -> Self:
        """提交申请，进入规则检查。"""
        if self.status != TravelStatus.DRAFT:
            raise ValueError(f"Cannot submit from status {self.status}")
        self.status = TravelStatus.RULE_CHECKING
        self.updated_at = datetime.utcnow()
        return self

    def cancel(self) -> Self:
        """取消申请。"""
        if self.status not in {TravelStatus.DRAFT, TravelStatus.NEED_MORE_INFO, TravelStatus.PENDING_APPROVAL}:
            raise ValueError(f"Cannot cancel from status {self.status}")
        self.status = TravelStatus.CANCELLED
        self.updated_at = datetime.utcnow()
        return self

    def need_more_info(self) -> Self:
        """规则检查发现结构化信息缺失。"""
        if self.status not in {TravelStatus.RULE_CHECKING, TravelStatus.AGENT_REVIEWING}:
            raise ValueError(f"Cannot request more info from status {self.status}")
        self.status = TravelStatus.NEED_MORE_INFO
        self.updated_at = datetime.utcnow()
        return self

    def reject_by_policy(self) -> Self:
        """硬性政策违规，直接拒绝。"""
        if self.status != TravelStatus.RULE_CHECKING:
            raise ValueError(f"Cannot reject by policy from status {self.status}")
        self.status = TravelStatus.REJECTED_BY_POLICY
        self.updated_at = datetime.utcnow()
        return self

    def send_to_agent(self) -> Self:
        """转入 Agent 审查。"""
        if self.status != TravelStatus.RULE_CHECKING:
            raise ValueError(f"Cannot send to agent from status {self.status}")
        self.status = TravelStatus.AGENT_REVIEWING
        self.updated_at = datetime.utcnow()
        return self

    def approve_pending(self) -> Self:
        """规则通过，等待人工审批。"""
        if self.status not in {TravelStatus.RULE_CHECKING, TravelStatus.AGENT_REVIEWING}:
            raise ValueError(f"Cannot approve pending from status {self.status}")
        self.status = TravelStatus.PENDING_APPROVAL
        self.updated_at = datetime.utcnow()
        return self

    def approve(self) -> Self:
        """人工审批通过。"""
        if self.status != TravelStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot approve from status {self.status}")
        self.status = TravelStatus.APPROVED
        self.updated_at = datetime.utcnow()
        return self

    def reject(self) -> Self:
        """人工审批驳回。"""
        if self.status != TravelStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot reject from status {self.status}")
        self.status = TravelStatus.REJECTED
        self.updated_at = datetime.utcnow()
        return self

    def resubmit_from_need_info(self) -> Self:
        """补充信息后重新进入 Rule Gate。"""
        if self.status != TravelStatus.NEED_MORE_INFO:
            raise ValueError(f"Cannot resubmit from status {self.status}")
        self.status = TravelStatus.RULE_CHECKING
        self.updated_at = datetime.utcnow()
        return self

    def return_to_rule_check(self) -> Self:
        """Agent 解析出新事实后重新校验。"""
        if self.status != TravelStatus.AGENT_REVIEWING:
            raise ValueError(f"Cannot return to rule checking from status {self.status}")
        self.status = TravelStatus.RULE_CHECKING
        self.updated_at = datetime.utcnow()
        return self

    def total_estimated_amount(self) -> Money:
        """计算预估总金额。"""
        total = Money(amount="0", currency="CNY")
        for it in self.itineraries:
            total = total.add(it.estimated_hotel_amount)
            total = total.add(it.estimated_transport_amount)
        return total
