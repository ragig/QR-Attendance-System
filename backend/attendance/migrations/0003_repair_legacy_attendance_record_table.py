from django.db import migrations


def repair_legacy_attendance_record_table(apps, schema_editor):
    table_name = 'attendance_attendancerecord'

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = {row[1]: row for row in cursor.fetchall()}

        legacy_columns = {'checked_in_at', 'student_id'}
        current_columns = {'check_in', 'employee_id', 'check_out'}
        if legacy_columns.isdisjoint(columns) and current_columns.issubset(columns):
            return

        if not legacy_columns.issubset(columns):
            return

        cursor.execute('PRAGMA foreign_keys=OFF')
        cursor.execute(
            f'''
            CREATE TABLE {table_name}_new (
                id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                check_in datetime NOT NULL,
                check_out datetime NULL,
                status varchar(20) NOT NULL,
                employee_id integer NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
                session_id bigint NULL REFERENCES attendance_attendancesession(id) DEFERRABLE INITIALLY DEFERRED
            )
            '''
        )
        cursor.execute(
            f'''
            INSERT INTO {table_name}_new (id, check_in, check_out, status, employee_id, session_id)
            SELECT id, checked_in_at, NULL, status, student_id, session_id
            FROM {table_name}
            '''
        )
        cursor.execute(f'DROP TABLE {table_name}')
        cursor.execute(f'ALTER TABLE {table_name}_new RENAME TO {table_name}')
        cursor.execute(
            f'CREATE INDEX attendance_attendancerecord_employee_id_idx ON {table_name} (employee_id)'
        )
        cursor.execute(
            f'CREATE INDEX attendance_attendancerecord_session_id_idx ON {table_name} (session_id)'
        )
        cursor.execute('PRAGMA foreign_keys=ON')


class Migration(migrations.Migration):
    dependencies = [
        ('attendance', '0002_userprofile_display_name_and_more'),
    ]

    operations = [
        migrations.RunPython(repair_legacy_attendance_record_table, migrations.RunPython.noop),
    ]
