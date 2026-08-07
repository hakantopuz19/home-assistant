"""Wi-Fi access point setup for MicroPython ESP32."""

try:
    import network
except ImportError:
    network = None


def create_access_point(ssid='ESP32-AP', password='12345678', channel=1,
                        authmode=3, hidden=False, max_clients=4,
                        ip='192.168.4.1', netmask='255.255.255.0',
                        gateway='192.168.4.1', dns='8.8.8.8'):
    """Start the ESP32 Wi-Fi access point with a fixed IP."""
    if network is None:
        raise RuntimeError('network module is not available')

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password,
              channel=channel, authmode=authmode,
              hidden=hidden, max_clients=max_clients)
    ap.ifconfig((ip, netmask, gateway, dns))
    return ap


def stop_access_point(ap=None):
    """Stop the access point."""
    if network is None:
        raise RuntimeError('network module is not available')

    if ap is None:
        ap = network.WLAN(network.AP_IF)
    ap.active(False)
    return ap


def access_point_status(ap=None):
    """Return the access point interface status."""
    if network is None:
        return {}

    if ap is None:
        ap = network.WLAN(network.AP_IF)

    return {
        'active': ap.active(),
        'config': ap.ifconfig() if ap.active() else None,
    }


__all__ = [
    'create_access_point',
    'stop_access_point',
    'access_point_status',
]
