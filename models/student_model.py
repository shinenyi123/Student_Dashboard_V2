import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from psycopg2.pool import ThreadedConnectionPool


load_dotenv()

_connection_pool = None
DATABASE_COLUMNS = [
    'စဉ်',
    'ကျောင်းဝင်အမှတ်',
    'နာမည်',
    'အဖေနာမည်',
    'ကျားမ',
    'မွေးနေ့',
    'class',
    'grade',
]


def _get_connection_pool():
    global _connection_pool
    if _connection_pool is None:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise RuntimeError('DATABASE_URL must be set before accessing the database')
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        _connection_pool = ThreadedConnectionPool(1, 10, dsn=database_url)
    return _connection_pool


def get_database_connection(timeout=10):
    del timeout
    return _get_connection_pool().getconn()


def release_database_connection(connection):
    if connection is not None:
        connection.rollback()
        _get_connection_pool().putconn(connection)


def create_table():
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(''' CREATE TABLE IF NOT EXISTS students
                ( id SERIAL PRIMARY KEY,
                စဉ် TEXT,
                ကျောင်းဝင်အမှတ် TEXT,
                နာမည် TEXT,
                အဖေနာမည် TEXT,
                ကျားမ TEXT,
                မွေးနေ့ TEXT,
                class TEXT,
                grade TEXT,
                UNIQUE(ကျောင်းဝင်အမှတ်) ) ''')
        cursor.execute("""SELECT column_name FROM information_schema.columns
            WHERE table_name = 'students'""")
        columns = [row[0] for row in cursor.fetchall()]
        if 'grade' not in columns:
            cursor.execute('ALTER TABLE students ADD COLUMN grade TEXT')
        conn.commit()
    finally:
        release_database_connection(conn)


def calculate_age_avg(dob_str, date):
    dob = datetime.strptime(dob_str, '%d-%m-%Y')
    target_date = datetime.strptime(date, '%Y-%m-%d')
    check_date = target_date - relativedelta(months=6)
    age = check_date.year - dob.year

    if (check_date.month, check_date.day) < (dob.month, dob.day):
        age -= 1

    return age + 1


def calculate_age(dob_str, date):
    dob = datetime.strptime(dob_str, '%d-%m-%Y')
    target_date = datetime.strptime(date, '%Y-%m-%d')
    age = target_date.year - dob.year - ((target_date.month, target_date.day) < (dob.month, dob.day))
    return age


def apply_filters(data_age, class_html, gender_html, grade_html, age_html, age_html_1, age_html_2):
    data = data_age
    if class_html and class_html != 'all':
        data = [row for row in data if row[6] == class_html]
    if gender_html != 'all':
        data = [row for row in data if row[4] == gender_html]
    if grade_html and grade_html != 'all':
        data = [row for row in data if row[7] == grade_html]
    if age_html and age_html != 'all':
        data = [row for row in data if int(row[8]) == int(age_html)]
    elif age_html_1 and age_html_2:
        data = [row for row in data if int(age_html_1) <= int(row[8]) <= int(age_html_2)]
    return data


def get_student_rows():
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT စဉ်, ကျောင်းဝင်အမှတ်, နာမည်, အဖေနာမည်, ကျားမ, မွေးနေ့, class, grade FROM students')
        return cursor.fetchall()
    finally:
        release_database_connection(conn)


def get_grade_class_summary(date, class_html='all', gender_html='all', grade_html='all',
                            age_html='', age_html_1='', age_html_2=''):
    grouped = {}
    grand_total = {'male': 0, 'female': 0, 'total': 0}

    filtered_rows = get_filtered_student_data(
        date, age_html, age_html_1, age_html_2, class_html, gender_html, grade_html,
    )
    for row in filtered_rows:
        gender = row[4]
        class_name = row[6]
        grade = row[7]
        key = (grade, class_name)
        if key not in grouped:
            grouped[key] = {
                'grade': grade,
                'class': class_name,
                'male': 0,
                'female': 0,
                'total': 0,
            }

        grouped[key]['total'] += 1
        grand_total['total'] += 1
        if gender == 'ကျား':
            grouped[key]['male'] += 1
            grand_total['male'] += 1
        elif gender == 'မ':
            grouped[key]['female'] += 1
            grand_total['female'] += 1

    rows = sorted(
        grouped.values(),
        key=lambda item: (str(item['grade'] or ''), str(item['class'] or '')),
    )
    return {'rows': rows, 'grand_total': grand_total}


def get_filter_options(date):
    rows = get_student_rows()
    if not rows:
        return {'classes': [], 'grades': [], 'ages': []}
    ages = set()
    classes = set()
    grades = set()
    for row in rows:
        classes.add(row[6])
        grades.add(row[7])
        ages.add(calculate_age_avg(row[5], date))
    return {
        'classes': sorted(value for value in classes if value not in (None, '')),
        'grades': sorted(value for value in grades if value not in (None, '')),
        'ages': sorted(ages),
    }


def get_filtered_student_data(date, age_html, age_html_1, age_html_2, class_html, gender_html, grade_html):
    rows = get_student_rows()

    data_age = []
    for row in rows:
        no, roll, name, father, gender, dob, class_name, grade = row
        if age_html == '' and age_html_1 == '' and age_html_2 == '':
            age = calculate_age_avg(dob, date)
        elif age_html != '':
            age = calculate_age_avg(dob, date)
        else:
            age = calculate_age(dob, date)
        data_age.append((no, roll, name, father, gender, dob, class_name, grade, age))

    return apply_filters(data_age, class_html, gender_html, grade_html, age_html, age_html_1, age_html_2)


def eng_to_mm(number):
    eng_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    mm_digits = ['၀', '၁', '၂', '၃', '၄', '၅', '၆', '၇', '၈', '၉']
    number_list = []
    for num in str(number):
        for eng, mm in zip(eng_digits, mm_digits):
            if num == mm:
                number_list.append(num)
            elif num == eng:
                number_list.append(mm)
    return ''.join(number_list)