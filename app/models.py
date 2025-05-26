from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.extensions import db
from app import db

faculty_roles = db.Table('faculty_roles',
    db.Column('faculty_id', db.Integer, db.ForeignKey('faculty.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

student_supervisors = db.Table(
    'student_supervisors',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('faculty_id', db.Integer, db.ForeignKey('faculty.id'), primary_key=True)
)

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20))  # ← ADD THIS LINE
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    student_number = db.Column(db.String(50), unique=True, nullable=False)
    program = db.Column(db.String(100), nullable=False)
    year_of_intake = db.Column(db.String(10), nullable=False)
    research_topic = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

    supervisors = db.relationship('Faculty', secondary='student_supervisors', back_populates='students')
    student_milestones = db.relationship('StudentMilestone', back_populates='student')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    user = db.relationship('User', back_populates='student_profile')     

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_login = db.Column(db.Boolean, default=True)  
    student_profile = db.relationship('Student', back_populates='user', uselist=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


from datetime import datetime

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    professional_field = db.Column(db.String(100), nullable=True)

    roles = db.relationship('Role', secondary=faculty_roles, backref=db.backref('faculties', lazy='dynamic'))
    students = db.relationship(
        'Student',
        secondary='student_supervisors',
        back_populates='supervisors'
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = db.relationship('User', backref='faculty_profile', uselist=False)

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    subtasks = db.relationship('Subtask', backref='milestone', lazy=True)


class Subtask(db.Model):
    __tablename__ = 'subtasks'
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)


class StudentMilestone(db.Model):
    __tablename__ = 'student_milestones'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    student = db.relationship('Student', back_populates='student_milestones') 
    milestone = db.relationship('Milestone', backref='student_milestones')


class StudentSubtask(db.Model):
    __tablename__ = 'student_subtasks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subtask_id = db.Column(db.Integer, db.ForeignKey('subtasks.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending | in_progress | completed
    comment = db.Column(db.Text)
    date_completed = db.Column(db.DateTime)
