"""Budget and approval API authentication tests."""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_budget_account_requires_authentication() -> None:
    response = client.post(
        "/api/v1/budgets/accounts",
        json={"budget_center_id": "dept-1", "allocated_amount": "1000", "currency": "CNY"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_budget_reserve_requires_authentication_before_idempotency_header() -> None:
    response = client.post(
        "/api/v1/budgets/reservations",
        headers={"Idempotency-Key": "idem-1"},
        json={
            "account_id": "budget-1",
            "business_id": "travel-1",
            "amount": "300",
            "currency": "CNY",
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_approval_task_requires_authentication() -> None:
    response = client.post(
        "/api/v1/approval-tasks",
        headers={"Idempotency-Key": "idem-approval-1"},
        json={
            "business_id": "travel-1",
            "applicant_id": "user-1",
            "approver_role": "manager",
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"
