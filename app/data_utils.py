# app/data_utils.py

import pandas as pd
from app.models import Student, db

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'csv'}

def process_student_excel(filepath):
    try:
        import pandas as pd
        from app.models import Student, db

        df = pd.read_excel(filepath) if filepath.endswith('xlsx') else pd.read_csv(filepath)
        success, failed = 0, 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Check required fields
                if pd.isna(row['Registration Number']) or pd.isna(row['Student Number']):
                    errors.append(f"Row {index+2}: Missing registration or student number.")
                    failed += 1
                    continue

                # Duplicate checks
                if Student.query.filter_by(registration_number=row['Registration Number']).first():
                    errors.append(f"Row {index+2}: Duplicate registration number.")
                    failed += 1
                    continue

                if Student.query.filter_by(student_number=row['Student Number']).first():
                    errors.append(f"Row {index+2}: Duplicate student number.")
                    failed += 1
                    continue

                # Create new student
                student = Student(
                    full_name=row['Full Name'],
                    gender=row['Gender'],
                    email=row['Email'],
                    phone=row['Phone'],
                    registration_number=row['Registration Number'],
                    student_number=str(row['Student Number']),
                    program=row['Program'],
                    year_of_intake=row['Year of Intake'],
                    research_topic=row['Research Topic']
                )
                db.session.add(student)
                success += 1

            except Exception as e:
                errors.append(f"Row {index+2}: Error - {str(e)}")
                failed += 1

        db.session.commit()
        return {'success': success, 'failed': failed, 'errors': errors}

    except Exception as e:
        return {'success': 0, 'failed': 0, 'errors': [f"File read error: {str(e)}"]}
