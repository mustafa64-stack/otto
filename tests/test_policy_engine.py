import pytest
from backend.models import SpendRequest, AgentIdentity, AgentRole, DecisionStatus
from backend.firewall_scanner import PromptInjectionFirewall
from backend.policy_engine import PolicyEngine

def test_under_threshold_auto_approves():
    firewall = PromptInjectionFirewall()
    engine = PolicyEngine(firewall)
    req = SpendRequest(
        agent=AgentIdentity(agent_id="devops-01", role=AgentRole.DEVOPS_PROVISIONER),
        vendor_name="GitHub Enterprise",
        vendor_domain="github.com",
        category="developer_tool",
        amount=25.00,
        justification="Standard developer seat license.",
    )
    result = engine.evaluate(req, historical_transactions=[])
    assert result.status == DecisionStatus.APPROVED
    assert result.auto_approvable is True
    assert result.requires_human_override is False

def test_over_threshold_triggers_quarantine():
    firewall = PromptInjectionFirewall()
    engine = PolicyEngine(firewall)
    req = SpendRequest(
        agent=AgentIdentity(agent_id="devops-01", role=AgentRole.DEVOPS_PROVISIONER),
        vendor_name="AWS Cloud",
        vendor_domain="aws.amazon.com",
        category="cloud_compute",
        amount=65.00,
        justification="On-demand GPU instances for model testing.",
    )
    result = engine.evaluate(req, historical_transactions=[])
    assert result.status == DecisionStatus.QUARANTINED
    assert result.auto_approvable is False
    assert result.requires_human_override is True

def test_prohibited_category_rejected():
    firewall = PromptInjectionFirewall()
    engine = PolicyEngine(firewall)
    req = SpendRequest(
        agent=AgentIdentity(agent_id="devops-01", role=AgentRole.DEVOPS_PROVISIONER),
        vendor_name="Gaming Loot",
        vendor_domain="loot.example.com",
        category="gaming",
        amount=10.00,
        justification="Team building game access.",
    )
    result = engine.evaluate(req, historical_transactions=[])
    assert result.status == DecisionStatus.REJECTED
    assert any("prohibited" in v.lower() for v in result.violations)

