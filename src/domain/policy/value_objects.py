"""政策值对象。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyRuleCondition:
    """规则条件：如"职级 >= 经理 AND 城市等级 = 一线"。

    TODO: 后续可以演进为结构化表达式或小型 DSL。
    """

    city_tier: str | None = None  # 城市等级：一线、二线...
    employee_level: str | None = None  # 员工职级
    transport_type: str | None = None  # 交通工具：飞机、高铁...
    # 更多条件维度后续补充
