"""TCP client/server helpers for external communication."""

import socket

try:
    import _thread
except ImportError:
    _thread = None


class TCPClientConfig:
    """Simple TCP client configuration wrapper."""

    def __init__(self, host='localhost', port=9000, timeout=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self._running = False
        self._thread = None
        self._callbacks = []

    def connect(self):
        if self.sock is not None:
            return self.sock
        self.sock = socket.socket()
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        return self.sock

    def send(self, data):
        sock = self.connect()
        if isinstance(data, str):
            data = data.encode('utf-8')
        sock.sendall(data)
        return True

    def receive(self, size=1024):
        sock = self.connect()
        return sock.recv(size)

    def on_data(self, callback):
        self._callbacks.append(callback)
        return callback

    def start_background(self):
        if self._thread is not None and self._running:
            return True
        self._running = True
        if _thread is not None:
            self._thread = _thread.start_new_thread(self._run_loop, ())
            return True
        self._run_loop()
        return True

    def stop_background(self):
        self._running = False
        self._thread = None
        return True

    def _run_loop(self):
        while self._running:
            try:
                data = self.receive(1024)
                if data:
                    for callback in self._callbacks:
                        try:
                            callback(data)
                        except Exception:
                            pass
            except Exception:
                continue

    def disconnect(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        return True


class TCPServerConfig:
    """Simple TCP server configuration wrapper."""

    def __init__(self, host='0.0.0.0', port=9000, backlog=2):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.sock = None
        self._running = False
        self._thread = None
        self._callbacks = []

    def start(self):
        if self.sock is not None:
            return self.sock
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.backlog)
        return self.sock

    def accept(self):
        if self.sock is None:
            self.start()
        return self.sock.accept()

    def on_data(self, callback):
        self._callbacks.append(callback)
        return callback

    def start_background(self):
        if self._thread is not None and self._running:
            return True
        self._running = True
        self.start()
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
                client_sock, _ = self.accept()
            except Exception:
                continue
            try:
                data = client_sock.recv(1024)
                if data:
                    for callback in self._callbacks:
                        try:
                            callback(data)
                        except Exception:
                            pass
            except Exception:
                pass
            finally:
                try:
                    client_sock.close()
                except Exception:
                    pass


__all__ = ['TCPClientConfig', 'TCPServerConfig']
