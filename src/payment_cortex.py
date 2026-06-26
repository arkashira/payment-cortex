import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

class PaymentCortex:
    @dataclass
    class Transaction:
        message_type: str
        amount: float
        sender: str
        recipient: str

    def __init__(self):
        self.audit_logs = []
        self.settlement_networks = {
            "SWIFT": self.process_swift,
            "SEPA": self.process_sepa
        }

    def validate_message(self, message: Dict) -> bool:
        if message["type"] not in ["SWIFT_MT103", "SEPA_Credit_Transfer"]:
            return False
        if message["amount"] <= 0:
            return False
        return True

    def process_swift(self, transaction: 'PaymentCortex.Transaction'):
        # Simulate processing SWIFT transaction
        return f"SWIFT transaction processed: {transaction.amount} from {transaction.sender} to {transaction.recipient}"

    def process_sepa(self, transaction: 'PaymentCortex.Transaction'):
        # Simulate processing SEPA transaction
        return f"SEPA transaction processed: {transaction.amount} from {transaction.sender} to {transaction.recipient}"

    def route_transaction(self, message: Dict) -> str:
        if not self.validate_message(message):
            raise ValueError("Invalid message")
        transaction = PaymentCortex.Transaction(
            message_type=message["type"],
            amount=message["amount"],
            sender=message["sender"],
            recipient=message["recipient"]
        )
        if message["type"] == "SWIFT_MT103":
            return self.settlement_networks["SWIFT"](transaction)
        elif message["type"] == "SEPA_Credit_Transfer":
            return self.settlement_networks["SEPA"](transaction)

    def persist_audit_log(self, message: Dict, result: str):
        self.audit_logs.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "result": result
        })

    def process_message(self, message: Dict) -> str:
        try:
            result = self.route_transaction(message)
            self.persist_audit_log(message, result)
            return result
        except Exception as e:
            self.persist_audit_log(message, str(e))
            raise
