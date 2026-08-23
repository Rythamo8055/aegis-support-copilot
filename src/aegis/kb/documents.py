KB_DOCS = [
    {
        "id": "KB-001",
        "title": "Duplicate charge refund policy",
        "text": (
            "If a customer is charged twice for the same subscription in one billing cycle, "
            "agents must verify both transactions in the billing console, then issue a full refund "
            "for the duplicate within 2 business days. Refunds above $500 require supervisor approval. "
            "Always confirm the refunded amount to the customer in writing."
        ),
    },
    {
        "id": "KB-002",
        "title": "Refund processing timelines",
        "text": (
            "Standard refunds take 5-7 business days to appear on the customer's card. "
            "UPI and wallet refunds complete within 24 hours. If a refund has not appeared after "
            "10 business days, escalate to the payments team with the transaction ID."
        ),
    },
    {
        "id": "KB-003",
        "title": "Chargeback and dispute handling",
        "text": (
            "When a customer threatens or initiates a bank dispute, do not promise outcomes. "
            "Collect the transaction ID, timestamp, and amount; file an internal dispute ticket tagged "
            "'chargeback-risk' within 1 hour so the payments team can respond before the bank deadline."
        ),
    },
    {
        "id": "KB-004",
        "title": "Password reset procedure",
        "text": (
            "Send the self-service password reset link from the admin console after verifying identity "
            "with two of: registered email, phone OTP, last transaction amount. Never reset passwords "
            "for accounts flagged with recent login anomalies; route those to security."
        ),
    },
    {
        "id": "KB-005",
        "title": "Account deletion requests",
        "text": (
            "Customers may request full account deletion. Verify identity, export their data per policy, "
            "and schedule deletion after 7 days grace period. Active subscriptions must be cancelled first; "
            "outstanding balances block deletion until settled."
        ),
    },
    {
        "id": "KB-006",
        "title": "App crash on startup troubleshooting",
        "text": (
            "For app crashing on launch: 1) confirm OS and app version, 2) ask user to clear cache and "
            "reinstall, 3) if version is older than 2 releases, update first. Collect crash logs via "
            "Settings > Send diagnostics. Unresolved crashes on latest version go to mobile squad with logs attached."
        ),
    },
    {
        "id": "KB-007",
        "title": "Payment failure troubleshooting",
        "text": (
            "Common payment failures: insufficient limit, bank OTP timeout, expired card, or 3DS challenge failure. "
            "Ask the customer to retry once after checking card validity. Repeated failures with valid cards "
            "should be checked against the payment gateway status page before escalating."
        ),
    },
    {
        "id": "KB-008",
        "title": "Subscription cancellation policy",
        "text": (
            "Customers can cancel anytime from Settings > Subscription. Access continues until period end; "
            "no prorated refunds except where local law requires. Offer retention discount only once per year."
        ),
    },
    {
        "id": "KB-009",
        "title": "Data breach report handling",
        "text": (
            "Any report of exposed personal data is a security incident. Do not investigate yourself. "
            "Capture what the customer saw, notify the security on-call immediately, and classify the ticket "
            "as critical. Response SLA is 30 minutes."
        ),
    },
    {
        "id": "KB-010",
        "title": "Escalation matrix",
        "text": (
            "Escalate to: billing team for refunds above agent limits; security for suspected fraud or breaches; "
            "legal for regulatory threats or court notices; engineering on-call for outages affecting multiple customers. "
            "All angry-customer tickets older than 24 hours auto-escalate to shift lead."
        ),
    },
    {
        "id": "KB-011",
        "title": "Angry customer de-escalation script",
        "text": (
            "Acknowledge the frustration, apologize once without admitting fault, restate the issue in your own words, "
            "and give a concrete next step with a time commitment. Avoid scripted repetition; offer callback if hold exceeds 5 minutes."
        ),
    },
    {
        "id": "KB-012",
        "title": "Invoice and billing statement access",
        "text": (
            "Customers can download invoices for any period from Settings > Billing > History. "
            "GST-compliant invoices are generated within 1 hour of successful payment. Agents can email "
            "copies manually for payments older than 12 months."
        ),
    },
]
