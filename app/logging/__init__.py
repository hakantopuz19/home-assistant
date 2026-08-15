"""Backward-compatible imports for the shared logger package."""

from logger import SYSTEM_LOGS, append_system_log, get_recent_logs

__all__ = [
    'SYSTEM_LOGS',
    'append_system_log',
    'get_recent_logs',
]
