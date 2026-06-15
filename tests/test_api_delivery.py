from typing import Generator
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Fixture providing a managed TestClient that cleanly executes app lifecycle hooks."""
    # Using 'with' guarantees that the FastAPI lifespan startup/shutdown code runs!
    with TestClient(app) as test_client:
        yield test_client


def test_api_root_landing_endpoint(client: TestClient) -> None:
    """Verifies that the public landing gateway responds with an operational status code."""
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ONLINE"
    assert "Structured Concurrency" in json_data["concurrency_model"]


def test_api_order_creation_enforces_tenant_header(client: TestClient) -> None:
    """Guarantees that the delivery layer blocks requests missing the security tenant identifier."""
    payload = {"user_id": "usr_dev_10", "amount": 99.99}
    
    # Send request without the X-Tenant-ID header
    response = client.post("/orders", json=payload)
    
    # FastAPI automatically intercepts missing headers and drops a 422 Unprocessable Entity
    assert response.status_code == 422


def test_api_order_e2e_pipeline_and_tenant_isolation(client: TestClient) -> None:
    """Tests the full transaction pipeline and verifies absolute data isolation between separate tenants."""
    payload = {"user_id": "customer_alpha", "amount": 250.00}
    headers_alpha = {"X-Tenant-ID": "tenant_alpha"}
    headers_beta = {"X-Tenant-ID": "tenant_beta"}

    # 1. Create the order under Tenant Alpha
    create_response = client.post("/orders", json=payload, headers=headers_alpha)
    assert create_response.status_code == 200
    
    order_data = create_response.json()["data"]
    order_id = order_data["id"]
    assert order_data["user_id"] == "customer_alpha"

    # 2. Assert Tenant Alpha can look up and read their own order successfully
    read_ok_response = client.get(f"/orders/{order_id}", headers=headers_alpha)
    assert read_ok_response.status_code == 200
    assert read_ok_response.json()["data"]["id"] == order_id

    # 3. ACID SECURITY TEST: Verify Tenant Beta receives a 404 Not Found if they try to look up Alpha's order ID
    read_isolated_response = client.get(f"/orders/{order_id}", headers=headers_beta)
    assert read_isolated_response.status_code == 404


def test_api_billing_invoice_e2e_workflow(client: TestClient) -> None:
    """Verifies that the new billing domain endpoints process invoice creation and payments smoothly."""
    invoice_payload = {"order_id": "ord_mock_77", "amount": 1420.00}
    headers = {"X-Tenant-ID": "tenant_gamma"}

    # 1. Create an Unpaid Invoice
    invoice_response = client.post("/billing/invoices", json=invoice_payload, headers=headers)
    assert invoice_response.status_code == 200
    
    invoice_data = invoice_response.json()
    assert invoice_data["status"] == "CREATED"
    invoice_id = invoice_data["invoice_id"]
    assert invoice_data["state"] == "UNPAID"

    # 2. Settle the Invoice balance via the pay endpoint
    pay_response = client.post(f"/billing/invoices/{invoice_id}/pay", headers=headers)
    assert pay_response.status_code == 200
    assert pay_response.json()["current_state"] == "PAID"