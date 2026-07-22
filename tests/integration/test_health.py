from fastapi.testclient import TestClient  # 导入 FastAPI 测试客户端，用来在测试里模拟 HTTP 请求。

from src.main import app  # 导入真实 FastAPI 应用，确保测试覆盖项目实际入口。


def test_health_returns_unified_response() -> None:  # 定义 /health 接口测试，验证健康检查和统一响应格式。
    client = TestClient(app)  # 创建测试客户端，后续可以像调用 HTTP API 一样调用应用。
    response = client.get("/health", headers={"X-Request-ID": "test-request"})  # 发送 GET /health 请求并指定固定 request_id。

    assert response.status_code == 200  # 验证 HTTP 状态码是 200，说明接口成功响应。
    assert response.headers["X-Request-ID"] == "test-request"  # 验证响应头保留了请求传入的追踪 ID。
    assert response.json() == {  # 验证响应体完全符合 M1 要求的统一响应结构。
        "code": "OK",  # 验证业务状态码是 OK。
        "data": {"status": "ok", "service": "travelguard-api"},  # 验证健康检查返回服务状态和服务名。
        "message": "success",  # 验证默认成功提示信息是 success。
        "request_id": "test-request",  # 验证响应体里也包含同一个 request_id。
    }  # 结束响应体断言。
