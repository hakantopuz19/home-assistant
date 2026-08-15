"""Network access point helpers for the device."""

from network_config import create_access_point, access_point_status


def build_access_point_from_config(cfg):
    access_cfg = cfg.get('access_point', {})
    return create_access_point(
        ssid=access_cfg.get('ssid', 'ESP32-AP'),
        password=access_cfg.get('password', '12345678'),
        channel=access_cfg.get('channel', 1),
        authmode=access_cfg.get('authmode', 3),
        hidden=access_cfg.get('hidden', False),
        max_clients=access_cfg.get('max_clients', 4),
        ip=access_cfg.get('ip', '192.168.4.1'),
        netmask=access_cfg.get('netmask', '255.255.255.0'),
        gateway=access_cfg.get('gateway', '192.168.4.1'),
        dns=access_cfg.get('dns', '8.8.8.8'),
    )


def print_device_banner(cfg):
    ui_cfg = cfg.get('ui', {})
    print('Access point started:')
    print('Open http://192.168.4.1/ to access the login page')
    print('Login credentials: %s / %s' % (
        ui_cfg.get('login_user', 'admin'),
        ui_cfg.get('login_password', 'admin'),
    ))
