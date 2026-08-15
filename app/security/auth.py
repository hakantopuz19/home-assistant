"""Authentication and token management for the dashboard."""

import time

AUTHORIZED_TOKENS = {}
# Backward-compatible alias for older references.
AUTHORIZA_TOKENS = AUTHORIZED_TOKENS
TOKEN_TIMEOUT_SECONDS = 60 * 60 * 8


def _purge_expired_tokens():
    now = time.time()
    for token, issued_at in list(AUTHORIZED_TOKENS.items()):
        if now - issued_at > TOKEN_TIMEOUT_SECONDS:
            del AUTHORIZED_TOKENS[token]


def get_token_from_request(query, headers):
    token = None
    if query:
        parts = query.split('&')
        for item in parts:
            if item.startswith('token='):
                token = item.split('=', 1)[1]
                break
    if token is None:
        auth_header = headers.get('authorization', '')
        if auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1]
    return token


def is_authorized(token):
    _purge_expired_tokens()
    return bool(token) and token in AUTHORIZED_TOKENS


def revoke_token(token):
    if token in AUTHORIZED_TOKENS:
        del AUTHORIZED_TOKENS[token]
    return True


def issue_token(username):
    _purge_expired_tokens()
    token = 'token-%s' % username
    AUTHORIZED_TOKENS[token] = time.time()
    return token
