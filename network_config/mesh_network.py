"""Simple application-layer mesh overlay for ESP32 MicroPython.

This module does not implement hardware-level ESP-MESH, but it provides a
UDP-based peer discovery and messaging overlay for ESP32 nodes on the same
Wi-Fi subnet.
"""
try:
    import network
except ImportError:
    network = None

try:
    import socket
except ImportError:
    socket = None

try:
    import time
except ImportError:
    import utime as time

try:
    import _thread
except ImportError:
    _thread = None

try:
    import ujson as json
except ImportError:
    import json

DEFAULT_MESH_PORT = 10000
BROADCAST_ADDRESS = '255.255.255.255'
BUFFER_SIZE = 1024
DISCOVERY_INTERVAL = 5
RECEIVE_TIMEOUT = 0.5


class MeshNode:
    def __init__(
        self,
        node_id,
        listen_port=DEFAULT_MESH_PORT,
        discovery_interval=DISCOVERY_INTERVAL,
        timeout=RECEIVE_TIMEOUT,
    ):
        self.node_id = node_id
        self.listen_port = listen_port
        self.discovery_interval = discovery_interval
        self.timeout = timeout
        self.peers = {}
        self.sock = None
        self.running = False
        self._last_hello = 0
        self._thread_started = False

    def connect_station(self, ssid, password, timeout=15):
        if network is None:
            raise RuntimeError('network module is not available')

        wlan = network.WLAN(network.STA_IF)
        if not wlan.active():
            wlan.active(True)

        if wlan.isconnected():
            return True

        wlan.connect(ssid, password)
        deadline = time.time() + timeout
        while not wlan.isconnected() and time.time() < deadline:
            time.sleep(1)

        return wlan.isconnected()

    def start_access_point(
        self,
        ssid='ESP32-MESH',
        password='12345678',
        channel=1,
        authmode=3,
        hidden=False,
        max_clients=4,
    ):
        if network is None:
            raise RuntimeError('network module is not available')

        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(
            essid=ssid,
            password=password,
            channel=channel,
            authmode=authmode,
            hidden=hidden,
            max_clients=max_clients,
        )
        return ap

    def stop_access_point(self):
        if network is None:
            raise RuntimeError('network module is not available')

        ap = network.WLAN(network.AP_IF)
        ap.active(False)
        return ap

    def status(self):
        return {
            'node_id': self.node_id,
            'peers': list(self.peers.keys()),
            'peer_count': len(self.peers),
            'running': self.running,
            'local_ip': self._local_ip(),
        }

    def start(self, use_thread=True):
        if socket is None:
            raise RuntimeError('socket module is not available')

        self._ensure_socket()
        self.running = True

        if use_thread and _thread is not None:
            self._thread_started = True
            _thread.start_new_thread(self._run, ())

        return self

    def stop(self):
        self.running = False
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        return self

    def run_once(self):
        if not self.running:
            raise RuntimeError('MeshNode is not running')

        self._send_hello()
        self._receive_packets()

    def broadcast_message(self, message):
        payload = {
            'type': 'mesh_message',
            'node_id': self.node_id,
            'message': message,
        }
        self._send_packet(BROADCAST_ADDRESS, self.listen_port, payload)

    def send_message(self, node_id, message):
        peer = self.peers.get(node_id)
        if peer is None:
            raise ValueError('Unknown peer: %s' % node_id)

        payload = {
            'type': 'mesh_message',
            'node_id': self.node_id,
            'message': message,
        }
        self._send_packet(peer['ip'], peer['port'], payload)

    def _run(self):
        while self.running:
            self._send_hello()
            deadline = time.time() + self.discovery_interval
            while self.running and time.time() < deadline:
                self._receive_packets()

    def _ensure_socket(self):
        if self.sock is not None:
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass

        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except Exception:
            pass

        self.sock.bind(('0.0.0.0', self.listen_port))
        self.sock.settimeout(self.timeout)

    def _send_hello(self):
        now = time.time()
        if now - self._last_hello < self.discovery_interval:
            return
        self._last_hello = now
        payload = {
            'type': 'mesh_hello',
            'node_id': self.node_id,
            'ip': self._local_ip(),
            'port': self.listen_port,
        }
        self._send_packet(BROADCAST_ADDRESS, self.listen_port, payload)

    def _receive_packets(self):
        if self.sock is None:
            return

        while True:
            try:
                data, address = self.sock.recvfrom(BUFFER_SIZE)
            except OSError:
                return
            except Exception:
                return

            if not data:
                return

            try:
                payload = json.loads(data.decode('utf-8', 'ignore'))
            except Exception:
                continue

            self._handle_payload(payload, address)

    def _handle_payload(self, payload, address):
        if not isinstance(payload, dict):
            return

        message_type = payload.get('type')
        sender_id = payload.get('node_id')
        if sender_id is None or sender_id == self.node_id:
            return

        if message_type == 'mesh_hello':
            self.peers[sender_id] = {
                'ip': payload.get('ip', address[0]),
                'port': payload.get('port', address[1]),
                'last_seen': time.time(),
            }
        elif message_type == 'mesh_message':
            print('[MESH]', sender_id, payload.get('message'))
            self.peers[sender_id] = {
                'ip': address[0],
                'port': address[1],
                'last_seen': time.time(),
            }

    def _send_packet(self, host, port, payload):
        if self.sock is None:
            self._ensure_socket()

        try:
            data = json.dumps(payload).encode('utf-8')
            self.sock.sendto(data, (host, port))
        except Exception:
            pass

    def _local_ip(self):
        if network is None:
            return None

        sta = network.WLAN(network.STA_IF)
        if sta.active() and sta.isconnected():
            return sta.ifconfig()[0]

        ap = network.WLAN(network.AP_IF)
        if ap.active():
            return ap.ifconfig()[0]

        return None


def create_mesh_node(node_id, **kwargs):
    return MeshNode(node_id, **kwargs)
