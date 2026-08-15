"""Configuration helpers for device JSON files."""

try:
    import uos as os
except ImportError:  # pragma: no cover
    import os

try:
    import ujson as json
except ImportError:  # pragma: no cover
    import json


def _as_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ('1', 'true', 'yes', 'on'):
            return True
        if lowered in ('0', 'false', 'no', 'off'):
            return False
    return default


def _as_int(value, default=0):
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _clean_gpio_config(gpio_cfg):
    gpio_cfg = _as_dict(gpio_cfg)
    pins = gpio_cfg.get('pins', [])
    if not isinstance(pins, list):
        pins = []
    cleaned_pins = []
    for pin in pins:
        if not isinstance(pin, dict):
            continue
        piece = {} 
        if 'id' in pin:
            piece['id'] = _as_int(pin.get('id'), 0)
        if 'mode' in pin:
            mode = str(pin.get('mode', 'out'))
            piece['mode'] = mode if mode in ('in', 'out', 'analog') else 'out'
        if 'pull' in pin:
            pull = str(pin.get('pull', 'none'))
            piece['pull'] = pull if pull in ('none', 'up', 'down') else 'none'
        if 'value' in pin:
            piece['value'] = _as_int(pin.get('value'), 0)
        if piece:
            cleaned_pins.append(piece)
    gpio_cfg['enabled'] = _as_bool(gpio_cfg.get('enabled'), False)
    gpio_cfg['pins'] = cleaned_pins
    return gpio_cfg


def validate_network_config(data):
    if not isinstance(data, dict):
        return {}

    ap_cfg = _as_dict(data.get('access_point'))
    station_cfg = _as_dict(data.get('station'))
    mesh_cfg = _as_dict(data.get('mesh'))
    http_cfg = _as_dict(data.get('http_server'))
    ui_cfg = _as_dict(data.get('ui'))
    defaults_cfg = _as_dict(data.get('defaults'))

    cleaned = {
        'access_point': {
            'enabled': _as_bool(ap_cfg.get('enabled'), True),
            'ssid': str(ap_cfg.get('ssid', 'ESP32-AP')),
            'password': str(ap_cfg.get('password', '12345678')),
            'channel': _as_int(ap_cfg.get('channel'), 1),
            'authmode': _as_int(ap_cfg.get('authmode'), 3),
            'hidden': _as_bool(ap_cfg.get('hidden'), False),
            'max_clients': _as_int(ap_cfg.get('max_clients'), 4),
            'ip': str(ap_cfg.get('ip', '192.168.4.1')),
            'netmask': str(ap_cfg.get('netmask', '255.255.255.0')),
            'gateway': str(ap_cfg.get('gateway', '192.168.4.1')),
            'dns': str(ap_cfg.get('dns', '8.8.8.8')),
        },
        'station': {
            'enabled': _as_bool(station_cfg.get('enabled'), False),
            'ssid': str(station_cfg.get('ssid', '')),
            'password': str(station_cfg.get('password', '')),
            'timeout': _as_int(station_cfg.get('timeout'), 15),
            'reconnect': _as_bool(station_cfg.get('reconnect'), False),
            'reconnect_interval': _as_int(station_cfg.get('reconnect_interval'), 5),
        },
        'mesh': {
            'enabled': _as_bool(mesh_cfg.get('enabled'), False),
            'node_id': str(mesh_cfg.get('node_id', 'esp32-node-1')),
            'listen_port': _as_int(mesh_cfg.get('listen_port'), 10000),
            'discovery_interval': _as_int(mesh_cfg.get('discovery_interval'), 5),
            'broadcast': _as_bool(mesh_cfg.get('broadcast'), True),
        },
        'http_server': {
            'enabled': _as_bool(http_cfg.get('enabled'), True),
            'port': _as_int(http_cfg.get('port'), 80),
        },
        'ui': {
            'login_user': str(ui_cfg.get('login_user', 'admin')),
            'login_password': str(ui_cfg.get('login_password', 'admin')),
        },
        'defaults': {
            'encoding': str(defaults_cfg.get('encoding', 'utf-8')),
            'connect_timeout': _as_int(defaults_cfg.get('connect_timeout'), 15),
        },
    }
    return cleaned


def validate_hardware_config(data):
    if not isinstance(data, dict):
        return {}

    adc_cfg = _as_dict(data.get('adc'))
    dac_cfg = _as_dict(data.get('dac'))
    gpio_cfg = _clean_gpio_config(data.get('gpio'))
    pwm_cfg = _as_dict(data.get('pwm'))
    i2c_cfg = _as_dict(data.get('i2c'))
    i2s_cfg = _as_dict(data.get('i2s'))

    cleaned = {
        'adc': {
            'enabled': _as_bool(adc_cfg.get('enabled'), False),
            'pin': _as_int(adc_cfg.get('pin'), 0),
            'attenuation': _as_int(adc_cfg.get('attenuation'), 3),
            'sample_rate': _as_int(adc_cfg.get('sample_rate'), 1000),
        },
        'dac': {
            'enabled': _as_bool(dac_cfg.get('enabled'), False),
            'pin': _as_int(dac_cfg.get('pin'), 0),
            'value': _as_int(dac_cfg.get('value'), 0),
        },
        'gpio': gpio_cfg,
        'pwm': {
            'enabled': _as_bool(pwm_cfg.get('enabled'), False),
            'pin': _as_int(pwm_cfg.get('pin'), 0),
            'freq': _as_int(pwm_cfg.get('freq'), 1000),
            'duty': _as_int(pwm_cfg.get('duty'), 0),
        },
        'i2c': {
            'enabled': _as_bool(i2c_cfg.get('enabled'), False),
            'scl_pin': _as_int(i2c_cfg.get('scl_pin'), 0),
            'sda_pin': _as_int(i2c_cfg.get('sda_pin'), 0),
            'freq': _as_int(i2c_cfg.get('freq'), 100000),
        },
        'i2s': {
            'enabled': _as_bool(i2s_cfg.get('enabled'), False),
            'sck_pin': _as_int(i2s_cfg.get('sck_pin'), 0),
            'ws_pin': _as_int(i2s_cfg.get('ws_pin'), 0),
            'sd_pin': _as_int(i2s_cfg.get('sd_pin'), 0),
            'mode': _as_int(i2s_cfg.get('mode'), 1),
            'bits': _as_int(i2s_cfg.get('bits'), 16),
            'rate': _as_int(i2s_cfg.get('rate'), 16000),
        },
    }
    return cleaned


def load_json_config(path, default=None):
    try:
        with open(path, 'r') as handle:
            text = handle.read()
        if not text:
            return default
        return json.loads(text)
    except Exception:
        return default


def save_json_config(path, data):
    backup_path = path + '.bak'
    payload = json.dumps(data)
    try:
        with open(path, 'rb') as handle:
            backup_data = handle.read()
        try:
            with open(backup_path, 'wb') as backup_handle:
                backup_handle.write(backup_data)
        except Exception:
            pass
    except Exception:
        backup_data = None

    try:
        with open(path, 'w') as handle:
            handle.write(payload)
        return data
    except Exception:
        if backup_data is not None:
            try:
                with open(backup_path, 'rb') as backup_handle:
                    restored = backup_handle.read()
                with open(path, 'wb') as handle:
                    handle.write(restored)
            except Exception:
                pass
        raise


def load_network_config():
    return validate_network_config(load_json_config('device_config/network_cfg.json', default={}))


def load_hardware_config():
    return validate_hardware_config(load_json_config('device_config/hardware_cfg.json', default={}))
