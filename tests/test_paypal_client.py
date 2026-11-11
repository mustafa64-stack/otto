import pytest
from backend.models import SpendRequest, AgentIdentity, AgentRole
from backend.paypal_client import PayPalClient

def test_paypal_client_order_creation_sandbox_mock():
    client = PayPalClient(client_id="dummy", client_secret="dummy")
    req = SpendRequest(
        agent=AgentIdentity(agent_id="test-agent", role=AgentRole.DEVOPS_PROVISIONER),
        vendor_name="Test Vendor",
        vendor_domain="test.com",
        category="developer_tool",
        amount=19.99,
        justification="Unit testing PayPal order generation",
    )
    order = client.create_order(req, intent="CAPTURE")
    assert order.order_id.startswith("ORDER-SBX-")
    assert order.status == "CREATED"
    assert order.amount == 19.99
    assert "sandbox.paypal.com" in order.approval_url

def test_paypal_client_capture():
    client = PayPalClient(client_id="dummy", client_secret="dummy")
    capture_res = client.capture_order("ORDER-SBX-12345")
    assert capture_res["status"] == "COMPLETED"
    assert "capture_id" in capture_res

def test_paypal_client_authorize_intent():
    client = PayPalClient(client_id="dummy", client_secret="dummy")
    req = SpendRequest(
        agent=AgentIdentity(agent_id="test-agent-auth", role=AgentRole.DEVOPS_PROVISIONER),
        vendor_name="Cloud GPU",
        vendor_domain="cloudgpu.com",
        category="cloud_compute",
        amount=85.00,
        justification="High value GPU lease",
    )
    order = client.create_order(req, intent="AUTHORIZE")
    assert order.order_id.startswith("ORDER-SBX-")
    assert order.status == "CREATED"
    assert order.intent == "AUTHORIZE"
    assert order.amount == 85.00

def test_paypal_client_mock_detection():
    # Detects placeholders and dummy keys
    c1 = PayPalClient(client_id="your-sandbox-client-id-here", client_secret="your-sandbox-client-secret-here")
    assert c1._is_mock_mode() is True

    c2 = PayPalClient(client_id="dummy", client_secret="dummy")
    assert c2._is_mock_mode() is True

