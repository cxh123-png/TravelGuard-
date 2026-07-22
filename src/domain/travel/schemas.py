"""跨模块共享 Schema 草案：先占位，后续与 M3/M4 对齐后填充字段。"""

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RuleGateDecision(StrEnum):
    """Rule Gate 输出：决定申请走哪条路。"""

    DIRECT_APPROVE = "DIRECT_APPROVE"
    DIRECT_REJECT = "DIRECT_REJECT"
    NEED_MORE_INFO = "NEED_MORE_INFO"
    REQUIRES_AGENT = "REQUIRES_AGENT"


class TravelRequestSnapshot(BaseModel):
    """不可变事实快照：供 M4 Agent 分析使用。

    TODO: 与 M4 对齐字段列表。
    """

    request_id: str
    tenant_id: str
    user_id: str
    created_at: datetime
    total_estimated_amount_cny: str = Field(description="预估总金额，字符串避免精度问题")
    city_list: list[str] = Field(default_factory=list)
    date_range_start: date | None = None
    date_range_end: date | None = None
    purpose_summary: str = ""
    policy_version_id: str = ""
    # M4 需要的其他字段后续补充


class PolicyEvidenceRef(BaseModel):
    """政策依据引用：供 M5 RAG 检索使用。

    TODO: 与 M5 对齐字段列表。
    """

    policy_version_id: str
    rule_id: str
    rule_type: str  # e.g. "hotel_limit", "transport_class"
    matched_value: str  # e.g. "800", "economy"
    evidence_text: str = ""  # 政策原文片段


class RuleGateResult(BaseModel):
    """Rule Gate 完整输出。"""

    decision: RuleGateDecision
    request_snapshot: TravelRequestSnapshot
    reasons: list[str] = Field(default_factory=list)
    evidence_refs: list[PolicyEvidenceRef] = Field(default_factory=list)
    requires_human: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
