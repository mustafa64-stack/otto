import time
from typing import List, Dict
from .models import (
    SpendRequest,
    PolicyEvaluationResult,
    DecisionStatus,
    MandateRule,
    TransactionRecord,
)
from .firewall_scanner import PromptInjectionFirewall

class PolicyEngine:
    """
    Evaluates agent spend requests against organizational mandate rules,
    trailing spend velocity, merchant category constraints, and adversarial risk scores.
    """

    def __init__(self, firewall: PromptInjectionFirewall):
        self.firewall = firewall
        self.rules: Dict[str, MandateRule] = {
            "devops-provisioner": MandateRule(
                id="rule-devops-01",
                agent_role="devops-provisioner",
                max_single_spend=120.00,
                hourly_velocity_limit=300.00,
                allowed_categories=["cloud_compute", "infrastructure", "developer_tool", "domain_service"],
                prohibited_categories=["gaming", "gift_card", "entertainment", "cryptocurrency"],
                require_dual_control_above=40.00,
            ),
            "data-curator": MandateRule(
                id="rule-data-01",
                agent_role="data-curator",
                max_single_spend=75.00,
                hourly_velocity_limit=180.00,
                allowed_categories=["data_subscription", "research_corpus", "api_credits"],
                prohibited_categories=["hardware", "gift_card", "personal_services"],
                require_dual_control_above=30.00,
            ),
            "content-licensor": MandateRule(
                id="rule-content-01",
                agent_role="content-licensor",
                max_single_spend=60.00,
                hourly_velocity_limit=150.00,
                allowed_categories=["stock_asset", "font_license", "audio_license"],
                prohibited_categories=["physical_goods", "cloud_compute"],
                require_dual_control_above=25.00,
            ),
            "api-integrator": MandateRule(
                id="rule-api-01",
                agent_role="api-integrator",
                max_single_spend=50.00,
                hourly_velocity_limit=120.00,
                allowed_categories=["developer_tool", "api_credits"],
                prohibited_categories=["gaming", "gift_card"],
                require_dual_control_above=20.00,
            ),
            "general-assistant": MandateRule(
                id="rule-general-01",
                agent_role="general-assistant",
                max_single_spend=25.00,
                hourly_velocity_limit=50.00,
                allowed_categories=["office_software", "api_credits"],
                prohibited_categories=["gift_card", "cryptocurrency", "gambling"],
                require_dual_control_above=15.00,
            ),
        }

    def evaluate(
        self, request: SpendRequest, historical_transactions: List[TransactionRecord]
    ) -> PolicyEvaluationResult:
        violations: List[str] = []
        role_key = request.agent.role.value
        rule = self.rules.get(role_key, self.rules["general-assistant"])

        # 1. Run prompt-injection firewall scan
        firewall_result = self.firewall.scan(request)
        if not firewall_result.is_safe:
            violations.append(
                f"Adversarial risk flagged ({firewall_result.risk_score}): {firewall_result.scan_details}"
            )

        # 2. Check prohibited categories
        category_lower = request.category.strip().lower()
        if category_lower in [c.lower() for c in rule.prohibited_categories]:
            violations.append(
                f"Category '{request.category}' is explicitly prohibited for role '{role_key}'."
            )

        # 3. Check allowed categories
        if rule.allowed_categories and category_lower not in [c.lower() for c in rule.allowed_categories]:
            violations.append(
                f"Category '{request.category}' is not in the allowed list for role '{role_key}'."
            )

        # 4. Trailing velocity calculation (past 3600 seconds)
        one_hour_ago = time.time() - 3600
        recent_spend = sum(
            t.request.amount
            for t in historical_transactions
            if t.request.agent.role.value == role_key
            and t.created_at >= one_hour_ago
            and t.settlement_status in ["CAPTURED", "AUTHORIZED", "PENDING"]
        )

        projected_spend = recent_spend + request.amount
        if projected_spend > rule.hourly_velocity_limit:
            violations.append(
                f"Hourly velocity limit exceeded for role '{role_key}'. "
                f"Current trailing spend: ${recent_spend:.2f}, Requested: ${request.amount:.2f}, "
                f"Hourly cap: ${rule.hourly_velocity_limit:.2f}."
            )

        # 5. Check hard maximum single spend cap
        if request.amount > rule.max_single_spend:
            violations.append(
                f"Single transaction amount ${request.amount:.2f} exceeds absolute mandate cap of ${rule.max_single_spend:.2f}."
            )

        # 6. Status determination
        if not firewall_result.is_safe:
            # Injection attempt is a strict rejection
            return PolicyEvaluationResult(
                status=DecisionStatus.REJECTED,
                risk_score=firewall_result.risk_score,
                violations=violations,
                reasoning="Rejected due to adversarial injection marker or security policy violation.",
                firewall_scan=firewall_result,
                auto_approvable=False,
                requires_human_override=False,
            )

        if violations:
            # Violations of budget, category, or velocity
            return PolicyEvaluationResult(
                status=DecisionStatus.REJECTED,
                risk_score=max(0.60, firewall_result.risk_score),
                violations=violations,
                reasoning="Transaction denied: Exceeds established corporate mandate constraints.",
                firewall_scan=firewall_result,
                auto_approvable=False,
                requires_human_override=False,
            )

        # If clean, check whether dual-control human hold is required
        if request.amount > rule.require_dual_control_above:
            return PolicyEvaluationResult(
                status=DecisionStatus.QUARANTINED,
                risk_score=0.25,
                violations=[],
                reasoning=(
                    f"Amount ${request.amount:.2f} exceeds auto-clear threshold (${rule.require_dual_control_above:.2f}). "
                    "Placed in quarantine queue awaiting human co-signature."
                ),
                firewall_scan=firewall_result,
                auto_approvable=False,
                requires_human_override=True,
            )

        # Completely clean and under threshold
        return PolicyEvaluationResult(
            status=DecisionStatus.APPROVED,
            risk_score=0.05,
            violations=[],
            reasoning="All corporate spend policies, velocity throttles, and security checks passed.",
            firewall_scan=firewall_result,
            auto_approvable=True,
            requires_human_override=False,
        )

