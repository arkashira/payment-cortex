from onboarding import PaymentCortex, User

def test_onboard_user():
    payment_cortex = PaymentCortex()
    user = User(1, "John Doe", "john@example.com")
    result = payment_cortex.onboard_user(user)
    assert result == "User John Doe onboarded successfully"

def test_get_documentation():
    payment_cortex = PaymentCortex()
    documentation = payment_cortex.get_documentation()
    assert len(documentation["payment_tasks"]) == 2
    assert documentation["payment_tasks"][0]["task"] == "Send payment"

def test_respond_to_support_issue():
    payment_cortex = PaymentCortex()
    issue = "Payment not received"
    response = payment_cortex.respond_to_support_issue(issue)
    assert issue in response

def test_onboard_user_edge_case():
    payment_cortex = PaymentCortex()
    user = User(1, "", "john@example.com")
    result = payment_cortex.onboard_user(user)
    assert result == "User  onboarded successfully"

def test_get_documentation_edge_case():
    payment_cortex = PaymentCortex()
    payment_cortex.documentation = {}
    documentation = payment_cortex.get_documentation()
    assert documentation == {}

def test_respond_to_support_issue_edge_case():
    payment_cortex = PaymentCortex()
    issue = ""
    response = payment_cortex.respond_to_support_issue(issue)
    assert issue in response
