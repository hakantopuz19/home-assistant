"""ESP32 bootstrap for AP mode and a local configuration web UI."""

import gc
import time

try:
    import usocket as socket
except ImportError:
    import socket

try:
    import ujson as json
except ImportError:
    import json

from network_config import create_access_point, access_point_status


AUTH_TOKENS = {}
PROTECTED_PATHS = ('/hardware_cfg_page', '/hardware_cfg_page/', '/network_cfg_page', '/network_cfg_page/')


def load_json_config(path):
    with open(path, 'r') as handle:
        return json.loads(handle.read())


def read_request(conn):
    request = b''
    conn.settimeout(1.0)
    while True:
        try:
            chunk = conn.recv(4096)
        except Exception:
            break
        if not chunk:
            break
        request += chunk
        if b'\r\n\r\n' in request:
            break
    return request


def parse_request(request):
    if not request:
        return None

    text = request.decode('utf-8', 'ignore')
    header_text, body_text = text.split('\r\n\r\n', 1) if '\r\n\r\n' in text else (text, '')
    lines = header_text.split('\r\n')
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

    return method, path, query, headers, body_text


def get_token_from_request(path, query, headers):
    token = None
    if query:
        parts = query.split('&')
        for item in parts:
            if item.startswith('token='):
                token = item.split('=', 1)[1]
                break
    if token is None:
        auth_header = headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
    return token


def is_authorized(token):
    return bool(token) and token in AUTH_TOKENS


def issue_token(username):
    token = 'token-%s' % username
    AUTH_TOKENS[token] = time.time()
    return token


def build_response(status_code, body, content_type='text/plain'):
    if isinstance(body, str):
        payload = body.encode('utf-8')
    else:
        payload = body

    headers = [
        'HTTP/1.1 %s OK' % status_code if status_code == 200 else 'HTTP/1.1 %s' % status_code,
        'Content-Type: %s' % content_type,
        'Content-Length: %s' % len(payload),
        'Cache-Control: no-store',
        'Connection: close',
        '',
    ]
    response = '\r\n'.join(headers).encode('utf-8') + payload
    return response


def build_json_response(status_code, data):
    body = json.dumps(data)
    return build_response(status_code, body, 'application/json')


def resolve_static_path(path):
    path = path or '/'
    path = path.split('?', 1)[0]
    if path in ('/', '/login', '/login/'):
        return 'web_pages/login_page/index.html'
    if path in ('/hardware_cfg_page', '/hardware_cfg_page/', '/hardware'):
        return 'web_pages/hardware_cfg_page/index.html'
    if path in ('/network_cfg_page', '/network_cfg_page/', '/network'):
        return 'web_pages/network_cfg_page/index.html'
    if path in ('/style.css', '/script.js'):
        return 'web_pages/login_page/' + path.lstrip('/')
    if path.startswith('/login_page/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/hardware_cfg_page/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/network_cfg_page/'):
        return 'web_pages/' + path.lstrip('/')
    if path.startswith('/'):
        path = path[1:]
    if path.startswith('login_page/'):
        return 'web_pages/' + path
    if path.startswith('hardware_cfg_page/'):
        return 'web_pages/' + path
    if path.startswith('network_cfg_page/'):
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


def parse_form_body(body_text):
    values = {}
    if not body_text:
        return values
    for item in body_text.split('&'):
        if '=' in item:
            key, value = item.split('=', 1)
            values[key] = value.replace('+', ' ')
    return values


def handle_request(request, conn, addr):
    parsed = parse_request(request)
    if parsed is None:
        conn.sendall(build_response(400, 'Bad Request', 'text/plain'))
        conn.close()
        return

    method, path, query, headers, body_text = parsed
    token = get_token_from_request(path, query, headers)

    if method == 'POST' and path == '/api/login':
        form_data = parse_form_body(body_text)
        username = form_data.get('username', '')
        password = form_data.get('password', '')
        network_cfg = load_json_config('device_config/network_cfg.json')
        ui_cfg = network_cfg.get('ui', {})
        expected_user = ui_cfg.get('login_user', 'admin')
        expected_password = ui_cfg.get('login_password', 'admin')
        if username == expected_user and password == expected_password:
            token = issue_token(username)
            conn.sendall(build_json_response(200, {'ok': True, 'token': token}))
        else:
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Invalid credentials'}))
        conn.close()
        return

    if method == 'GET' and path == '/api/auth/validate':
        if is_authorized(token):
            conn.sendall(build_json_response(200, {'ok': True}))
        else:
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
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

    if method == 'GET' and path == '/api/config/hardware':
        if not is_authorized(token):
            conn.sendall(build_json_response(401, {'ok': False, 'error': 'Unauthorized'}))
            conn.close()
            return
        conn.sendall(build_json_response(200, load_json_config('device_config/hardware_cfg.json')))
        conn.close()
        return

    if path in PROTECTED_PATHS and not is_authorized(token):
        conn.sendall(build_response(302, '', 'text/plain'))
        conn.close()
        return

    response = serve_static(path)
    conn.sendall(response)
    conn.close()


def start_http_server(port=80):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print('HTTP server listening on port %s' % port)
    while True:
        conn, addr = server.accept()
        try:
            request = read_request(conn)
            handle_request(request, conn, addr)
        except Exception as exc:
            print('request failed:', exc)
            try:
                conn.close()
            except Exception:
                pass
        gc.collect()


def main():
    network_cfg = load_json_config('device_config/network_cfg.json')
    access_cfg = network_cfg.get('access_point', {})
    http_cfg = network_cfg.get('http_server', {})

    ap = create_access_point(
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

    print('Access point started:')
    print(access_point_status(ap))
    print('Open http://192.168.4.1/ to access the login page')
    start_http_server(port=http_cfg.get('port', 80))


if __name__ == '__main__':
    main()

