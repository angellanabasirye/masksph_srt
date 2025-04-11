from . import db

student_supervisors = db.Table('student_supervisors',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
    db.Column('supervisor_id', db.Integer, db.ForeignKey('supervisor.id'))
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
    supervisors = db.relationship('Supervisor', secondary=student_supervisors, back_populates='students')


class Supervisor(db.Model):
    __tablename__ = 'supervisor'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    department = db.Column(db.String(100))

    students = db.relationship('Student', secondary=student_supervisors, back_populates='supervisors')

class Milestone(db.Model):
    __tablename__ = 'milestone'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)


