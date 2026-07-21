# 成员 2：差旅、政策与 Rule Gate 任务包（M2）

## 模块目标

实现差旅申请和版本化结构化政策规则，并通过 Rule Gate 把案件稳定分成“直接决策”与“需要 Agent”的路径。Rule Gate 是确定性程序，不调用 LLM。

## 开始条件

- M1 的数据库会话、认证上下文、迁移和统一错误模型已合并。
- 已与 M3、M4 确认公共 Schema：`TravelRequestSnapshot`、`RuleGateDecision`、`PolicyEvidenceRef`。

## 允许修改的目录

`src/domain/travel/`、`src/domain/policy/`、`src/application/travel/`、`src/application/policy/`、`src/adapters/persistence/travel/`、`src/adapters/persistence/policy/`、`src/api/v1/travel/`、`tests/unit/travel/`、`tests/unit/policy/`、`tests/integration/travel/`、`alembic/versions/`。

## 禁止修改的目录

`src/agents/`、`src/orchestrator/`、`src/domain/budget/`、`src/domain/approval/`、OCR/对象存储 Provider、前端页面。

## 交付步骤

1. 建立 `TravelRequest`、`TravelItinerary`、`Policy`、`PolicyVersion` 与结构化 `PolicyRule` 的领域实体、迁移和仓储。
2. 实现申请创建、提交、取消和乐观锁状态迁移；状态遵循 `DRAFT → RULE_CHECKING → NEED_MORE_INFO / AGENT_REVIEWING / PENDING_APPROVAL / REJECTED_BY_POLICY / APPROVED`。
3. 实现按租户、组织、业务发生日选择政策版本的规则服务。
4. 实现 Rule Gate：字段、权限、状态、硬性政策和预算预检结果输入后，只能输出 `DIRECT_APPROVE`、`DIRECT_REJECT`、`NEED_MORE_INFO` 或 `REQUIRES_AGENT`。
5. 为 `REQUIRES_AGENT` 输出不可变事实快照与明确原因；M4 使用它创建 Agent Run，M5 只读取它。
6. 提供申请 API 与 Rule Gate 结果查询 API。

## 验收场景

- 住宿金额超过不可例外阈值，Rule Gate 直接拒绝且不创建 Agent Run。
- 普通合规申请直接进入预算预占/审批路径且不调用 LLM。
- 含展会满房例外说明的申请输出 `REQUIRES_AGENT`，保留政策版本和待分析文本。
- 补充信息后必须重新进入 Rule Gate，不能从旧状态直接通过。

## 验证命令

```text
pytest tests/unit/travel/ tests/unit/policy/ tests/integration/travel/ -v
ruff check src/domain/travel src/domain/policy src/application/travel src/application/policy
mypy src/domain/travel src/domain/policy src/application/travel src/application/policy
```

## 解锁任务

M4 的 Agent 路由、M5 的 Compliance Agent、M6 的申请/行程事实匹配、M7 的申请和合规结果页面。
