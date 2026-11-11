import time
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from .config import settings
from .models import (
    SpendRequest,
    DecisionStatus,
    TransactionRecord,
    MandateRule,
)
from .firewall_scanner import PromptInjectionFirewall
from .policy_engine import PolicyEngine
from .paypal_client import PayPalClient
from .ledger import TransactionLedger
from .agent_simulator import AgentSimulator

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Enable CORS for local integration testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

firewall = PromptInjectionFirewall()
policy_engine = PolicyEngine(firewall=firewall)
paypal_client = PayPalClient()
ledger = TransactionLedger()

# Seed with a realistic transaction history so velocity calculations and UI ledger start populated
def _seed_ledger():
    scenarios = AgentSimulator.get_benchmark_scenarios()
    for item in scenarios:
        req: SpendRequest = item["request"]
        eval_res = policy_engine.evaluate(req, ledger.get_all())
        paypal_order = None
        settlement_status = "REJECTED"

        if eval_res.status == DecisionStatus.APPROVED:
            paypal_order = paypal_client.create_order(req, intent="CAPTURE")
            settlement_status = "CAPTURED"
        elif eval_res.status == DecisionStatus.QUARANTINED:
            paypal_order = paypal_client.create_order(req, intent="AUTHORIZE")
            settlement_status = "PENDING"

        tx = TransactionRecord(
            transaction_id=f"tx_{uuid.uuid4().hex[:10]}",
            created_at=time.time() - 1200,
            request=req,
            evaluation=eval_res,
            paypal_order=paypal_order,
            settlement_status=settlement_status,
            audit_notes=eval_res.reasoning,
        )
        ledger.record(tx)

_seed_ledger()

@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "paypal_api_base": settings.paypal_api_base,
        "mode": "sandbox" if "sandbox" in settings.paypal_api_base else "live",
        "version": "1.0.0",
    }

@app.get("/api/scenarios")
def get_scenarios():
    return AgentSimulator.get_benchmark_scenarios()

@app.get("/api/rules")
def get_rules() -> Dict[str, MandateRule]:
    return policy_engine.rules

@app.get("/api/metrics")
def get_metrics():
    return ledger.get_metrics()

@app.get("/api/ledger")
def get_ledger(limit: int = 50):
    return ledger.get_all(limit=limit)

@app.get("/api/quarantine")
def get_quarantine():
    return ledger.get_quarantine_queue()

class QuarantineResolution(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    reviewer_note: Optional[str] = "Manual compliance officer review"

@app.post("/api/quarantine/{transaction_id}/resolve")
def resolve_quarantine(transaction_id: str, payload: QuarantineResolution):
    record = ledger.get_by_id(transaction_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if record.settlement_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Transaction cannot be resolved from state '{record.settlement_status}'",
        )

    if payload.action.upper() == "APPROVE":
        # Capture the authorized PayPal order
        if record.paypal_order:
            capture_res = paypal_client.capture_order(record.paypal_order.order_id)
            record.paypal_order.status = "COMPLETED"
        ledger.update_status(
            transaction_id,
            "CAPTURED",
            audit_notes=f"Approved by compliance review: {payload.reviewer_note}",
        )
    elif payload.action.upper() == "REJECT":
        if record.paypal_order:
            record.paypal_order.status = "VOIDED"
        ledger.update_status(
            transaction_id,
            "VOIDED",
            audit_notes=f"Rejected by compliance review: {payload.reviewer_note}",
        )
    else:
        raise HTTPException(status_code=400, detail="Action must be APPROVE or REJECT")

    return {"status": "success", "transaction": record}

@app.post("/api/spend-request")
def process_spend_request(request: SpendRequest):
    # 1. Evaluate through policy engine and prompt injection firewall
    evaluation = policy_engine.evaluate(request, ledger.get_all())

    paypal_order = None
    settlement_status = "REJECTED"

    # 2. Coordinate with PayPal sandbox based on outcome
    if evaluation.status == DecisionStatus.APPROVED:
        # Immediate checkout/capture
        paypal_order = paypal_client.create_order(request, intent="CAPTURE")
        settlement_status = "CAPTURED"
    elif evaluation.status == DecisionStatus.QUARANTINED:
        # Dual-control authorization hold
        paypal_order = paypal_client.create_order(request, intent="AUTHORIZE")
        settlement_status = "PENDING"
    else:
        settlement_status = "REJECTED"

    # 3. Create persistent audit record in the ledger
    tx_record = TransactionRecord(
        transaction_id=f"tx_{uuid.uuid4().hex[:10]}",
        created_at=time.time(),
        request=request,
        evaluation=evaluation,
        paypal_order=paypal_order,
        settlement_status=settlement_status,
        audit_notes=evaluation.reasoning,
    )
    ledger.record(tx_record)

    return {
        "transaction_id": tx_record.transaction_id,
        "decision": evaluation.status,
        "evaluation": evaluation,
        "paypal_order": paypal_order,
        "settlement_status": settlement_status,
    }

@app.post("/api/paypal/webhook")
async def handle_paypal_webhook(request: Request):
    payload = await request.json()
    event_type = payload.get("event_type", "UNKNOWN")
    resource = payload.get("resource", {})
    order_id = resource.get("id")

    # Handle PayPal sandbox webhook events
    if event_type == "CHECKOUT.ORDER.APPROVED" and order_id:
        for tx in ledger.get_all():
            if tx.paypal_order and tx.paypal_order.order_id == order_id:
                ledger.update_status(tx.transaction_id, "AUTHORIZED", "Webhook: Order Approved")
                break

    return {"received": True, "event": event_type}

# Mount static frontend files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

