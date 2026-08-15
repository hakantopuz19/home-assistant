"""Shared runtime logger for the dashboard and device services.

This is the canonical log implementation used across the project. The older
app.logging package remains as a compatibility shim for legacy imports.
"""

import os
import time

from .logger_store import StorageLogger
from .logger_stream import SerialLogger


def _resolve_storage_root():
    candidates = ['/storage', '/tmp/home-assistant-storage', os.path.join(os.getcwd(), '.storage')]
    for path in candidates:
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            if os.access(path, os.W_OK):
                return path
        except Exception:
            continue
    return '/tmp/home-assistant-storage'


SYSTEM_LOGS = StorageLogger(
    storage_root=_resolve_storage_root(),
    subdir='logs',
    filename='system.log',
    meta_filename='system.meta.json',
    max_size=64 * 1024,
)


def now_timestamp():
    return time.time()


def format_log_entry(message):
    stamp = now_timestamp()
    try:
        timestamp = time.localtime(stamp)
        return '%04d-%02d-%02d %02d:%02d:%02d %s' % (
            timestamp[0], timestamp[1], timestamp[2],
            timestamp[3], timestamp[4], timestamp[5], message,
        )
    except Exception:
        return '%s %s' % (str(stamp), message)


def append_system_log(message):
    """Store a human-readable device log entry using the circular storage logger."""
    text = format_log_entry(message)
    SYSTEM_LOGS.write(text)
    return text


def get_recent_logs(limit=200):
    full_log = SYSTEM_LOGS.read_all()
    if not full_log:
        return []
    lines = [line for line in full_log.splitlines() if line.strip()]
    return lines[-limit:]


__all__ = [
    'SYSTEM_LOGS',
    'append_system_log',
    'get_recent_logs',
    'StorageLogger',
    'SerialLogger',
    'format_log_entry',
    'now_timestamp',
]

