"""Simple MQTT-style configuration helpers for external communication.

This module provides both client and server abstractions for lightweight
MQTT-like messaging over TCP sockets. Each class can run in its own background
thread when requested.
"""

try:
    import json
except ImportError:
    import ujson as json

import socket

try:
    import _thread
except ImportError:
    _thread = None


class MQTTClientConfig:
    """A tiny MQTT-like client wrapper using plain TCP sockets."""

    def __init__(self, host='localhost', port=1883, timeout=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock = None
        self._running = False
        self._thread = None
        self._callbacks = {}

    def connect(self):
        if self._sock is not None:
            return self._sock

        self._sock = socket.socket()
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.host, self.port))
        return self._sock

    def publish(self, topic, payload):
        sock = self.connect()
        message = json.dumps({'topic': topic, 'payload': payload})
        sock.sendall(message.encode('utf-8'))
        return True

    def subscribe(self, topic):
        sock = self.connect()
        message = json.dumps({'command': 'subscribe', 'topic': topic})
        sock.sendall(message.encode('utf-8'))
        return True

    def on_message(self, topic, callback):
        self._callbacks[topic] = callback
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
                sock = self.connect()
                data = sock.recv(1024)
                if not data:
                    continue
                message = data.decode('utf-8', 'ignore')
                try:
                    payload = json.loads(message)
                except Exception:
                    payload = {'topic': None, 'payload': message}
                topic = payload.get('topic')
                callback = self._callbacks.get(topic)
                if callback is not None:
                    callback(payload)
            except Exception:
                continue

    def disconnect(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        return True


class MQTTServerConfig:
    """A lightweight MQTT-like server that accepts client messages."""

    def __init__(self, host='0.0.0.0', port=1883, backlog=2, timeout=3):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout
        self._sock = None
        self._running = False
        self._thread = None
        self._callbacks = {}

    def start(self):
        if self._sock is not None:
            return self._sock
        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(self.backlog)
        self._sock.settimeout(self.timeout)
        return self._sock

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
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self._thread = None
        return True

    def on_message(self, topic, callback):
        self._callbacks[topic] = callback
        return callback

    def publish(self, topic, payload):
        message = json.dumps({'topic': topic, 'payload': payload})
        return message

    def _run_loop(self):
        while self._running:
            try:
                client_sock, _ = self._sock.accept()
            except Exception:
                continue
            try:
                data = client_sock.recv(1024)
                if not data:
                    client_sock.close()
                    continue
                payload = json.loads(data.decode('utf-8', 'ignore'))
                topic = payload.get('topic')
                callback = self._callbacks.get(topic)
                if callback is not None:
                    callback(payload)
            except Exception:
                pass
            finally:
                try:
                    client_sock.close()
                except Exception:
                    pass


__all__ = ['MQTTClientConfig', 'MQTTServerConfig']
