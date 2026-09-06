import os
import sqlite3

from dotenv import load_dotenv

from models.student_model import (
    DATABASE_COLUMNS,
    create_table,
    get_database_connection,
    release_database_connection,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'database', 'students.db')


def migrate():
    load_dotenv()
    if not os.environ.get('DATABASE_URL'):
        raise RuntimeError('DATABASE_URL must be set for the migration')
    if not os.path.exists(SQLITE_PATH):
        raise FileNotFoundError(f'SQLite database not found: {SQLITE_PATH}')

    create_table()
    sqlite_connection = sqlite3.connect(SQLITE_PATH)
    postgres_connection = get_database_connection()
    try:
        sqlite_rows = sqlite_connection.execute(
            'SELECT {} FROM students'.format(', '.join(DATABASE_COLUMNS))
        ).fetchall()
        cursor = postgres_connection.cursor()
        placeholders = ', '.join(['%s'] * len(DATABASE_COLUMNS))
        columns = ','.join(DATABASE_COLUMNS)
        cursor.executemany(
            f'''INSERT INTO students ({columns}) VALUES ({placeholders})
                ON CONFLICT (ကျောင်းဝင်အမှတ်) DO NOTHING''',
            sqlite_rows,
        )
        postgres_connection.commit()
        print(f'Migrated {len(sqlite_rows)} rows to PostgreSQL.')
    finally:
        sqlite_connection.close()
        release_database_connection(postgres_connection)


if __name__ == '__main__':
    migrate()
