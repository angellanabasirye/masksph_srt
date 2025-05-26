from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms import StringField, SelectField, SelectMultipleField, SubmitField, TelField, HiddenField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models import User, Student
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import InputRequired, DataRequired, Email

class RegisterUserForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
        ('student', 'Student'),
        ('coordinator', 'Program Coordinator')
    ], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email is already registered.')

    def validate_full_name(self, full_name):
        if User.query.filter_by(full_name=full_name.data).first():
            raise ValidationError('Username already exists.')


class RegisterStudentForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(min=10, max=15)])
    registration_number = StringField('Registration Number', validators=[DataRequired()])
    student_number = StringField('Student Number', validators=[DataRequired()])
    program = SelectField('Program', choices=[
        ('MHI', 'Master of Health Informatics'),
        ('MPH', 'Master of Public Health'),
        ('MScEpi', 'MSc Epidemiology'),
        ('PhD', 'PhD in Health Sciences'),
        # Add more programs as needed
    ], validators=[DataRequired()])
    year_of_intake = StringField('Year of Intake', validators=[DataRequired()])
    research_topic = StringField('Research Topic', validators=[DataRequired()])
    submit = SubmitField('Register Student')

    def __init__(self, *args, **kwargs):
        self._obj = kwargs.get('obj')  
        super().__init__(*args, **kwargs)

    def validate_registration_number(self, field):
        existing = Student.query.filter_by(registration_number=field.data).first()
        if existing and (not self._obj or existing.id != self._obj.id):
            raise ValidationError('Registration number already exists.')

    def validate_student_number(self, field):
        existing = Student.query.filter_by(student_number=field.data).first()
        if existing and (not self._obj or existing.id != self._obj.id):
            raise ValidationError('Student number already exists.')
        
class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()
        

class AssignSupervisorsForm(FlaskForm):
    supervisors = SelectMultipleField(
        'Select Supervisors',
        coerce=int,  # assuming Supervisor.id is an integer
        validators=[DataRequired()],
        render_kw={"class": "form-control"}
    )
    submit = SubmitField('Assign Supervisors')

class RegisterSupervisorForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone')
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')])
    department = StringField('Department', validators=[DataRequired()])
    professional_field = StringField('Professional Field', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if Supervisor.query.filter_by(email=email.data).first():
            raise ValidationError('This email is already registered.')
        

class FacultyForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = TelField('Phone', validators=[DataRequired()])
    # department = StringField('Department', validators=[DataRequired()])
    department = SelectField('Department', choices=[
    ('', 'Select Department'),  # Placeholder
    ('Epidemiology and Biostatistics', 'Epidemiology and Biostatistics'),
    ('Health Policy, Planning and Management', 'Health Policy, Planning and Management'),
    ('Community Health and Behavioural Sciences', 'Community Health and Behavioural Sciences'),
    ('Disease Control and Environmental Health', 'Disease Control and Environmental Health'),
    ('Other', 'Other')
    ], validators=[DataRequired(message="Please select a department.")])
    professional_field = StringField('Professional Field')
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    roles = SelectMultipleField('Role(s)', choices=[
    ('Supervisor', 'Supervisor'),
    ('Program Coordinator', 'Program Coordinator'),
    ('Overseer', 'Overseer'),
    ('Program Admin', 'Program Administrator')
], validators=[DataRequired(message="Please select at least one role.")])
    submit = SubmitField('Register')

class AssignSupervisorsForm(FlaskForm):
    supervisors = MultiCheckboxField(
        'Select Supervisors',
        coerce=int,
        validators=[InputRequired(message="Select at least one supervisor.")]
    )
    submit = SubmitField('Assign')

