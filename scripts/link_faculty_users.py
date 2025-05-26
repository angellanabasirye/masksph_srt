# scripts/link_faculty_users.py

import os
import sys
from werkzeug.security import generate_password_hash

# Ensure the app root is in the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from app import create_app, db
from app.models import Faculty, User

app = create_app()

with app.app_context():
    created, linked = 0, 0

    faculty_members = Faculty.query.all()

    for faculty in faculty_members:
        # Check if already linked
        if faculty.user_id:
            continue

        user = User.query.filter_by(email=faculty.email).first()

        if user:
            faculty.user_id = user.id
            linked += 1
        else:
            user = User(
                full_name=faculty.full_name,
                email=faculty.email,
                role='faculty',
                password=generate_password_hash("12345")
            )
            db.session.add(user)
            db.session.flush()  # Ensures user.id is available
            faculty.user_id = user.id
            created += 1

    db.session.commit()

    print(f"✅ Linked {linked} existing users to faculty.")
    print(f"✅ Created and linked {created} new user accounts.")
