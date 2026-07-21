# 成员 1：工程平台任务包（M1）

## 模块目标

提供所有模块共享且不含业务决策的工程底座：运行配置、认证、数据库会话、迁移、统一 API 外壳、基础观测、容器编排与 CI。

## 开始条件

- 已阅读根目录 `requirements.txt` 与 `实现方案.md` 的技术栈、分层和安全约束。
- 已从最新 `main` 创建个人分支。

## 允许修改的目录

`pyproject.toml`、`.env.example`、`docker-compose.yml`、`.github/`、`alembic/`、`src/main.py`、`src/core/`、`src/db/`、`src/api/` 的公共中间件/依赖、`src/infrastructure/observability/`、`tests/integration/`、`tests/contract/`。

## 禁止修改的目录

`src/domain/travel/`、`src/domain/policy/`、`src/domain/budget/`、`src/domain/approval/`、`src/agents/` 的业务实现、`frontend/src/views/` 的业务页面。

## Phase 0 交付物

1. Python 3.11 项目配置、Ruff、mypy、pytest 与 pre-commit 配置。
2. FastAPI 应用入口、`/health`、统一 `{code,data,message,request_id}` 响应和全局异常映射。
3. Pydantic Settings、`.env.example`、脱敏结构化日志与 `request_id` 中间件。
4. SQLAlchemy Async 会话、Alembic、PostgreSQL/Redis/Milvus/MinIO Docker Compose 服务。
5. JWT 认证骨架、`tenant_id` 注入依赖和最小角色检查；所有后续查询可从此处取得租户上下文。
6. GitHub Actions：后端格式、类型与测试检查；前端检查命令先以存在性检测方式接入，待前端工程合并后启用。

## 对其他模块的公共契约

- 提供请求上下文：`request_id`、认证用户 ID、`tenant_id`、角色集合。
- 提供异步数据库事务和仓储基类；领域层不得直接导入 FastAPI 或 ORM。
- 提供统一错误码、分页、幂等键解析和 SSE 事件外壳。

接口变更必须先开契约 PR，获得 M2 至 M7 的确认后再合并。

## 验收场景

- 未认证请求访问受保护路由，返回统一权限错误且带 `request_id`。
- 带有效租户上下文的健康/示例路由可访问，日志不包含密钥。
- Alembic 能升级、回滚一级、再升级。
- Docker Compose 中 PostgreSQL、Redis、Milvus、MinIO 可被健康检查发现。

## 验证命令

```text
ruff check .
ruff format --check .
mypy src/
pytest tests/integration/ tests/contract/ -v
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

## 解锁任务

M2、M3、M4 的实现工作；M7 的前端工程初始化与 E2E 外壳。
