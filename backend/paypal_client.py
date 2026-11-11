import base64
import time
import uuid
from typing import Dict, Any, Optional
import requests
from .config import settings
from .models import SpendRequest, PayPalOrderResponse

class PayPalClient:
    """
    Client for interacting with the PayPal Orders v2 REST API in Sandbox.
    Handles token authentication, order creation with capture/authorize intents,
    and payment settlement.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.client_id = client_id or settings.paypal_client_id
        self.client_secret = client_secret or settings.paypal_client_secret
        self.api_base = api_base or settings.paypal_api_base
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0

    def _is_mock_mode(self) -> bool:
        """Determines if default dummy keys are used or live sandbox credentials."""
        if not self.client_id or not self.client_secret:
            return True
        lowered_id = self.client_id.lower()
        lowered_sec = self.client_secret.lower()
        return (
            "dummy" in lowered_id
            or "dummy" in lowered_sec
            or "your-sandbox" in lowered_id
            or "your-sandbox" in lowered_sec
            or "placeholder" in lowered_id
            or "placeholder" in lowered_sec
        )

    def get_access_token(self) -> str:
        """Retrieves an OAuth2 access token from PayPal Sandbox."""
        if self._is_mock_mode():
            return "MOCK_SANDBOX_ACCESS_TOKEN"

        if self._cached_token and time.time() < self._token_expiry:
            return self._cached_token

        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        ).decode("utf-8")

        response = requests.post(
            f"{self.api_base}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        self._cached_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
        return self._cached_token

    def create_order(
        self, request: SpendRequest, intent: str = "CAPTURE"
    ) -> PayPalOrderResponse:
        """Creates an order in PayPal Sandbox using Orders v2 API."""
        if self._is_mock_mode():
            mock_order_id = f"ORDER-SBX-{uuid.uuid4().hex[:10].upper()}"
            return PayPalOrderResponse(
                order_id=mock_order_id,
                status="CREATED",
                intent=intent,
                amount=request.amount,
                currency=request.currency,
                approval_url=f"https://www.sandbox.paypal.com/checkoutnow?token={mock_order_id}",
                create_time=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                raw_response={"mock": True, "id": mock_order_id, "intent": intent},
            )

        token = self.get_access_token()
        purchase_unit: Dict[str, Any] = {
            "reference_id": request.request_id,
            "description": f"Agent {request.agent.agent_id}: {request.justification[:100]}",
            "custom_id": request.agent.agent_id,
            "amount": {
                "currency_code": request.currency,
                "value": f"{request.amount:.2f}",
            },
        }

        payload: Dict[str, Any] = {
            "intent": intent,
            "purchase_units": [purchase_unit],
            "application_context": {
                "brand_name": "Otto Financial Gateway",
                "landing_page": "NO_PREFERENCE",
                "user_action": "PAY_NOW",
                "return_url": "http://localhost:8000/api/paypal/return",
                "cancel_url": "http://localhost:8000/api/paypal/cancel",
            },
        }

        response = requests.post(
            f"{self.api_base}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        approval_link = None
        for link in data.get("links", []):
            if link.get("rel") == "approve":
                approval_link = link.get("href")

        return PayPalOrderResponse(
            order_id=data["id"],
            status=data.get("status", "CREATED"),
            intent=intent,
            amount=request.amount,
            currency=request.currency,
            approval_url=approval_link,
            create_time=data.get("create_time", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
            raw_response=data,
        )

    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Captures payment for an approved order."""
        if self._is_mock_mode():
            return {
                "id": order_id,
                "status": "COMPLETED",
                "capture_id": f"CAP-{uuid.uuid4().hex[:8].upper()}",
                "simulated": True,
            }

        token = self.get_access_token()
        response = requests.post(
            f"{self.api_base}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

