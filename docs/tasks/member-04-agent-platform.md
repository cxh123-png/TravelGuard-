# 成员 4：Agent 平台任务包（M4）

## 模块目标

提供所有 Agent 共用的受控运行平台。平台负责状态、工具权限、重试、暂停恢复、Trace 与降级；它不包含差旅、报销或审计的业务规则。

## 开始条件

- M1 的配置、数据库、日志、SSE 外壳与租户上下文已合并。
- 已与 M2/M3/M5 确认 `RuleGateDecision`、人工任务、工具输入输出和 Agent 结果 Schema。

## 允许修改的目录

`src/agents/base/`、`src/orchestrator/`、`src/core/llm/`、`src/adapters/llm/`、`src/db/agent_runs/`、`src/api/v1/agent_runs/`、`src/api/v1/events/`、`tests/unit/agents/base/`、`tests/integration/orchestrator/`、`tests/contract/tools/`、`alembic/versions/`。

## 禁止修改的目录

`src/domain/travel/`、`src/domain/policy/`、`src/domain/budget/`、`src/domain/approval/`、具体 Compliance/Expense/Audit Agent 节点、前端业务页面。

## 交付步骤

1. 定义公共 Pydantic Schema：`AgentRun`、`ToolCall`、`AgentEvent`、`HumanDecision`、失败原因与版本信息。
2. 实现 Tool Registry：名称、版本、输入输出 Schema、允许调用 Agent、只读/高风险标记、超时、重试、脱敏和审计字段。
3. 实现 LLM Factory：首选模型、备用模型、超时、调用预算和一次结构化格式修复；Provider 调用不得持有数据库事务。
4. 实现 LangGraph Orchestrator：根据业务事件路由，只有 `RULE_GATE_REQUIRES_AGENT` 才创建 Compliance Agent Run；直接决策不得被 Agent 阻塞。
5. 使用 PostgreSQL Checkpointer 持久化暂停点；Human-in-the-Loop 恢复时校验 `tenant_id`、业务版本和操作者权限。
6. 实现 Trace、工具调用审计、SSE 事件、最大步数/重复工具循环保护与规则降级。

## 验收场景

- Rule Gate 的 `DIRECT_APPROVE` 和 `DIRECT_REJECT` 不创建 Agent Run。
- 未登记工具、未授权 Agent 或不匹配的输入 Schema 均被 Tool Registry 拒绝并审计。
- 同一工具连续调用超过阈值时停止图执行并转人工。
- 模型超时后只尝试允许的备用调用；仍失败时保留规则结论和 Trace。
- 人工决策可从持久化检查点恢复同一 `thread_id`，且不会串租户。

## 验证命令

```text
pytest tests/unit/agents/base/ tests/integration/orchestrator/ tests/contract/tools/ -v
ruff check src/agents/base src/orchestrator src/core/llm src/adapters/llm
mypy src/agents/base src/orchestrator src/core/llm src/adapters/llm
```

## 解锁任务

M5、M6、M7 的全部 Agent 执行；M7 的 Trace 页面和 Agent 评估报告。
