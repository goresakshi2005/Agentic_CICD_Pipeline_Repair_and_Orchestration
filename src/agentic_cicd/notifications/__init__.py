from .slack import SlackNotifier
from ..config import settings

def get_notification_provider():
    if settings.slack_token:
        return SlackNotifier(settings.slack_token, settings.slack_channel)
    return None