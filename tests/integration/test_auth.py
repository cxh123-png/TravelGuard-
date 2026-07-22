from fastapi.testclient import TestClient  # 导入 FastAPI 测试客户端，用来模拟 HTTP 请求。

from src.core.security import create_access_token  # 导入 JWT 生成函数，用来构造测试用访问令牌。
from src.main import app  # 导入真实应用入口，确保测试覆盖实际中间件和异常处理器。


def test_protected_route_requires_authentication() -> None:  # 测试受保护接口在没有 token 时返回统一未认证错误。
    client = TestClient(app)  # 创建测试客户端。
    response = client.get("/api/v1/me", headers={"X-Request-ID": "auth-test"})  # 不带 Authorization 访问受保护接口。

    assert response.status_code == 401  # 验证 HTTP 状态码是 401 未认证。
    assert response.headers["X-Request-ID"] == "auth-test"  # 验证响应头里保留请求追踪 ID。
    assert response.json() == {  # 验证错误响应体符合统一格式。
        "code": "UNAUTHORIZED",  # 验证业务错误码是未认证。
        "data": {"details": {}},  # 验证错误详情为空字典。
        "message": "Authentication required.",  # 验证错误提示来自认证依赖。
        "request_id": "auth-test",  # 验证响应体里也包含同一个 request_id。
    }  # 结束响应体断言。


def test_protected_route_returns_current_user_context() -> None:  # 测试带有效 token 时受保护接口返回当前用户上下文。
    client = TestClient(app)  # 创建测试客户端。
    token = create_access_token(subject="user-1", tenant_id="tenant-1", roles=["employee"])  # 创建测试访问令牌。
    response = client.get(  # 发送受保护接口请求。
        "/api/v1/me",  # 指定受保护示例接口路径。
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": "auth-success"},  # 同时传入 Bearer token 和追踪 ID。
    )  # 结束请求构造。

    assert response.status_code == 200  # 验证认证成功时 HTTP 状态码为 200。
    assert response.headers["X-Request-ID"] == "auth-success"  # 验证响应头保留同一个追踪 ID。
    assert response.json() == {  # 验证响应体符合统一成功响应格式。
        "code": "OK",  # 验证业务状态码是 OK。
        "data": {"user_id": "user-1", "tenant_id": "tenant-1", "roles": ["employee"]},  # 验证用户上下文被正确解析。
        "message": "success",  # 验证默认成功提示信息。
        "request_id": "auth-success",  # 验证响应体里保留同一个 request_id。
    }  # 结束响应体断言。
