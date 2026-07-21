# 成员 5：Compliance Agent 与政策 RAG 任务包（M5）

## 模块目标

将版本化政策文档转换成可追溯证据，并在 M2 的 Rule Gate 已无法安全自动裁决时，给出结构化的合规建议。该模块不能覆盖硬规则、预算或审批动作。

## 开始条件

- M1 的对象存储、数据库、配置和 Provider Adapter 基础已合并。
- M2 已提供 `TravelRequestSnapshot`、`RuleGateDecision=REQUIRES_AGENT`、政策版本和规则结果。
- M4 已提供 Tool Registry、Agent Run、Checkpointer、Trace 和 Human-in-the-Loop 契约。

## 允许修改的目录

`src/vectorstore/`、`src/adapters/vectorstore/`、`src/adapters/storage/` 的政策文档实现、`src/agents/compliance/`、`src/application/policy_knowledge/`、`src/api/v1/policies/` 的文档/索引接口、`scripts/evaluations/`、`tests/unit/vectorstore/`、`tests/unit/agents/compliance/`、`tests/evaluations/compliance/`。

## 禁止修改的目录

Rule Gate 与结构化规则、预算账本、审批状态机、Agent 公共基座、OCR/报销/审计领域实现。

## 交付步骤

1. 实现政策导入、版本元数据、生效区间、适用组织和内容哈希。
2. 按条款语义切分政策文档，保留 `tenant_id`、`policy_version_id`、章节、页码、适用期和条款 ID。
3. 实现 BM25/稀疏召回、向量召回、Rerank 和相邻上下文扩展；检索必须先按租户、政策版本和业务日期硬过滤。
4. 定义 `PolicyEvidence`：版本、条款、原文摘录、来源位置、适用理由和检索分数。
5. 实现 Compliance Agent 图：读取 Rule Gate 快照，检索证据，分析例外说明，生成 `PASS_RECOMMENDED`、`EXCEPTION_APPROVAL`、`REJECT_RECOMMENDED` 或 `NEED_MORE_INFO` 建议。
6. 对 Agent 输出校验证据引用、政策版本、枚举、金额和租户一致性；无证据时输出 `EVIDENCE_INSUFFICIENT` 并转人工。
7. 建立固定金标集，分别度量条款召回、证据引用正确率、合规建议和人工接管正确性。

## 验收场景

- 政策更新后，历史申请仍引用业务发生日对应的版本。
- 展会满房例外只在检索到有效条款时产生例外建议。
- 无有效证据时 Agent 不得编造条款或自动放行。
- Agent 输出与 Rule Gate 的硬性拒绝冲突时，系统保留 Rule Gate 结论并转人工。

## 验证命令

```text
pytest tests/unit/vectorstore/ tests/unit/agents/compliance/ -v
pytest tests/evaluations/compliance/ -v
ruff check src/vectorstore src/agents/compliance src/application/policy_knowledge
mypy src/vectorstore src/agents/compliance src/application/policy_knowledge
```

## 解锁任务

M6 对政策证据的复用、M7 的合规结果/Trace 页面、Phase 2 的模型与检索回归评估。
