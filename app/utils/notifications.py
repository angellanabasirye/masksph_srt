# app/utils/notifications.py

from app.models import SubtaskComment, StudentSubtask, Student, Faculty
from flask_login import current_user
from sqlalchemy.orm import joinedload


def get_student_unread_count(user_id):
    """Count unread comments for a student (excluding their own)."""
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return 0

    subtask_ids = [s.subtask_id for s in StudentSubtask.query.filter_by(student_id=student.id).all()]

    return SubtaskComment.query.filter(
        SubtaskComment.subtask_id.in_(subtask_ids),
        SubtaskComment.user_id != user_id,
        SubtaskComment.is_read == False
    ).count()


def get_supervisor_unread_count(user_id):
    """Count unread comments for subtasks under the supervisor’s students."""
    faculty = Faculty.query.filter_by(user_id=user_id).first()
    if not faculty:
        return 0

    student_ids = [s.id for s in faculty.students]

    subtask_ids = [s.subtask_id for s in StudentSubtask.query.filter(
        StudentSubtask.student_id.in_(student_ids)
    ).all()]

    return SubtaskComment.query.filter(
        SubtaskComment.subtask_id.in_(subtask_ids),
        SubtaskComment.user_id != user_id,
        SubtaskComment.is_read == False
    ).count()
