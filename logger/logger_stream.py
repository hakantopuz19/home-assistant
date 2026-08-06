"""Stream logger that outputs log lines to serial (UART) or stdout.

Provides a small `SerialLogger` that accepts a UART-like object with
`write(bytes)` method or falls back to `print()`.
"""

import time


class SerialLogger:
    """Logger that writes lines to a UART or stdout.

    Parameters
    ----------
    uart: optional
        An object with a `write(bytes)` method (e.g., machine.UART).
    prefix: str
        Optional string prefix for each line (timestamp will be added).
    """

    def __init__(self, uart=None, prefix=''):
        self.uart = uart
        self.prefix = prefix

    def write(self, line: str) -> None:
        """Send a log `line` to the configured output.

        Adds an ISO-like timestamp prefix to the message.
        """
        ts = time.time()
        msg = '{}{}: {}'.format(self.prefix, ts, line)
        if not msg.endswith('\r\n'):
            msg = msg + '\r\n'
        if self.uart is not None:
            try:
                # uart.write expects bytes on many ports
                self.uart.write(msg.encode('utf-8'))
                return
            except Exception:
                pass
        # Fallback to print
        print(msg, end='')


__all__ = ['SerialLogger']
