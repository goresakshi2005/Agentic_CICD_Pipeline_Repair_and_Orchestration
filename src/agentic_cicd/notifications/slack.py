from slack_sdk.web.async_client import AsyncWebClient
from ..core.interfaces import NotificationProvider

class SlackNotifier(NotificationProvider):
    def __init__(self, token: str, channel: str):
        self.client = AsyncWebClient(token=token)
        self.channel = channel

    async def send_approval_request(self, run_id: str, diagnosis: dict, fix_plan: dict = None):
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Approval Required for Run #{run_id}*"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Root Cause:* {diagnosis.get('root_cause', 'N/A')}\n"
                            f"*Confidence:* {diagnosis.get('confidence', 0.0)}\n"
                            f"*Fix Type:* {diagnosis.get('suggested_fix_type', 'unknown')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "value": f"approve_{run_id}",
                        "action_id": "approve_run"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "value": f"reject_{run_id}",
                        "action_id": "reject_run"
                    }
                ]
            }
        ]
        await self.client.chat_postMessage(channel=self.channel, blocks=blocks)