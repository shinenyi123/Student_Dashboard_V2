import os
import time
from urllib.parse import urlencode

import jwt
import requests
from jwt import PyJWKClient
from flask import session


def _required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f'{name} must be set before starting the application')
    return value


def auth_service_base_url():
    return os.environ.get('AUTH_SERVICE_BASE_URL', 'https://auth-service-kaef.onrender.com').rstrip('/')


def oauth_client_id():
    return _required('OAUTH_CLIENT_ID')


def oauth_redirect_uri():
    return _required('OAUTH_REDIRECT_URI')


def build_auth_url(state):
    return f'{auth_service_base_url()}/login?' + urlencode({
        'client_id': oauth_client_id(), 'redirect_uri': oauth_redirect_uri(), 'state': state,
    })


def build_signup_url(state):
    return f'{auth_service_base_url()}/signup?' + urlencode({
        'client_id': oauth_client_id(), 'redirect_uri': oauth_redirect_uri(), 'state': state,
    })


def exchange_code(code):
    response = requests.post(
        f'{auth_service_base_url()}/oauth/token',
        json={
            'code': code,
            'client_id': oauth_client_id(),
            'client_secret': _required('OAUTH_CLIENT_SECRET'),
            'redirect_uri': oauth_redirect_uri(),
        }, timeout=10,
    )
    response.raise_for_status()
    tokens = response.json()
    if not tokens.get('access_token') or not tokens.get('refresh_token'):
        raise ValueError('Auth service returned an incomplete token response.')
    return tokens


def store_tokens(tokens, claims):
    session['user_id'] = str(claims['sub'])
    session['email'] = claims['email']
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']
    session['access_token_expires_at'] = int(time.time()) + int(tokens.get('expires_in', 1800))


def validate_access_token(access_token):
    jwks_client = PyJWKClient(f'{auth_service_base_url()}/.well-known/jwks.json')
    signing_key = jwks_client.get_signing_key_from_jwt(access_token)
    claims = jwt.decode(
        access_token, signing_key.key, algorithms=['RS256'], audience=oauth_client_id(),
    )
    if not claims.get('sub') or not claims.get('email'):
        raise ValueError('Auth service token did not contain an identity.')
    return claims


def refresh_session_tokens():
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return False
    response = requests.post(
        f'{auth_service_base_url()}/oauth/refresh',
        json={
            'client_id': oauth_client_id(),
            'client_secret': _required('OAUTH_CLIENT_SECRET'),
            'refresh_token': refresh_token,
        }, timeout=10,
    )
    response.raise_for_status()
    tokens = response.json()
    claims = validate_access_token(tokens['access_token'])
    session['user_id'] = str(claims['sub'])
    session['email'] = claims['email']
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']
    session['access_token_expires_at'] = int(time.time()) + int(tokens.get('expires_in', 1800))
    return True