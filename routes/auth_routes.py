from functools import wraps

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from auth_client import auth_service_base_url
from models.student_model import get_database_connection, release_database_connection


auth_bp = Blueprint('auth', __name__)


def get_user_for_login(email):
    normalized_email = (email or '').strip().lower()
    if not normalized_email:
        return None
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, email, password_hash, is_verified FROM users WHERE email = %s',
            (normalized_email,),
        )
        return cursor.fetchone()
    finally:
        release_database_connection(conn)


def is_student_dashboard_authorized(user_id):
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT 1
               FROM user_websites uw
               JOIN websites w ON w.id = uw.website_id
               WHERE uw.user_id = %s AND w.slug = %s''',
            (user_id, 'student-dashboard'),
        )
        return cursor.fetchone() is not None
    finally:
        release_database_connection(conn)


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

    email = (request.form.get('email', '') or '').strip()
    password = request.form.get('password', '')

    user = get_user_for_login(email)
    if not user:
        return render_template('login.html', auth_service_url=auth_service_base_url(), error='Invalid email or password.'), 401

    user_id, user_email, password_hash, is_verified = user
    if not is_verified or not password_hash or not check_password_hash(password_hash, password):
        return render_template('login.html', auth_service_url=auth_service_base_url(), error='Invalid email or password.'), 401

    if not is_student_dashboard_authorized(user_id):
        return render_template('login.html', auth_service_url=auth_service_base_url(), error='Invalid email or password.'), 403

    session.clear()
    session['user_id'] = user_id
    session['email'] = user_email
    return redirect(url_for('student.home'))


@auth_bp.route('/auth/logout', methods=['GET', 'POST'])
@auth_bp.post('/api/logout')
def logout():
    session.clear()
    if request.path == '/api/logout' or request.is_json:
        return jsonify({'message': 'Logged out.', 'redirect': '/'})
    return redirect('/')
