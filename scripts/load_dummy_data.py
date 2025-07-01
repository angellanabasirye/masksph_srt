# WARNING:
# This script deletes ALL DATA and loads dummy test data.
# Do NOT run this on production databases.

import random
from faker import Faker
from sqlalchemy import text
from app import create_app, db
from app.models import (
    User,
    Role,
    Faculty,
    Student,
    StudentMilestone,
    Milestone,
    Subtask,
    StudentSubtask,
    SubtaskComment
)

app = create_app()
fake = Faker()

programs = [
    "MHI",         # Master of Health Informatics
    "MPH",         # Master of Public Health
    "MScEpi",      # MSc Epidemiology
    "PhD"          # PhD in Health Sciences
]

years = [
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2025/2026"
]

departments = [
    "Epidemiology and Biostatistics",
    "Health Policy, Planning and Management",
    "Community Health and Behavioural Sciences",
    "Disease Control and Environmental Health",
    "Other"
]

milestones_data = [
    {
        "name": "Concept Presentation and Approval",
        "description": "Initial research idea development and approval process.",
        "subtasks": [
            "Submit 3 initial concepts to supervisor",
            "Select 1 concept and refine",
            "Format final concept per school guidelines",
            "Supervisor reviews and approves final concept",
            "Submit concept to faculty",
            "Faculty presentation",
            "Faculty approval of concept"
        ]
    },
    {
        "name": "Proposal Writing",
        "description": "Drafting and revising the research proposal.",
        "subtasks": [
            "Begin writing proposal",
            "Submit draft to supervisor",
            "Receive supervisor feedback",
            "Resolve supervisor comments",
            "Supervisor approves final proposal"
        ]
    },
    {
        "name": "Proposal Defence and Approval",
        "description": "Formal defense of proposal before faculty.",
        "subtasks": [
            "Await defense scheduling",
            "Defend before faculty",
            "Faculty decision",
            "Resolve defense comments (if any)",
            "Final approval by faculty"
        ]
    },
    {
        "name": "Dissertation Writing",
        "description": "Research execution and dissertation documentation.",
        "subtasks": [
            "Begin dissertation writing",
            "Submit sections to supervisor",
            "Submit complete draft to supervisor",
            "Supervisor review",
            "Resolve comments",
            "Supervisor final approval",
            "Submit final for signatures"
        ]
    },
    {
        "name": "Dissertation Defence",
        "description": "Final oral defense of dissertation.",
        "subtasks": [
            "Await defense scheduling",
            "Defend dissertation",
            "Receive committee feedback",
            "Resolve committee comments",
            "Submit revised version for approval"
        ]
    },
    {
        "name": "Compliance and Final Dissertation Submission",
        "description": "Final checks and submission of signed dissertation.",
        "subtasks": [
            "Await compliance sign-off",
            "Submit final signed dissertation"
        ]
    }
]

with app.app_context():
    # ---------------------------
    # Wipe all existing data
    # ---------------------------
    print("🧹 Deleting old data...")

    db.session.execute(text("DELETE FROM subtask_comment"))
    db.session.execute(text("DELETE FROM student_subtask"))
    db.session.execute(text("DELETE FROM student_milestones"))
    db.session.execute(text("DELETE FROM student_supervisors"))
    db.session.execute(text("DELETE FROM milestone_upload"))
    db.session.execute(text("DELETE FROM subtasks"))
    db.session.execute(text("DELETE FROM milestones"))
    db.session.execute(text("DELETE FROM student"))
    db.session.execute(text("DELETE FROM faculty_roles"))
    db.session.execute(text("DELETE FROM faculty"))
    db.session.execute(text("DELETE FROM role"))
    db.session.execute(text("DELETE FROM \"user\""))

    db.session.commit()
    print("✅ All old data deleted.")

    # ---------------------------
    # Create Roles
    # ---------------------------
    print("🎭 Creating roles...")
    role_names = ["Supervisor", "Program Coordinator", "Overseer", "Program Admin", "Admin", "Student"]
    role_objs = {}
    for name in role_names:
        r = Role(name=name)
        db.session.add(r)
        role_objs[name] = r
    db.session.commit()
    print("✅ Roles created.")

    # ---------------------------
    # Create Dummy Faculty
    # ---------------------------
    print("👩‍🏫 Creating dummy faculty...")

    supervisors = []
    coordinators = []
    faculty_members = []

    for i in range(3):
        full_name = fake.name()
        email = f"supervisor{i}@example.com"

        user = User(
            full_name=full_name,
            email=email,
            role="faculty"
        )
        user.set_password("12345")
        db.session.add(user)
        db.session.flush()

        faculty = Faculty(
            full_name=full_name,
            email=email,
            phone=fake.phone_number()[:20],
            gender=random.choice(["Male", "Female"]),
            department=random.choice(departments),
            professional_field="Supervisor",
            user_id=user.id
        )
        faculty.roles.append(role_objs["Supervisor"])
        db.session.add(faculty)
        supervisors.append(faculty)
        faculty_members.append(faculty)

    for i in range(2):
        full_name = fake.name()
        email = f"coordinator{i}@example.com"

        user = User(
            full_name=full_name,
            email=email,
            role="faculty"
        )
        user.set_password("12345")
        db.session.add(user)
        db.session.flush()

        faculty = Faculty(
            full_name=full_name,
            email=email,
            phone=fake.phone_number()[:20],
            gender=random.choice(["Male", "Female"]),
            department=random.choice(departments),
            professional_field="Coordinator",
            user_id=user.id
        )
        faculty.roles.append(role_objs["Program Coordinator"])
        db.session.add(faculty)
        coordinators.append(faculty)
        faculty_members.append(faculty)

    db.session.commit()
    print(f"✅ Created {len(supervisors)} supervisors and {len(coordinators)} coordinators.")

    # ---------------------------
    # Create Dummy Students
    # ---------------------------
    print("🎓 Creating dummy students...")

    students = []
    for i in range(10):
        full_name = fake.name()
        email = f"student{i}@example.com"
        reg_number = f"REG{str(i).zfill(4)}"
        student_number = f"SN{str(i).zfill(4)}"

        user = User(
            full_name=full_name,
            email=email,
            role="student"
        )
        user.set_password("12345")
        db.session.add(user)
        db.session.flush()

        student = Student(
            full_name=full_name,
            email=email,
            gender=random.choice(["Male", "Female"]),
            phone=fake.phone_number()[:20],
            registration_number=reg_number,
            student_number=student_number,
            program=random.choice(programs),
            year_of_intake=random.choice(years),
            research_topic=fake.sentence(),
            user_id=user.id
        )
        db.session.add(student)

        # Randomly assign 1-2 supervisors
        assigned_supervisors = random.sample(supervisors, k=min(2, len(supervisors)))
        for sup in assigned_supervisors:
            student.supervisors.append(sup)

        students.append(student)

    db.session.commit()
    print(f"✅ Created {len(students)} students.")

    # ---------------------------
    # Create Admin User
    # ---------------------------
    print("🛠️ Creating admin user...")
    admin_user = User(
        full_name="Admin User",
        email="admin@example.com",
        role="admin"
    )
    admin_user.set_password("12345")
    db.session.add(admin_user)
    db.session.commit()
    print("✅ Admin user created.")

    # ---------------------------
    # Create Milestones + Subtasks
    # ---------------------------
    print("🗂️ Creating milestones and subtasks...")

    milestones = []
    for mdata in milestones_data:
        milestone = Milestone(name=mdata["name"], description=mdata["description"])
        db.session.add(milestone)
        db.session.flush()

        for idx, st_name in enumerate(mdata["subtasks"], start=1):
            subtask = Subtask(
                milestone_id=milestone.id,
                name=st_name,
                sequence_order=idx
            )
            db.session.add(subtask)

        milestones.append(milestone)

    db.session.commit()
    print(f"✅ Created {len(milestones)} milestones and all subtasks.")

    # ---------------------------
    # Assign milestones + subtasks to students
    # ---------------------------
    print("🔗 Linking milestones and subtasks to students...")

    subtasks = Subtask.query.all()

    for student in students:
        for milestone in milestones:
            sm = StudentMilestone(
                student_id=student.id,
                milestone_id=milestone.id,
                completed=random.choice([True, False]),
                in_progress=random.choice([True, False])
            )
            db.session.add(sm)

            milestone_subtasks = [s for s in subtasks if s.milestone_id == milestone.id]

            for subtask in milestone_subtasks:
                sst = StudentSubtask(
                    student_id=student.id,
                    subtask_id=subtask.id,
                    status=random.choice(['pending', 'in_progress', 'ready', 'completed'])
                )
                db.session.add(sst)

                # Add dummy comments randomly
                if random.choice([True, False]):
                    comment = SubtaskComment(
                        subtask_id=subtask.id,
                        user_id=student.user_id,
                        content=fake.sentence(),
                        is_read=False
                    )
                    db.session.add(comment)

    db.session.commit()
    print("✅ Dummy milestones, subtasks, and comments assigned to students.")

    print("🎉 Dummy data loaded successfully!")
