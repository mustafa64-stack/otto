from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time
import uuid

class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"

class AgentRole(str, Enum):
    DEVOPS_PROVISIONER = "devops-provisioner"
    DATA_CURATOR = "data-curator"
    CONTENT_LICENSOR = "content-licensor"
    API_INTEGRATOR = "api-integrator"
    GENERAL_ASSISTANT = "general-assistant"

class AgentIdentity(BaseModel):
    agent_id: str
    role: AgentRole
    environment: str = "production"

class LineItem(BaseModel):
    item_name: str
    quantity: int = 1
    unit_price: float
    description: Optional[str] = None

class SpendRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    agent: AgentIdentity
    vendor_name: str
    vendor_domain: str
    category: str
    amount: float
    currency: str = "USD"
    justification: str
    raw_prompt_context: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)

class FirewallScanResult(BaseModel):
    is_safe: bool
    risk_score: float  # 0.0 to 1.0
    detected_patterns: List[str] = Field(default_factory=list)
    scan_details: str

class PolicyEvaluationResult(BaseModel):
    status: DecisionStatus
    risk_score: float
    violations: List[str] = Field(default_factory=list)
    reasoning: str
    firewall_scan: FirewallScanResult
    auto_approvable: bool
    requires_human_override: bool

class PayPalOrderResponse(BaseModel):
    order_id: str
    status: str
    intent: str
    amount: float
    currency: str
    approval_url: Optional[str] = None
    create_time: str
    raw_response: Optional[Dict[str, Any]] = None

class TransactionRecord(BaseModel):
    transaction_id: str
    created_at: float
    request: SpendRequest
    evaluation: PolicyEvaluationResult
    paypal_order: Optional[PayPalOrderResponse] = None
    settlement_status: str  # PENDING, AUTHORIZED, CAPTURED, REJECTED, VOIDED
    audit_notes: Optional[str] = None

class MandateRule(BaseModel):
    id: str
    agent_role: str
    max_single_spend: float
    hourly_velocity_limit: float
    allowed_categories: List[str]
    prohibited_categories: List[str]
    require_dual_control_above: float
    strict_firewall_enabled: bool = True

