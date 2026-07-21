# 成员 3：预算与审批任务包（M3）

## 模块目标

实现确定性的预算与审批能力。Agent 可以建议路径和解释风险，但不能写预算流水、审批动作或业务状态。

## 开始条件

- M1 的事务、认证租户上下文、迁移与幂等键解析已合并。
- 已与 M2 确认 `TravelRequestId`、申请状态和预计金额快照；已与 M4 确认人工接管事件格式。

## 允许修改的目录

`src/domain/budget/`、`src/domain/approval/`、`src/application/budget/`、`src/application/approval/`、`src/adapters/persistence/budget/`、`src/adapters/persistence/approval/`、`src/api/v1/budgets/`、`src/api/v1/approvals/`、`src/celery/` 的 Outbox 投递、`tests/unit/budget/`、`tests/unit/approval/`、`tests/integration/budget/`、`alembic/versions/`。

## 禁止修改的目录

差旅/政策领域逻辑、`src/agents/`、LLM Provider、OCR/验真实现、前端业务页面。

## Phase 1 交付物

- 单笔预算可用性查询、原子 `RESERVE`、`RELEASE` 和最小预算流水。
- 单一人工审批任务：创建、通过、驳回、超时释放，全部带 `expected_version` 和 `Idempotency-Key`。
- Rule Gate 或 Agent 平台调用的只读预算工具；工具不允许写账。

## Phase 2 扩展

- 追加式完整账本：`ALLOCATE`、`RESERVE`、`RELEASE`、`SETTLE`、`ADJUST`。
- 多级审批、例外审批、加签、Outbox 可靠通知和并发冲突处理。

## 验收场景

- 相同幂等键重复提交预算预占，只产生一条 `RESERVE`。
- 两个并发申请争抢最后余额时，最多一个成功。
- 审批驳回或超时后恰好释放一次预算。
- Agent 失败或人工接管不会回滚已确认的确定性账本事实。

## 验证命令

```text
pytest tests/unit/budget/ tests/unit/approval/ tests/integration/budget/ -v
ruff check src/domain/budget src/domain/approval src/application/budget src/application/approval
mypy src/domain/budget src/domain/approval src/application/budget src/application/approval
```

## 解锁任务

M5 的合规建议路径、M6 的实际结算、M7 的审批页面和审计预算事实。
