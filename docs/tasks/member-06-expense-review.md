# 成员 6：报销与 Expense Review Agent 任务包（M6）

## 模块目标

实现报销资料的可信事实处理和费用审核建议。OCR、验真、三单匹配、重复检测是确定性服务；Expense Review Agent 只处理需要语义理解的异常解释和审核建议。

## 开始条件

- M1 的对象存储、异步任务、数据库和权限基础已合并。
- M2 的已完成差旅、行程和政策版本事实可读。
- M3 的结算接口、预算预占引用和审批接口已合并。
- M4 的 Agent 平台已合并；M5 的 `PolicyEvidence` Schema 可复用。

## 允许修改的目录

`src/domain/expense/`、`src/application/expense/`、`src/agents/expense_review/`、`src/adapters/invoice/`、`src/adapters/storage/` 的票据实现、`src/api/v1/expense_claims/`、`src/celery/expense/`、`tests/unit/expense/`、`tests/unit/agents/expense_review/`、`tests/integration/expense/`、`alembic/versions/`。

## 禁止修改的目录

预算账本实现、差旅申请状态机、Agent 公共平台、政策 RAG 内核、审计实现和前端页面。

## 交付步骤

1. 建立 `ExpenseClaim`、`ExpenseItem`、`Invoice`、Provider 调用记录及文件指纹模型。
2. 实现文件隔离上传、大小/MIME/内容校验、哈希去重和短时签名访问；Provider 原始响应不进入领域层。
3. 通过 Celery 执行 OCR 与验真，并映射为内部 `InvoiceRecognitionResult`；外部调用不持有数据库事务。
4. 实现申请—预订—票据/消费三单匹配和发票/文件重复检测。
5. 实现费用规则，输出确定性发现；金额由程序重新计算。
6. 实现 Expense Review Agent，读取结构化事实和政策证据，输出审核建议、逐项发现和人工复核原因；Agent 不写结算或审批状态。
7. 调用 M3 的结算服务完成通过后的 `SETTLE` 和差额释放。

## 验收场景

- 相同发票号码或文件哈希重复上传被识别，不能自动通过。
- OCR 与验真字段冲突、金额不一致或个人延住均强制人工复核。
- Agent 给出的建议金额与程序逐项求和不一致时，结果无效且不结算。
- 同一报销请求重复提交不会重复 OCR、审批或结算。

## 验证命令

```text
pytest tests/unit/expense/ tests/unit/agents/expense_review/ tests/integration/expense/ -v
ruff check src/domain/expense src/application/expense src/agents/expense_review src/adapters/invoice
mypy src/domain/expense src/application/expense src/agents/expense_review src/adapters/invoice
```

## 解锁任务

M7 的财务页面、审计特征、报销 E2E 和 Phase 4 跨单据审计。
