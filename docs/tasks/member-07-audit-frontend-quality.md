# 成员 7：审计、前端与质量任务包（M7）

## 模块目标

提供最小但完整的业务操作界面、端到端验证和最终审计能力。前端只呈现事实、状态和 Agent 证据，不复制后端规则；审计 Agent 只产生待人工确认的发现。

## 开始条件

- 前端工程依赖 M1 的认证、统一错误与 API/SSE 契约。
- 申请/合规页面依赖 M2、M3、M4、M5 的已合并 API。
- 报销页面依赖 M6；审计 Agent 依赖 M3 至 M6 的只读事实和 Trace。

## 允许修改的目录

`frontend/`、`src/domain/audit/`、`src/application/audit/`、`src/agents/audit_analysis/`、`src/api/v1/audit/`、`scripts/seed_data/`、`scripts/evaluations/` 的跨模块运行脚本、`tests/e2e/`、`tests/evaluations/audit/`、`tests/frontend/`、`alembic/versions/`。

## 禁止修改的目录

差旅/政策/预算/审批领域规则、Agent Platform 公共实现、Compliance/Expense Agent 内部节点、Provider Adapter 内部实现。

## Phase 0 与 Phase 1 交付物

1. 初始化 Vue 3、TypeScript、Vite、Element Plus、Pinia、API 客户端和路由守卫。
2. 实现差旅申请、合规结果、人工审批和 Agent Trace 四个最小页面。
3. SSE 客户端必须支持事件序号、去重和重连；页面只展示服务端提供的状态、金额和合规结果。
4. 编写 Phase 1 E2E：明确合规、直接拒绝、政策例外转人工、Provider/模型失败转人工。
5. 构造脱敏种子数据和固定 Agent 评估运行入口。

## Phase 3 与 Phase 4 交付物

1. 实现报销上传、审核结果、财务复核页面和报销 E2E。
2. 建立审计批次、风险特征、Audit Analysis Agent、审计发现和人工确认流程。
3. 实现审计看板和报告导出；正式报告只展示人工确认的发现。
4. 提供跨模块回归报告，比较 Agent 指标、人工接管率、调用成本和 E2E 结果。

## 验收场景

- 用户能通过界面完成 Phase 1 四条路径，并看到政策证据和完整 Trace。
- 断开 SSE 后重连不重复显示或遗漏终态事件。
- 审计 Agent 只能提交待确认发现；人工确认前不能进入正式报告。
- E2E 不依赖真实机酒、支付、真实个人数据或生产 Provider。

## 验证命令

```text
cd frontend && npm run lint && npm run typecheck && npm run test
pytest tests/e2e/ tests/evaluations/audit/ -v
```

## 解锁任务

每个阶段的手工演示与最终集成验收；Phase 5 的压测、故障演练和发布检查。
