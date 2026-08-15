"""HTTP server, request parsing and API routing for the local dashboard."""

try:
    import usocket as socket
except ImportError:  # pragma: no cover
    import socket

try:
    import ujson as json
except ImportError:  # pragma: no cover
    import json

import gc

from app.security.auth import get_token_from_request, is_authorized, issue_token
from app.config import load_json_config, save_json_config, validate_network_config, validate_hardware_config
from logger import append_system_log, get_recent_logs

WEB_CONFIG_PATHS = (
    '/hardware_cfg_page', '/hardware_cfg_page/', '/network_cfg_page', '/network_cfg_page/',
    '/logs', '/logs/', '/logs_page', '/logs_page/'
)
IGNORED_LOG_PATHS = (
    '/favicon.ico', '/style.css', '/script.js', '/login_page/', '/hardware_cfg_page/',
    '/network_cfg_page/', '/logs_page/'
)


def should_log_request(method, path):
    if method == 'POST' and path.startswith('/api/'):
        return True
    if method == 'GET' and path.startswith('/api/'):
        return True
    if path.startswith('/api/'):
        return True
    if path in ('/', '/login', '/login/', '/hardware_cfg_page', '/hardware_cfg_page/', '/network_cfg_page', '/network_cfg_page/', '/logs', '/logs/', '/logs_page', '/logs_page/'):
        return True
    if path.endswith(('.css', '.js', '.ico', '.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.woff', '.woff2', '.ttf')):
        return False
    if path.startswith(IGNORED_LOG_PATHS):
        return False
    return False


def url_decode(value):
    result = ''
    i = 0
    while i < len(value):
        char = value[i]
        if char == '+':
            result += ' '
        elif char == '%' and i + 2 < len(value):
            try:
                result += chr(int(value[i + 1:i + 3], 16))
                i += 2
            except ValueError:
                result += char
        else:
            result += char
        i += 1
    return result


def parse_form_body(body_text):
    values = {}
    if not body_text:
        return values
    for item in body_text.split('&'):
        if '=' in item:
            key, value = item.split('=', 1)
            values[url_decode(key)] = url_decode(value)
    return values


def build_response(status_code, body, content_type='text/plain', location=None):
    if isinstance(body, str):
        payload = body.encode('utf-8')
    else:
        payload = body

    status_line = 'HTTP/1.1 200 OK' if status_code == 200 else 'HTTP/1.1 %s' % status_code
    headers = [
        status_line,
        'Content-Type: %s' % content_type,
        'Content-Length: %s' % len(payload),
        'Cache-Control: no-store',
        'Connection: close',
    ]
    if location is not None:
        headers.insert(1, 'Location: %s' % location)

    response = ('\r\n'.join(headers) + '\r\n\r\n').encode('utf-8') + payload
    return response


def build_json_response(status_code, data):
    return build_response(status_code, json.dumps(data), 'application/json')


def read_request(conn):
    request = b''
    conn.settimeout(1.0)
    body_length = None

    while True:
        try:
            chunk = conn.recv(4096)
        except Exception:
            break

        if not chunk:
            break

        request += chunk

        if b'\r\n\r\n' in request:
            header_part, body_part = request.split(b'\r\n\r\n', 1)
            for line in header_part.split(b'\r\n')[1:]:
                if b':' not in line:
                    continue
                key, value = line.split(b':', 1)
                if key.strip().lower() == b'content-length':
                    try:
                        body_length = int(value.strip())
                    except ValueError:
                        body_length = None
                    break
            if body_length is None:
                break
            if len(body_part) >= body_length:
                break

    return request


def parse_request(request):
    if not request:
        return None

    text = request.decode('utf-8', 'ignore')
    header_text, body_text = (text.split('\r\n\r\n', 1) + [''])[:2] if '\r\n\r\n' in text else (text, '')

    lines = header_text.split('\r\n')
    if not lines or ' ' not in lines[0]:
        return None

    method, raw_path, _ = lines[0].split(' ', 2)
    path = raw_path
    query = ''
    if '?' in raw_path:
        path, query = raw_path.split('?', 1)

    headers = {}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()

    try:
        content_length = int(headers.get('content-length', '0'))
    except ValueError:
        content_length = 0

    if content_length > 0:
        body_text = body_text[:content_length]

    return method, path, query, headers, body_text


def resolve_static_path(path):
    path = path or '/'
    path = path.split('?', 1)[0]
    if path in ('/', '/login', '/login/'):
        return 'web_pages/login_page/index.html'
    if path in ('/hardware_cfg_page', '/hardware_cfg_page/', '/hardware'):
        return 'web_pages/hardware_cfg_page/index.html'
    if path in ('/network_cfg_page', '/network_cfg_page/', '/network'):
        return 'web_pages/network_cfg_page/index.html'
    if path in ('/logs', '/logs/', '/logs_page', '/logs_page/'):
        return 'web_pages/logs_page/index.html'
    if path in ('/style.css', '/script.js'):
        return 'web_pages/login_page/' + path.lstrip('/')
    if path.startswith('/login_page/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/hardware_cfg_page/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/network_cfg_page/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/logs_page/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/logs/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/'):
        path = path[1:]
    if path.startswith('login_page/'):
        return 'web_pages/' + path
    if path.startswith('hardware_cfg_page/'):
        return 'web_pages/' + path
    if path.startswith('network_cfg_page/'):
        return 'web_pages/' + path
    if path.startswith('logs_page/'):
        return 'web_pages/' + path
    return None


def serve_static(path):
    file_path = resolve_static_path(path)
    if file_path is None:
        return build_response(404, 'Not Found', 'text/plain')

    try:
        with open(file_path, 'rb') as handle:
            payload = handle.read()
    except Exception:
        return build_response(404, 'Not Found', 'text/plain')

    ext = file_path.split('.')[-1].lower()
    if ext == 'css':
        content_type = 'text/css'
    elif ext == 'js':
        content_type = 'application/javascript'
    elif ext == 'json':
        content_type = 'application/json'
    else:
        content_type = 'text/html'

    return build_response(200, payload, content_type)


def handle_request(request, conn, addr):
    if not request:
        append_system_log('EMPTY_REQUEST_FROM %s' % (addr,))
        try:
            conn.close()
        except Exception:
            pass
        return

    parsed = parse_request(request)
    if parsed is None:
        append_system_log('BAD_REQUEST_FROM %s' % (addr,))
        conn.sendall(build_response(400, 'Bad Request', 'text/plain'))
        conn.close()
        return

    method, path, query, headers, body_text = parsed
    if should_log_request(method, path):
        append_system_log('REQUEST %s %s %s' % (addr, method, path))

    token = get_token_from_request(query, headers)

    if method == 'POST' and path == '/api/login':
        form_data = parse_form_body(body_text)
        username = form_data.get('username', '')
        password = form_data.get('password', '')
        network_cfg = load_json_config('device_config/network_cfg.json')
        ui_cfg = network_cfg.get('ui', {}) if isinstance(network_cfg, dict) else {}
        expected_user = ui_cfg.get('login_user', 'admin')
        expected_password = ui_cfg.get('login_password', 'admin')
        if username == expected_user and password == expected_password:
            token = issue_token(username)
            conn.sendall(build_json_response(200, {'ok': True, 'token': token}))
        else:
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Invalid credentials'}))
        conn.close()
        return

    if method == 'POST' and path == '/api/logout':
        if token:
            from app.security.auth import revoke_token
            revoke_token(token)
        conn.sendall(build_json_response(200, {'ok': True, 'logged_out': True}))
        conn.close()
        return

    if method == 'GET' and path == '/api/auth/validate':
        if is_authorized(token):
            conn.sendall(build_json_response(200, {'ok': True}))
        else:
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
        conn.close()
        return

    if method == 'GET' and path == '/api/hardware/read':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return

        cfg = load_json_config('device_config/hardware_cfg.json', default={}) or {}
        result = {
            'ok': True,
            'adc': {'enabled': False, 'value': None},
            'dac': {'enabled': False, 'value': None},
            'gpio': {'enabled': False, 'pins': []},
            'pwm': {'enabled': False, 'duty': None, 'freq': None},
            'i2c': {'enabled': False, 'devices': []},
        }

        try:
            from hardware_config.analog_to_digital import ADCConfig
            adc_cfg = cfg.get('adc', {}) if isinstance(cfg, dict) else {}
            if adc_cfg.get('enabled', False):
                adc = ADCConfig(adc_cfg.get('pin', 34), adc_cfg.get('attenuation', 3))
                result['adc'] = {'enabled': True, 'pin': adc_cfg.get('pin', 34), 'value': adc.read()}
        except Exception as exc:
            result['adc'] = {'enabled': bool(cfg.get('adc', {}).get('enabled', False)) if isinstance(cfg, dict) else False, 'value': None, 'error': str(exc)}

        try:
            from hardware_config.input_output import GPIOConfig
            gpio_cfg = cfg.get('gpio', {}) if isinstance(cfg, dict) else {}
            if gpio_cfg.get('enabled', False):
                pins = []
                for pin in gpio_cfg.get('pins', []):
                    if not isinstance(pin, dict):
                        continue
                    pin_id = pin.get('id', 0)
                    mode = pin.get('mode', 'out')
                    pull = pin.get('pull')
                    reader = GPIOConfig(pin_id, mode=mode, pull=pull, value=pin.get('value'))
                    pins.append({'id': pin_id, 'mode': mode, 'pull': pull, 'value': reader.read()})
                result['gpio'] = {'enabled': True, 'pins': pins}
        except Exception as exc:
            result['gpio'] = {'enabled': bool(cfg.get('gpio', {}).get('enabled', False)) if isinstance(cfg, dict) else False, 'pins': [], 'error': str(exc)}

        try:
            from hardware_config.i2c import I2CConfig
            i2c_cfg = cfg.get('i2c', {}) if isinstance(cfg, dict) else {}
            if i2c_cfg.get('enabled', False):
                i2c = I2CConfig(i2c_cfg.get('scl_pin', 22), i2c_cfg.get('sda_pin', 21), i2c_cfg.get('freq', 100000))
                devices = i2c.scan()
                result['i2c'] = {'enabled': True, 'devices': [str(item) for item in devices]}
        except Exception as exc:
            result['i2c'] = {'enabled': bool(cfg.get('i2c', {}).get('enabled', False)) if isinstance(cfg, dict) else False, 'devices': [], 'error': str(exc)}

        dac_cfg = cfg.get('dac', {}) if isinstance(cfg, dict) else {}
        if dac_cfg.get('enabled', False):
            result['dac'] = {'enabled': True, 'value': dac_cfg.get('value', 0)}

        pwm_cfg = cfg.get('pwm', {}) if isinstance(cfg, dict) else {}
        if pwm_cfg.get('enabled', False):
            result['pwm'] = {'enabled': True, 'duty': pwm_cfg.get('duty', 0), 'freq': pwm_cfg.get('freq', 1000)}

        conn.sendall(build_json_response(200, result))
        conn.close()
        return

    if method == 'GET' and path == '/api/logs':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return
        conn.sendall(build_json_response(200, {'ok': True, 'logs': get_recent_logs()}))
        conn.close()
        return

    if method == 'POST' and path == '/api/device/reset':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return
        try:
            from app.services.device import reset_device
            result = reset_device()
            conn.sendall(build_json_response(200, result))
        except Exception as exc:  # pragma: no cover
            conn.sendall(build_json_response(500, {'ok': False, 'error': str(exc)}))
        conn.close()
        return

    if method == 'GET' and path == '/api/config/network':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return
        conn.sendall(build_json_response(200, load_json_config('device_config/network_cfg.json')))
        conn.close()
        return

    if method == 'POST' and path == '/api/config/network':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return
        try:
            payload = json.loads(body_text or '{}')
        except Exception:
            conn.sendall(build_json_response(400, {'ok': False, 'error': 'Invalid JSON payload'}))
            conn.close()
            return

        current = load_json_config('device_config/network_cfg.json', default={}) or {}
        merged = current
        if isinstance(current, dict) and isinstance(payload, dict):
            merged = current.copy()
            for key, value in payload.items():
                merged[key] = value
        validated = validate_network_config(merged)
        try:
            save_json_config('device_config/network_cfg.json', validated)
            conn.sendall(build_json_response(200, {'ok': True, 'config': validated}))
        except Exception as exc:
            conn.sendall(build_json_response(500, {'ok': False, 'error': 'Unable to save configuration: %s' % exc}))
        conn.close()
        return

    if method == 'GET' and path == '/api/config/hardware':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return
        conn.sendall(build_json_response(200, load_json_config('device_config/hardware_cfg.json')))
        conn.close()
        return

    if method == 'POST' and path == '/api/config/hardware':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return
        try:
            payload = json.loads(body_text or '{}')
        except Exception:
            conn.sendall(build_json_response(400, {'ok': False, 'error': 'Invalid JSON payload'}))
            conn.close()
            return

        current = load_json_config('device_config/hardware_cfg.json', default={}) or {}
        merged = current
        if isinstance(current, dict) and isinstance(payload, dict):
            merged = current.copy()
            for key, value in payload.items():
                merged[key] = value
        validated = validate_hardware_config(merged)
        try:
            save_json_config('device_config/hardware_cfg.json', validated)
            conn.sendall(build_json_response(200, {'ok': True, 'config': validated}))
        except Exception as exc:
            conn.sendall(build_json_response(500, {'ok': False, 'error': 'Unable to save configuration: %s' % exc}))
        conn.close()
        return

    if path in WEB_CONFIG_PATHS and not is_authorized(token):
        append_system_log('REDIRECT_TO_LOGIN %s %s' % (addr, path))
        conn.sendall(build_response(302, 'Redirect', 'text/plain', location='/login'))
        conn.close()
        return

    response = serve_static(path)
    if should_log_request(method, path):
        append_system_log('SERVE %s %s len=%s' % (addr, path, len(response)))
    conn.sendall(response)
    conn.close()


def start_http_server(port=80):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    append_system_log('HTTP server listening on port %s' % port)
    print('HTTP server listening on port %s' % port)
    while True:
        try:
            conn, addr = server.accept()
            append_system_log('CONNECTION %s' % (addr,))
            print('CONNECTION', addr)
            try:
                request = read_request(conn)
                append_system_log('RAW_REQUEST_LEN %s' % (len(request) if request else 0))
                print('RAW_REQUEST_LEN', len(request) if request else 0)
                handle_request(request, conn, addr)
            except Exception as exc:
                append_system_log('request failed: %s' % exc)
                print('request failed:', exc)
                try:
                    conn.close()
                except Exception:
                    pass
        except Exception as exc:
            append_system_log('accept failed: %s' % exc)
            print('accept failed:', exc)
            break
        gc.collect()
