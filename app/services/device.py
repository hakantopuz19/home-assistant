"""Device-level helpers for boot, network and UI startup."""

from app.config import load_network_config
from logger import append_system_log
from app.network import build_access_point_from_config, print_device_banner
from app.http.server import start_http_server
from network_config import access_point_status


def start_servers(cfg):
    http_cfg = cfg.get('http_server', {})
    if http_cfg.get('enabled', True):
        start_http_server(port=http_cfg.get('port', 80))


def reset_device():
    """Request a device reboot/reset in a safe, MicroPython-friendly way."""
    append_system_log('Device reset requested from dashboard')
    try:
        import machine
        machine.reset()
    except Exception:
        pass
    return {'ok': True, 'message': 'Device reset requested'}


def boot_device():
    cfg = load_network_config()
    ap = None
    access_cfg = cfg.get('access_point', {})

    try:
        if access_cfg.get('enabled', True):
            ap = build_access_point_from_config(cfg)
            append_system_log('Access point started')
            print(access_point_status(ap))
    except Exception as exc:
        append_system_log('Access point startup failed: %s' % exc)
        print('Access point startup failed:', exc)

    append_system_log('Booting device configuration UI')
    print_device_banner(cfg)
    start_servers(cfg)
