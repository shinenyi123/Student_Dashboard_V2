import re
import tempfile
from datetime import date, datetime

import pandas as pd
from flask import Blueprint, jsonify, render_template, request, send_file, session

from models.student_model import eng_to_mm, get_database_connection, release_database_connection
from routes.auth_routes import login_required


bug_check_bp = Blueprint('bug_check', __name__)

EXPECTED_COLUMNS = [
    'စဉ်',
    'ကျောင်းဝင်အမှတ်',
    'နာမည်',
    'အဖေနာမည်',
    'ကျားမ',
    'မွေးနေ့',
    'class',
    'Grade',
]
BUG_TYPES = {'duplicate_roll', 'incomplete_row', 'invalid_date'}
WORKING_COPY_KEY = 'bug_check_working_copy'
DATE_PATTERN = re.compile(r'^\d{2}-\d{2}-\d{4}$')


def _cell_value(value):
    if pd.isna(value):
        return ''
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.strftime('%d-%m-%Y')
    return str(value)


def _row_object(row, row_number):
    values = [_cell_value(value) for value in row]
    return {
        'original_row_number': row_number,
        **dict(zip(EXPECTED_COLUMNS, values)),
    }


def _dataframe_rows(dataframe):
    return [
        _row_object(row.tolist(), index + 2)
        for index, row in dataframe.iterrows()
    ]


def _is_filled(value):
    return _cell_value(value).strip() != ''


def _empty_columns(values):
    return [
        column for column, value in zip(EXPECTED_COLUMNS, values)
        if not _is_filled(value)
    ]


def _invalid_date(value):
    try:
        datetime.strptime(value, '%d-%m-%Y')
    except ValueError:
        return True
    return False


def _validate_rows(rows):
    duplicate_rows = []
    incomplete_rows = []
    invalid_date_rows = []
    roll_groups = {}

    for row in rows:
        values = [row.get(column, '') for column in EXPECTED_COLUMNS]
        row_object = {
            'original_row_number': row['original_row_number'],
            **dict(zip(EXPECTED_COLUMNS, values)),
        }
        roll_number = _cell_value(values[1]).strip()
        if roll_number:
            roll_groups.setdefault(roll_number, []).append(row_object)

        filled_count = sum(_is_filled(value) for value in values)
        if 0 < filled_count < len(EXPECTED_COLUMNS):
            incomplete_rows.append({
                **row_object,
                'offending_columns': _empty_columns(values),
            })

        date_value = _cell_value(values[5]).strip()
        if date_value and (
            not DATE_PATTERN.fullmatch(date_value)
            or _invalid_date(date_value)
        ):
            invalid_date_rows.append({
                **row_object,
                'offending_columns': ['မွေးနေ့'],
            })

    for grouped_rows in roll_groups.values():
        if len(grouped_rows) > 1:
            for row in grouped_rows:
                row['offending_columns'] = ['ကျောင်းဝင်အမှတ်']
            duplicate_rows.extend(grouped_rows)

    return {
        'duplicate_roll': {'count': len(duplicate_rows), 'rows': duplicate_rows},
        'incomplete_row': {'count': len(incomplete_rows), 'rows': incomplete_rows},
        'invalid_date': {'count': len(invalid_date_rows), 'rows': invalid_date_rows},
    }


def _get_rows():
    return session.get(WORKING_COPY_KEY)


def _summary_response(rows):
    return {
        'format_valid': True,
        'bugs': _validate_rows(rows),
    }


def _import_rows(rows):
    conn = get_database_connection(timeout=15)
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM students')
        for row in rows:
            values = [_cell_value(row.get(column, '')).strip() for column in EXPECTED_COLUMNS]
            if not any(values):
                continue
            cursor.execute('''INSERT INTO students
                (စဉ်,ကျောင်းဝင်အမှတ်,နာမည်,အဖေနာမည်,ကျားမ,မွေးနေ့,class,grade)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ကျောင်းဝင်အမှတ်) DO NOTHING''',
                (eng_to_mm(values[0]),
                 eng_to_mm(values[1]),
                 values[2],
                 values[3],
                 values[4],
                 datetime.strptime(values[5], '%d-%m-%Y').strftime('%d-%m-%Y'),
                 values[6],
                 values[7]))
        conn.commit()
    finally:
        release_database_connection(conn)


def _import_if_clean(rows):
    bugs = _validate_rows(rows)
    if any(bug['count'] > 0 for bug in bugs.values()):
        return False, bugs
    _import_rows(rows)
    session.pop(WORKING_COPY_KEY, None)
    session.modified = True
    return True, bugs


@bug_check_bp.get('/bug-check')
@login_required
def bug_check_page():
    return render_template('bug_check.html')


@bug_check_bp.get('/bug-check/detail/<bug_type>')
@login_required
def bug_detail_page(bug_type):
    if bug_type not in BUG_TYPES:
        return 'Unknown bug type', 404
    return render_template('bug_detail.html', bug_type=bug_type)


@bug_check_bp.post('/api/bug-check/upload')
@login_required
def upload_bug_check_file():
    uploaded_file = request.files.get('myfile')
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({'error': 'Please choose an Excel file.'}), 400

    try:
        dataframe = pd.read_excel(uploaded_file, dtype=object)
    except Exception as error:
        return jsonify({'error': f'Unable to read Excel file: {error}'}), 400

    session.pop(WORKING_COPY_KEY, None)
    if list(dataframe.columns) != EXPECTED_COLUMNS:
        session.modified = True
        return jsonify({
            'format_valid': False,
            'expected_columns': EXPECTED_COLUMNS,
        })

    rows = _dataframe_rows(dataframe)
    session[WORKING_COPY_KEY] = rows
    session.modified = True
    imported, bugs = _import_if_clean(rows)
    if imported:
        return jsonify({'format_valid': True, 'bugs': bugs, 'imported': True})
    return jsonify({
        'format_valid': True,
        'bugs': bugs,
        'imported': False,
    })


@bug_check_bp.get('/api/bug-check/status')
@login_required
def get_bug_check_status():
    rows = _get_rows()
    if rows is None:
        return jsonify({'active': False})
    return jsonify({'active': True, **_summary_response(rows)})


@bug_check_bp.get('/api/bug-check/detail/<bug_type>')
@login_required
def get_bug_detail(bug_type):
    if bug_type not in BUG_TYPES:
        return jsonify({'error': 'Unknown bug type.'}), 404
    rows = _get_rows()
    if rows is None:
        return jsonify({'error': 'No active bug check. Upload a file from the Dashboard first.'}), 404
    bugs = _validate_rows(rows)
    return jsonify({'bug_type': bug_type, 'rows': bugs[bug_type]['rows']})


@bug_check_bp.post('/api/bug-check/save-progress')
@login_required
def save_bug_progress():
    rows = _get_rows()
    if rows is None:
        return jsonify({'error': 'No active bug check. Upload a file from the Dashboard first.'}), 404

    payload = request.get_json(silent=True) or {}
    rows_by_number = {row['original_row_number']: row for row in rows}
    for edit in payload.get('edits', []):
        row_number = int(edit['original_row_number'])
        row = rows_by_number.get(row_number)
        if row is None:
            continue
        for column in EXPECTED_COLUMNS:
            if column in edit.get('values', {}):
                row[column] = edit['values'][column]

    deleted_rows = {
        int(row_number) for row_number in payload.get('deleted_rows', [])
    }
    updated_rows = [
        row for row in rows
        if row['original_row_number'] not in deleted_rows
    ]
    session[WORKING_COPY_KEY] = updated_rows
    session.modified = True
    imported, bugs = _import_if_clean(updated_rows)
    return jsonify({
        'active': not imported,
        'imported': imported,
        'redirect': '/' if imported else '/bug-check',
        'bugs': bugs,
    })


@bug_check_bp.get('/api/bug-check/template')
@login_required
def download_bug_template():
    sample_rows = [
        ['၁', 'A-001', 'မောင်အောင်', 'ဦးအောင်', 'ကျား', '14-09-2011', 'A', 'Grade 5'],
        ['၂', 'A-002', 'မဝင်း', 'ဦးဝင်း', 'မ', '02-01-2012', 'A', 'Grade 5'],
        ['၃', 'B-001', 'မောင်ထွန်း', 'ဦးထွန်း', 'ကျား', '25-11-2011', 'B', 'Grade 5'],
        ['၄', 'B-002', 'မသင်း', 'ဦးသင်း', 'မ', '30-06-2012', 'B', 'Grade 5'],
        ['၅', 'C-001', 'မောင်လင်း', 'ဦးလင်း', 'ကျား', '18-03-2011', 'C', 'Grade 5'],
    ]
    dataframe = pd.DataFrame(sample_rows, columns=EXPECTED_COLUMNS)
    output = tempfile.SpooledTemporaryFile()
    dataframe.to_excel(output, index=False)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name='student_upload_template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
