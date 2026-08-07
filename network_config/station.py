"""Wi-Fi station client mode for MicroPython ESP32."""

try:
    import network
except ImportError:
    network = None

try:
    import time
except ImportError:
    import utime as time


def connect(ssid, password, timeout=15, wlan=None):
    """Connect to a Wi-Fi network in station mode."""
    if network is None:
        raise RuntimeError('network module is not available')

    if wlan is None:
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


def disconnect(wlan=None, timeout=5):
    """Disconnect from the current Wi-Fi network."""
    if network is None:
        raise RuntimeError('network module is not available')

    if wlan is None:
        wlan = network.WLAN(network.STA_IF)

    wlan.disconnect()
    deadline = time.time() + timeout
    while wlan.isconnected() and time.time() < deadline:
        time.sleep(0.5)

    if not wlan.isconnected():
        try:
            wlan.active(False)
        except Exception:
            pass

    return wlan


def station_status(wlan=None):
    """Return the station interface status."""
    if network is None:
        return {}

    if wlan is None:
        wlan = network.WLAN(network.STA_IF)

    return {
        'active': wlan.active(),
        'connected': wlan.isconnected(),
        'config': wlan.ifconfig() if wlan.isconnected() else None,
    }


def scan_networks(wlan=None):
    """Scan and return nearby Wi-Fi networks."""
    if network is None:
        return []

    if wlan is None:
        wlan = network.WLAN(network.STA_IF)

    if not wlan.active():
        wlan.active(True)

    return wlan.scan()


__all__ = [
    'connect',
    'disconnect',
    'station_status',
    'scan_networks',
]
