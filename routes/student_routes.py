from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from models.student_model import (
    get_filter_options,
    get_filtered_student_data,
    get_grade_class_summary,
)
from routes.auth_routes import login_required


student_bp = Blueprint('student', __name__)


@student_bp.get('/')
@login_required
def home():
    return render_template('index.html')


@student_bp.get('/summary')
@login_required
def summary():
    return render_template('summary.html')


@student_bp.get('/api/summary')
@login_required
def get_summary():
    age = request.args.get('age', '')
    age_1 = request.args.get('age_1', '')
    age_2 = request.args.get('age_2', '')
    class_name = request.args.get('class', 'all')
    gender = request.args.get('gender', 'all')
    grade = request.args.get('grade', 'all')
    date = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')
    summary = get_grade_class_summary(
        date, class_name, gender, grade, age, age_1, age_2,
    )
    summary['options'] = get_filter_options(date)
    return jsonify(summary)


@student_bp.get('/api/students')
@login_required
def get_students():
    age = request.args.get('age', '')
    age_1 = request.args.get('age_1', '')
    age_2 = request.args.get('age_2', '')
    class_name = request.args.get('class', 'all')
    gender = request.args.get('gender', 'all')
    grade = request.args.get('grade', 'all')
    date = request.args.get('date') or datetime.now().strftime('%Y-%m-%d')

    data = get_filtered_student_data(date, age, age_1, age_2, class_name, gender, grade)
    students = [
        {
            'စဉ်': row[0],
            'ကျောင်းဝင်အမှတ်': row[1],
            'နာမည်': row[2],
            'အဖေနာမည်': row[3],
            'ကျားမ': row[4],
            'မွေးနေ့': row[5],
            'class': row[6],
            'Grade': row[7],
            'အသက်': row[8],
        }
        for row in data
    ]

    return jsonify({
        'students': students,
        'summary': {
            'all': len(data),
            'male': len([row for row in data if row[4] == 'ကျား']),
            'female': len([row for row in data if row[4] == 'မ']),
        },
        'options': get_filter_options(date),
    })