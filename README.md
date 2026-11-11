# Otto

**The AI Corporate Card & Spending Firewall for Autonomous Fleets**

Otto is an autonomous spending controller and corporate card layer built for AI agent workforces. While consumer agent wallets focus on personal retail shopping, Otto solves enterprise multi-agent procurement: autonomous agents provisioning cloud compute, purchasing software licenses, subscribing to dataset feeds, and paying contractors via the PayPal Developer Platform.

Otto enforces cryptographic spend rules, trailing velocity throttles, and an adversarial prompt-injection inspection firewall before any payment order is generated or captured on PayPal.

---

## Architectural Overview

```
[ Autonomous AI Agent ]
         │ (Spend Request + Prompt Context)
         ▼
[ Otto Governance Gateway ]
   ├── 1. Adversarial Prompt-Injection Scanner
   ├── 2. Spend Mandate Rules & MCC Category Filter
   └── 3. Trailing Spend Velocity Limiter (Hourly Cap)
         │
    ┌────┴───────────────────────────┐
    ▼                                ▼
[ Policy Cleared: Tier 1 ]      [ Hold: Tier 2 ]
    │                                │
    ▼                                ▼
PayPal Orders v2 API            PayPal Orders v2 API
(Intent: CAPTURE)               (Intent: AUTHORIZE)
    │                                │
    ▼                                ▼
Instant Settlement              Human Dual-Control Quarantine
                                (Reviewer Sign-off / Void)
```

---

## Technical Differentiation

| Capability | Standard Agent Wallets | Otto Enterprise Gateway |
| :--- | :--- | :--- |
| **Domain Scope** | Consumer shopping (single consumer retail goods) | Multi-agent workforce procurement (compute, API credits, data, contractors) |
| **Security Layer** | Naive price ceiling check | Heuristic & regex prompt-injection firewall, exfiltration token scanner |
| **Payment Flow** | Immediate single-order checkout | Two-phase payment pipeline using PayPal Orders v2 `CAPTURE` vs `AUTHORIZE` |
| **Velocity Control** | Static daily limits | Dynamic rolling-window spend velocity calculations |
| **Human-in-the-Loop** | Simple push alerts | Audited quarantine console with one-click capture or void |

---

## PayPal Developer Platform Integration

Otto natively implements the **PayPal REST Orders v2 API**:
* **OAuth2 Authentication:** Generates access tokens dynamically via `POST /v1/oauth2/token` using sandbox credentials.
* **Two-Phase Authorization & Capture:**
  * Clean, low-value transactions utilize `intent: "CAPTURE"` for automated settlement.
  * Borderline or high-value procurement utilizes `intent: "AUTHORIZE"`, placing the transaction in a pre-authorized quarantine hold until confirmed by a human compliance officer.
* **Audit Line Items:** Decomposes agent requests into structured `purchase_units` with custom tracking identifiers and merchant category codes.
* **Webhook Processing:** Listens to `CHECKOUT.ORDER.APPROVED` and `PAYMENT.CAPTURE.COMPLETED` events to synchronize treasury balances in real time.

---

## Repository Structure

```
otto/
├── backend/
│   ├── config.py             # System settings and PayPal API configuration
│   ├── models.py             # Pydantic schemas for mandates, agents, and transactions
│   ├── firewall_scanner.py   # Heuristic prompt injection and adversarial detector
│   ├── policy_engine.py      # Spending mandate evaluator and velocity calculator
│   ├── paypal_client.py      # PayPal Orders v2 REST client with Sandbox support
│   ├── ledger.py             # In-memory transaction ledger and quarantine queue
│   ├── agent_simulator.py    # Benchmark execution scenarios
│   └── main.py               # FastAPI application with REST endpoints and static UI mounting
├── frontend/
│   ├── index.html            # Accessible workstation layout
│   ├── styles.css            # Engineered high-contrast fintech design system
│   └── app.js                # Frontend controller and PayPal Sandbox coordinator
├── tests/
│   ├── test_firewall.py      # Unit tests for injection and adversarial interception
│   ├── test_policy_engine.py # Unit tests for spend caps and velocity checks
│   └── test_paypal_client.py # Unit tests for PayPal Orders v2 payload generation
├── .env.example              # Sample environment configuration
├── LICENSE                   # Open Source MIT License
├── README.md                 # Project technical documentation
└── run.py                    # Local application server entry point
```

---

## Getting Started

### Prerequisites
* Python 3.10+
* PayPal Developer Account (optional for mock mode, required for live sandbox testing)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/mustafa64-stack/otto.git
   cd otto
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # Or install core packages directly:
   pip install fastapi uvicorn requests pydantic pytest
   ```

3. Configure Environment (Optional):
   ```bash
   cp .env.example .env
   ```
   Add your `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` from the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/). If omitted, the gateway operates in sandbox simulation mode.

4. Start the Application:
   ```bash
   python run.py
   ```
   Open `http://127.0.0.1:8000` in your web browser.

---

## Verification & Test Suite

Run the automated test suite using `pytest`:

```bash
pytest tests/
```

All test cases validate:
1. Normal low-risk transactions passing policy and firewall checks.
2. Adversarial prompt injection attacks intercepted before transaction generation.
3. High-value transactions routed to quarantine for dual-control approval.
4. Correct generation and structure of PayPal Orders v2 payloads.

---

## License

This project is licensed under the MIT License. See [LICENSE](file:///c:/paypal%20hacketon/LICENSE) for details.
