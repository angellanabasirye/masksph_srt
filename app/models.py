from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
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
    db.Column('supervisor_id', db.Integer, db.ForeignKey('supervisor.id'), primary_key=True)
)

class StudentMilestone(db.Model):
    __tablename__ = 'student_milestone'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestone.id'))
    completed = db.Column(db.Boolean, default=False)

    student = db.relationship('Student', back_populates='student_milestones')
    milestone = db.relationship('Milestone')

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    registration_number = db.Column(db.String(50), unique=True)
    student_number = db.Column(db.String(50), unique=True)
    program = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    year_of_intake = db.Column(db.String(20))
    research_topic = db.Column(db.String(255))
    
    student_milestones = db.relationship('StudentMilestone', back_populates='student')
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'))
    supervisors = db.relationship(
        'Supervisor',
        secondary=student_supervisors,
        back_populates='students'
    )

class Supervisor(db.Model):
    __tablename__ = 'supervisor'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    department = db.Column(db.String(100))
    professional_field = db.Column(db.String(100))

    students = db.relationship(
        'Student',
        secondary=student_supervisors,
        back_populates='supervisors'
    )

class Milestone(db.Model):
    __tablename__ = 'milestone'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, full_name=None, email=None, role=None, password=None):
        self.full_name = full_name
        self.email = email
        self.role = role
        if password:
            self.set_password(password)

    def __repr__(self):
        return f"<User {self.full_name}>"
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

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
