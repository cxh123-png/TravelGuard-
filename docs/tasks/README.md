# 成员任务包索引

每个任务包都是成员的工作边界和 AI 指令依据。成员不得跳过“开始条件”，也不得将自己的任务包理解为可修改全仓库的授权。

| 任务包 | 模块 | Phase 0 | Phase 1 | 后续阶段 |
|---|---|---|---|---|
| [成员 1](member-01-engineering-platform.md) | 工程平台 | 工程、配置、数据库、CI | 鉴权、公共 API、观测 | 部署与运行加固 |
| [成员 2](member-02-travel-policy-rule-gate.md) | 差旅与政策规则 | Schema 与规则草案 | Rule Gate 与申请流程 | 政策发布与规则冲突检查 |
| [成员 3](member-03-budget-approval.md) | 预算与审批 | 账本/审批契约 | 最小预占与单一审批 | 完整账本与多级审批 |
| [成员 4](member-04-agent-platform.md) | Agent 平台 | State、工具和事件契约 | Orchestrator、Trace、HITL | 版本回放与影子评估 |
| [成员 5](member-05-compliance-rag.md) | Compliance 与 RAG | 政策样本与检索评估集 | Hybrid RAG 与 Compliance Agent | 质量回归与证据治理 |
| [成员 6](member-06-expense-review.md) | 报销与 Expense Agent | 票据/报销 Schema 与样本 | 依赖验证与测试准备 | OCR、匹配、Expense Agent |
| [成员 7](member-07-audit-frontend-quality.md) | 审计、前端与质量 | 页面原型、E2E 契约 | 申请/Trace 页面与 E2E | 审计 Agent、看板、全链路回归 |

## AI 提示词最小模板

```text
你正在实现 TravelGuard 的 [任务包编号]。先阅读：实现方案.md、docs/01-整体实施路线图.md、docs/02-协作PR与验收规范.md 和你的任务包。

仅修改任务包“允许修改的目录”；不要修改“禁止修改的目录”。先确认所有开始条件已经在 main 合并；不满足时停止实现并报告具体阻塞项。按任务包中的验收场景先写失败测试，再实现最小变更。运行任务包列出的验证命令，并在 PR 描述中逐项报告结果与可观察证据。
```
