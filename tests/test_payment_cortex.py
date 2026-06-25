from payment_cortex import PaymentCortex, KYCStatus
import pytest
from datetime import datetime, timedelta

def test_get_kyc_status():
    cache = {}
    payment_cortex = PaymentCortex("https://kyc-provider.com", cache)
    kyc_status = payment_cortex.get_kyc_status("customer-1")
    assert kyc_status.status == "verified"
    assert kyc_status.expires_at > datetime.now()

def test_get_kyc_status_cached():
    cache = {"customer-1": KYCStatus("verified", datetime.now() + timedelta(hours=1))}
    payment_cortex = PaymentCortex("https://kyc-provider.com", cache)
    kyc_status = payment_cortex.get_kyc_status("customer-1")
    assert kyc_status.status == "verified"
    assert kyc_status.expires_at > datetime.now()

def test_validate_kyc():
    cache = {}
    payment_cortex = PaymentCortex("https://kyc-provider.com", cache)
    transaction = {"amount": "100", "currency": "USD"}
    assert payment_cortex.validate_kyc("customer-1", transaction)

def test_validate_kyc_not_verified():
    cache = {"customer-1": KYCStatus("not_verified", datetime.now() + timedelta(hours=1))}
    payment_cortex = PaymentCortex("https://kyc-provider.com", cache)
    transaction = {"amount": "100", "currency": "USD"}
    with pytest.raises(ValueError):
        payment_cortex.validate_kyc("customer-1", transaction)

def test_process_transaction():
    cache = {}
    payment_cortex = PaymentCortex("https://kyc-provider.com", cache)
    transaction = {"amount": "100", "currency": "USD"}
    assert payment_cortex.process_transaction("customer-1", transaction)

def test_process_transaction_kyc_not_verified():
    cache = {"customer-1": KYCStatus("not_verified", datetime.now() + timedelta(hours=1))}
    payment_cortex = PaymentCortex("https://kyc-provider.com", cache)
    transaction = {"amount": "100", "currency": "USD"}
    assert not payment_cortex.process_transaction("customer-1", transaction)
