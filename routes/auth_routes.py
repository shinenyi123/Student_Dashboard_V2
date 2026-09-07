import secrets
import time
from functools import wraps

import jwt
import requests
from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

from oauth_client import (
    exchange_code,
    prepare_login_url,
    refresh_session_tokens,
    store_tokens,
    validate_access_token,
)


auth_bp = Blueprint('auth', __name__)


@auth_bp.get('/health')
def health():
    return jsonify({'status': 'ok'})


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_auth_user():
            expires_at = session.get('access_token_expires_at', 0)
            if expires_at <= int(time.time()) + 30:
                try:
                    refreshed = refresh_session_tokens()
                except (requests.RequestException, jwt.PyJWTError, ValueError, RuntimeError):
                    session.clear()
                else:
                    if refreshed:
                        return view(*args, **kwargs)
                    session.clear()
            elif session.get('auth_user'):
                return view(*args, **kwargs)
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'error': 'Authentication required.'}), 401
        return redirect(url_for('student.home'))
    return wrapped


def current_auth_user():
    user = session.get('auth_user')
    if not isinstance(user, dict) or not user.get('sub') or not user.get('email'):
        return None
    return user


@auth_bp.get('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    returned_state = request.args.get('state')
    expected_state = session.pop('oauth_state', None)
    if not code:
        return 'Unable to complete authentication.', 400
    if not returned_state or not expected_state or not secrets.compare_digest(returned_state, expected_state):
        return 'Invalid authentication callback.', 400
    try:
        tokens = exchange_code(code)
        claims = validate_access_token(tokens['access_token'])
    except (requests.RequestException, jwt.PyJWTError, ValueError, RuntimeError) as error:
        current_app.logger.warning('Central authentication failed: %s', type(error).__name__)
        return 'Unable to complete authentication. Please try again.', 502
    store_tokens(tokens, claims)
    return redirect('/')


@auth_bp.route('/auth/logout', methods=['GET', 'POST'])
@auth_bp.post('/api/logout')
def logout():
    session.clear()
    if request.path == '/api/logout' or request.is_json:
        return jsonify({'message': 'Logged out.', 'redirect': '/'})
    return redirect('/')
