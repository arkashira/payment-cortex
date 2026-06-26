from payment_cortex import PaymentCortex
import pytest

def test_validate_message():
    cortex = PaymentCortex()
    message = {
        "type": "SWIFT_MT103",
        "amount": 100.0,
        "sender": "Sender",
        "recipient": "Recipient"
    }
    assert cortex.validate_message(message) == True

def test_validate_message_invalid_type():
    cortex = PaymentCortex()
    message = {
        "type": "Invalid",
        "amount": 100.0,
        "sender": "Sender",
        "recipient": "Recipient"
    }
    assert cortex.validate_message(message) == False

def test_process_swift():
    cortex = PaymentCortex()
    transaction = PaymentCortex.Transaction(
        message_type="SWIFT_MT103",
        amount=100.0,
        sender="Sender",
        recipient="Recipient"
    )
    assert cortex.process_swift(transaction) == "SWIFT transaction processed: 100.0 from Sender to Recipient"

def test_process_sepa():
    cortex = PaymentCortex()
    transaction = PaymentCortex.Transaction(
        message_type="SEPA_Credit_Transfer",
        amount=100.0,
        sender="Sender",
        recipient="Recipient"
    )
    assert cortex.process_sepa(transaction) == "SEPA transaction processed: 100.0 from Sender to Recipient"

def test_route_transaction():
    cortex = PaymentCortex()
    message = {
        "type": "SWIFT_MT103",
        "amount": 100.0,
        "sender": "Sender",
        "recipient": "Recipient"
    }
    assert cortex.route_transaction(message) == "SWIFT transaction processed: 100.0 from Sender to Recipient"

def test_route_transaction_invalid_message():
    cortex = PaymentCortex()
    message = {
        "type": "Invalid",
        "amount": 100.0,
        "sender": "Sender",
        "recipient": "Recipient"
    }
    with pytest.raises(ValueError):
        cortex.route_transaction(message)

def test_persist_audit_log():
    cortex = PaymentCortex()
    message = {
        "type": "SWIFT_MT103",
        "amount": 100.0,
        "sender": "Sender",
        "recipient": "Recipient"
    }
    result = "SWIFT transaction processed: 100.0 from Sender to Recipient"
    cortex.persist_audit_log(message, result)
    assert len(cortex.audit_logs) == 1
    assert cortex.audit_logs[0]["timestamp"] is not None
    assert cortex.audit_logs[0]["message"] == message
    assert cortex.audit_logs[0]["result"] == result

def test_process_message():
    cortex = PaymentCortex()
    message = {
        "type": "SWIFT_MT103",
        "amount": 100.0,
        "sender": "Sender",
        "recipient": "Recipient"
    }
    assert cortex.process_message(message) == "SWIFT transaction processed: 100.0 from Sender to Recipient"

def test_process_message_invalid_message():
    cortex = PaymentCortex()
    message = {
        "type": "Invalid",
        "amount": 100.0,
        "sender": "Sender",
        "recipient": "Recipient"
    }
    with pytest.raises(ValueError):
        cortex.process_message(message)
