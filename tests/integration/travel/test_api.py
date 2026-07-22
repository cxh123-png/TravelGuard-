"""差旅 API 集成测试。"""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestHealthCheck:
    """测试健康检查接口（M1 提供）。"""

    def test_health_returns_ok(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "OK"
        assert data["data"]["status"] == "ok"


class TestTravelRequestAPI:
    """测试差旅申请 API（M2 提供）。"""

    def test_create_request_without_auth_returns_401(self) -> None:
        response = client.post("/api/v1/travel-requests", json={
            "itineraries": [
                {
                    "city": "深圳",
                    "check_in": "2026-08-01",
                    "check_out": "2026-08-03",
                    "estimated_hotel_amount": "1200",
                    "estimated_transport_amount": "800",
                    "purpose": "客户拜访",
                }
            ]
        })
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"

    def test_create_request_empty_itineraries_without_auth_returns_401(self) -> None:
        response = client.post("/api/v1/travel-requests", json={
            "itineraries": []
        })
        assert response.status_code == 401

    def test_submit_without_auth_returns_401(self) -> None:
        response = client.post("/api/v1/travel-requests/req-001/submit", json={
            "employee_level": "L3",
            "city_tier": "一线",
        })
        assert response.status_code == 401

    def test_cancel_without_auth_returns_401(self) -> None:
        response = client.post("/api/v1/travel-requests/req-001/cancel")
        assert response.status_code == 401

    def test_get_rule_gate_result_without_auth_returns_401(self) -> None:
        response = client.get("/api/v1/travel-requests/req-001/rule-gate")
        assert response.status_code == 401
