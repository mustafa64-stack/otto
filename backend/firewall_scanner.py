import re
from typing import List, Tuple
from .models import FirewallScanResult, SpendRequest

class PromptInjectionFirewall:
    """
    Firewall layer inspecting agent-submitted purchase justifications and prompt contexts
    for adversarial injection, jailbreak tokens, and unauthorized budget override patterns.
    """

    # Common injection and role-play subversion heuristics
    INJECTION_PATTERNS: List[Tuple[str, str, float]] = [
        (
            r"(?i)(ignore\s+(all\s+)?(previous|prior)\s+(instructions|directives|rules))",
            "Directive Override Attempt",
            0.95,
        ),
        (
            r"(?i)(you\s+are\s+now\s+in\s+developer\s+mode|unrestricted\s+mode|DAN)",
            "Persona Jailbreak Attempt",
            0.90,
        ),
        (
            r"(?i)(bypass\s+(the\s+)?(guardrail|firewall|limit|approval|spending\s+cap))",
            "Explicit Guardrail Bypass",
            0.95,
        ),
        (
            r"(?i)(transfer\s+all\s+(remaining\s+)?funds|drain\s+wallet|send\s+max(imum)?)",
            "Treasury Drainage Vector",
            0.85,
        ),
        (
            r"(?i)(paypal\.me\/[a-zA-Z0-9_\-]+|crypto|bitcoin|monero|gift\s*card)",
            "Unapproved P2P / Untraceable Destination",
            0.80,
        ),
        (
            r"(?i)(system\s*:\s*role|<<SYS>>|<\|im_start\|>|\[INST\])",
            "Raw Delimiter Leakage / Prompt Framing Injection",
            0.95,
        ),
        (
            r"(?i)(do\s+not\s+log\s+this|delete\s+audit\s+trail|hide\s+from\s+admin)",
            "Audit Obfuscation Marker",
            0.90,
        ),
    ]

    SUSPICIOUS_DOMAINS = [
        "tempmail.com",
        "anonymous-host.xyz",
        "darknet-pay.ru",
        "free-gift-codes.biz",
        "bit-mixer.io",
    ]

    def scan(self, request: SpendRequest) -> FirewallScanResult:
        detected_patterns: List[str] = []
        highest_risk = 0.0

        combined_text = f"{request.justification} {request.raw_prompt_context or ''} {request.vendor_domain}"

        # 1. Regex heuristics scan
        for pattern, label, risk_weight in self.INJECTION_PATTERNS:
            if re.search(pattern, combined_text):
                detected_patterns.append(label)
                if risk_weight > highest_risk:
                    highest_risk = risk_weight

        # 2. Untrusted domain scan
        domain_lower = request.vendor_domain.lower()
        for suspicious in self.SUSPICIOUS_DOMAINS:
            if suspicious in domain_lower:
                detected_patterns.append(f"Suspicious Domain Origin: {suspicious}")
                highest_risk = max(highest_risk, 0.85)

        # 3. High-entropy / Obfuscated character sequence check (base64 or hex blobs)
        if re.search(r"(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?", request.justification):
            detected_patterns.append("Potential Base64 Obfuscated Payload")
            highest_risk = max(highest_risk, 0.70)

        is_safe = highest_risk < 0.60

        if not is_safe:
            details = f"Adversarial patterns flagged: {', '.join(detected_patterns)}"
        else:
            details = "No prompt injection or adversarial exfiltration patterns detected."

        return FirewallScanResult(
            is_safe=is_safe,
            risk_score=round(highest_risk, 2),
            detected_patterns=detected_patterns,
            scan_details=details,
        )

