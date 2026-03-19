class SlackNotifier:
    def __init__(self, webhook: str = None):
        self.webhook = webhook

    def notify(self, message: str):
        return {"ok": bool(self.webhook)}
