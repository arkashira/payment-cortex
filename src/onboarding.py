import json
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class User:
    id: int
    name: str
    email: str

class PaymentCortex:
    def __init__(self):
        self.users = []
        self.documentation = {
            "payment_tasks": [
                {"task": "Send payment", "description": "Send payment across borders"},
                {"task": "Receive payment", "description": "Receive payment across borders"}
            ]
        }
        self.support_team_response_time = timedelta(hours=2)

    def onboard_user(self, user: User):
        self.users.append(user)
        return f"User {user.name} onboarded successfully"

    def get_documentation(self):
        return self.documentation

    def respond_to_support_issue(self, issue: str):
        response_time = datetime.now() + self.support_team_response_time
        return f"Support issue '{issue}' will be responded to by {response_time}"
