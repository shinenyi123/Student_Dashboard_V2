from functools import wraps

import requests
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from auth_client import auth_service_base_url, authenticate_user


auth_bp = Blueprint('auth', __name__)


@auth_bp.get('/health')
def health():
    return jsonify({'status': 'ok'})


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_auth_user():
            return view(*args, **kwargs)
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'error': 'Authentication required.'}), 401
        return redirect(url_for('student.home'))
    return wrapped


def current_auth_user():
    user_id = session.get('user_id')
    email = session.get('email')
    if not user_id or not email:
        return None
    return {'id': user_id, 'email': email}


@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_auth_user():
            return redirect(url_for('student.home'))
        return render_template('login.html', auth_service_url=auth_service_base_url())

    email = request.form.get('email', '')
    password = request.form.get('password', '')
    try:
        result = authenticate_user(email, password)
    except (requests.RequestException, ValueError, RuntimeError):
        return render_template('login.html', auth_service_url=auth_service_base_url(), error='Unable to contact the authentication service.'), 502
    if not result.get('success'):
        return render_template('login.html', auth_service_url=auth_service_base_url(), error=result.get('error', 'Invalid email or password.')), result.get('status', 401)

    user = result['user']
    session.clear()
    session['user_id'] = user['id']
    session['email'] = user['email']
    return redirect(url_for('student.home'))


@auth_bp.route('/auth/logout', methods=['GET', 'POST'])
@auth_bp.post('/api/logout')
def logout():
    session.clear()
    if request.path == '/api/logout' or request.is_json:
        return jsonify({'message': 'Logged out.', 'redirect': '/'})
    return redirect('/')