import os


def _required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f'{name} must be set before starting the application')
    return value


def auth_service_base_url():
    return _required('AUTH_SERVICE_URL').rstrip('/')
