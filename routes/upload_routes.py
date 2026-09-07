from flask import Blueprint, jsonify
from routes.auth_routes import login_required


upload_bp = Blueprint('upload', __name__)


@upload_bp.post('/api/upload')
@login_required
def upload_data():
    return jsonify({
        'error': 'Direct imports are disabled. Use the Dashboard bug-check flow.'
    }), 410