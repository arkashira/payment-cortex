import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

@dataclass
class KYCStatus:
    status: str
    expires_at: datetime

class PaymentCortex:
    def __init__(self, kyc_provider_url: str, cache: Dict[str, KYCStatus]):
        self.kyc_provider_url = kyc_provider_url
        self.cache = cache

    def get_kyc_status(self, customer_id: str) -> KYCStatus:
        if customer_id in self.cache:
            kyc_status = self.cache[customer_id]
            if kyc_status.expires_at > datetime.now():
                return kyc_status

        # Simulate REST API call to KYC provider
        kyc_status = KYCStatus("verified", datetime.now() + timedelta(hours=24))
        self.cache[customer_id] = kyc_status
        return kyc_status

    def validate_kyc(self, customer_id: str, transaction: Dict[str, str]) -> bool:
        kyc_status = self.get_kyc_status(customer_id)
        if kyc_status.status != "verified":
            raise ValueError("KYC status is not verified")
        return True

    def process_transaction(self, customer_id: str, transaction: Dict[str, str]) -> bool:
        try:
            self.validate_kyc(customer_id, transaction)
            return True
        except ValueError as e:
            print(f"Error: {e}")
            return False
