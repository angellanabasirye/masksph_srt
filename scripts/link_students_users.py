import os
import sys

# Ensure app directory is on sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from app import create_app, db
from app.models import Student, User

app = create_app()

with app.app_context():
    linked_count = 0
    created_count = 0

    students = Student.query.filter_by(user_id=None).all()

    for student in students:
        # Try to find user by email
        user = User.query.filter_by(email=student.email).first()

        if not user:
            # Create a new user
            user = User(
                full_name=student.full_name,
                email=student.email,
                role='student'
            )
            user.set_password("12345")  # assumes a set_password method exists
            db.session.add(user)
            db.session.flush()
            created_count += 1

        # Link the student to the user
        student.user_id = user.id
        linked_count += 1

    db.session.commit()
    print(f"✅ Linked {linked_count} students to users.")
    print(f"✅ Created {created_count} new user accounts.")
