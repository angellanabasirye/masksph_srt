"""
Run this script to generate dummy data for the Student Research Tracking app.
USAGE:
    python scripts/load_dummy_data.py
"""

from app import create_app, db
from app.models import User, Faculty, Student, StudentMilestone, Subtask, SubtaskComment
from werkzeug.security import generate_password_hash
from faker import Faker
import random

fake = Faker()

app = create_app()

with app.app_context():
    # 1. OPTIONAL: Clean out existing data for a fresh start
    print("Deleting existing data...")
    db.session.query(SubtaskComment).delete()
    db.session.query(Subtask).delete()
    db.session.query(StudentMilestone).delete()
    db.session.query(Student).delete()
    db.session.query(Faculty).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("✅ Old data cleared.")

    # 2. Create an admin user
    admin_user = User(
        full_name="Admin User",
        email="admin@example.com",
        role="Admin",
        password=generate_password_hash("12345"),
    )
    db.session.add(admin_user)

    # 3. Create several supervisors
    supervisors = []
    for i in range(3):
        full_name = fake.name()
        email = f"supervisor{i}@example.com"

        user = User(
            full_name=full_name,
            email=email,
            role="Supervisor",
            password=generate_password_hash("12345"),
        )
        db.session.add(user)
        db.session.flush()

        faculty = Faculty(
            full_name=full_name,
            email=email,
            professional_field="Supervisor",
            user_id=user.id,
        )
        db.session.add(faculty)
        supervisors.append(faculty)

    # 4. Create multiple students
    students = []
    for i in range(10):
        full_name = fake.name()
        email = f"student{i}@example.com"

        user = User(
            full_name=full_name,
            email=email,
            role="Student",
            password=generate_password_hash("12345"),
        )
        db.session.add(user)
        db.session.flush()

        student = Student(
            full_name=full_name,
            email=email,
            gender=random.choice(["Male", "Female"]),
            phone=fake.phone_number(),
            registration_number=f"REG{i:04}",
            student_number=f"SN{i:04}",
            program=random.choice(["Health Informatics", "Public Health", "Epidemiology"]),
            year_of_intake=random.choice(["2022/2023", "2023/2024", "2024/2025"]),
            research_topic=fake.sentence(nb_words=6),
            user_id=user.id,
        )
        db.session.add(student)
        students.append(student)

        # Assign random supervisors to this student
        assigned_supervisors = random.sample(supervisors, k=random.randint(1, 2))
        for sup in assigned_supervisors:
            student.supervisors.append(sup)

    db.session.flush()

    # 5. Create milestones and subtasks for each student
    milestone_names = [
        "Concept Presentation",
        "Proposal Development",
        "Data Collection",
        "Data Analysis",
        "Thesis Writing",
        "Thesis Defense"
    ]

    subtask_templates = [
        "Prepare initial draft",
        "Submit revised draft",
        "Review by supervisor",
        "Finalize submission"
    ]

    for student in students:
        for milestone_name in milestone_names:
            milestone = StudentMilestone(
                milestone_name=milestone_name,
                student=student,
                completed=False,
            )
            db.session.add(milestone)
            db.session.flush()

            # Create subtasks under this milestone
            for subtask_name in subtask_templates:
                subtask = Subtask(
                    name=subtask_name,
                    milestone_id=milestone.id,
                    status=random.choice(["pending", "in_progress", "ready", "completed"])
                )
                db.session.add(subtask)
                db.session.flush()

                # Add comments from supervisor
                for j in range(random.randint(0, 2)):
                    commenter = random.choice(supervisors)
                    comment = SubtaskComment(
                        subtask_id=subtask.id,
                        user_id=commenter.user_id,
                        content=fake.sentence(nb_words=10),
                        is_read=False
                    )
                    db.session.add(comment)

    db.session.commit()
    print("✅ Dummy data loaded successfully!")
