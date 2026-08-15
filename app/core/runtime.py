"""Runtime helpers for the device application."""

import time


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
