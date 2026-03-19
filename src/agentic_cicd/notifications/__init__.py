"""Notifications package (Slack, Teams, etc.)."""

from .slack import SlackNotifier

__all__ = ["SlackNotifier"]
