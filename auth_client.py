import os

import requests


def _required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f'{name} must be set before starting the application')
    return value


def auth_service_base_url():
    return _required('AUTH_SERVICE_URL').rstrip('/')


def authenticate_user(email, password):
    response = requests.post(
        f'{auth_service_base_url()}/api/authenticate',
        headers={'X-Auth-Service-Key': _required('AUTH_SERVICE_API_KEY')},
        json={
            'email': email,
            'password': password,
            'website_slug': _required('AUTH_SERVICE_WEBSITE_SLUG'),
        },
        timeout=10,
    )
    if response.status_code in (401, 403):
        result = response.json()
        result['status'] = response.status_code
        return result
    response.raise_for_status()
    result = response.json()
    if not result.get('success') or not isinstance(result.get('user'), dict):
        raise ValueError('Auth service returned an incomplete authentication response.')
    return result
