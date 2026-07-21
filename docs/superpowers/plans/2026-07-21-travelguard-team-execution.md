# TravelGuard Team Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver TravelGuard through seven independently reviewable modules that integrate in dependency order.

**Architecture:** Deterministic domain services own rules, budget, approval and state transitions. The Agent platform orchestrates only controlled semantic work; Compliance, Expense and Audit Agents consume fact snapshots and return suggestions with evidence.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy Async, PostgreSQL, Redis, Celery, LangGraph, Milvus, PaddleOCR, Vue 3 and TypeScript.

## Global Constraints

- Use Python 3.11 and the root `requirements.txt`; do not create a virtual environment as part of planning.
- `main` is PR-only; work begins from a short-lived task branch.
- Agent code cannot directly access ORM/database connections or perform budget, approval or state writes.
- All write commands require idempotency; all money uses `Decimal`; all times store UTC; all tables include `tenant_id`.
- Every task must include a failing test before implementation, targeted test evidence, and a user-observable verification.

---

### Task 1: Establish the engineering platform

**Owner:** Member 1.  
**Task package:** [member-01-engineering-platform.md](../../tasks/member-01-engineering-platform.md).  
**Depends on:** none.  
**Unblocks:** Tasks 2 through 7.

- [ ] Implement and merge M1 only after its Phase 0 acceptance scenarios pass.

### Task 2: Implement deterministic travel and policy routing

**Owner:** Member 2.  
**Task package:** [member-02-travel-policy-rule-gate.md](../../tasks/member-02-travel-policy-rule-gate.md).  
**Depends on:** Task 1.  
**Unblocks:** Tasks 4, 5, 6 and 7.

- [ ] Merge the public `RuleGateDecision` contract before integrating Agent code.

### Task 3: Implement budget and approval controls

**Owner:** Member 3.  
**Task package:** [member-03-budget-approval.md](../../tasks/member-03-budget-approval.md).  
**Depends on:** Task 1.  
**Unblocks:** Tasks 5, 6 and 7.

- [ ] Merge minimal reservation and approval behavior for Phase 1 before the full Phase 2 ledger expansion.

### Task 4: Implement the controlled Agent platform

**Owner:** Member 4.  
**Task package:** [member-04-agent-platform.md](../../tasks/member-04-agent-platform.md).  
**Depends on:** Task 1 and the shared contracts from Tasks 2 and 3.  
**Unblocks:** Tasks 5, 6 and 7.

- [ ] Verify direct Rule Gate decisions bypass Agent execution before merging.

### Task 5: Build policy RAG and Compliance Agent

**Owner:** Member 5.  
**Task package:** [member-05-compliance-rag.md](../../tasks/member-05-compliance-rag.md).  
**Depends on:** Tasks 1, 2 and 4.  
**Unblocks:** Tasks 6 and 7.

- [ ] Publish fixed evaluation evidence with the Phase 1 PR.

### Task 6: Build expense processing and Expense Review Agent

**Owner:** Member 6.  
**Task package:** [member-06-expense-review.md](../../tasks/member-06-expense-review.md).  
**Depends on:** Tasks 1 through 5.  
**Unblocks:** Task 7 Phase 3/4 integration.

- [ ] Prove OCR, matching, Agent recommendation and settlement remain separated before merging.

### Task 7: Build UI, E2E and audit capability

**Owner:** Member 7.  
**Task package:** [member-07-audit-frontend-quality.md](../../tasks/member-07-audit-frontend-quality.md).  
**Depends on:** Task 1 for UI scaffolding; Tasks 2 through 6 for corresponding integrations.  
**Unblocks:** Final user acceptance and Phase 5 hardening.

- [ ] Keep dependent implementation PRs as drafts until their APIs are merged into `main`.
