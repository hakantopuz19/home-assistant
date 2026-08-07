"""UDP communication helpers for external communication."""

import socket

try:
    import _thread
except ImportError:
    _thread = None


class UDPConfig:
    """Simple UDP sender/receiver wrapper for MicroPython."""

    def __init__(self, host='0.0.0.0', port=9001):
        self.host = host
        self.port = port
        self.sock = None
        self._running = False
        self._thread = None
        self._callbacks = []

    def open(self):
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception:
                pass
            self.sock.bind((self.host, self.port))
        return self.sock

    def sendto(self, data, host='127.0.0.1', port=9001):
        sock = self.open()
        if isinstance(data, str):
            data = data.encode('utf-8')
        sock.sendto(data, (host, port))
        return True

    def recvfrom(self, size=1024):
        sock = self.open()
        return sock.recvfrom(size)

    def on_data(self, callback):
        self._callbacks.append(callback)
        return callback

    def start_background(self):
        if self._thread is not None and self._running:
            return True
        self._running = True
        self.open()
        if _thread is not None:
            self._thread = _thread.start_new_thread(self._run_loop, ())
            return True
        self._run_loop()
        return True

    def stop_background(self):
        self._running = False
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self._thread = None
        return True

    def _run_loop(self):
        while self._running:
            try:
                data, address = self.recvfrom(1024)
                if data:
                    for callback in self._callbacks:
                        try:
                            callback(data, address)
                        except Exception:
                            pass
            except Exception:
                continue

    def close(self):
        return self.stop_background()


__all__ = ['UDPConfig']
