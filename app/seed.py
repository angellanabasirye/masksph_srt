from flask import Blueprint
from app.models import db, Milestone, Subtask

seed_bp = Blueprint('seed', __name__)

@seed_bp.route('/seed-milestones')
def seed_milestones():
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

    for m in milestones_data:
        milestone = Milestone.query.filter_by(name=m["name"]).first()
        if not milestone:
            milestone = Milestone(name=m["name"], description=m["description"])
            db.session.add(milestone)
            db.session.flush()

        for i, subtask_name in enumerate(m["subtasks"], start=1):
            existing = Subtask.query.filter_by(milestone_id=milestone.id, name=subtask_name).first()
            if not existing:
                subtask = Subtask(
                    milestone_id=milestone.id,
                    name=subtask_name,
                    sequence_order=i
                )
                db.session.add(subtask)

    db.session.commit()
    return "Milestones and subtasks seeded successfully!"

@seed_bp.route('/link-students-to-users')
def link_students_to_users():
    from app.models import Student, User
    linked = 0

    # Assumes student emails match user emails
    for student in Student.query.filter_by(user_id=None).all():
        user = User.query.filter_by(email=student.email).first()
        if user:
            student.user_id = user.id
            linked += 1

    db.session.commit()
    return f"Linked {linked} students to users."
