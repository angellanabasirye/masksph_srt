from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models import User, Student, Supervisor
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms import HiddenField

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

    def validate_registration_number(self, field):
        if Student.query.filter_by(registration_number=field.data).first():
            raise ValidationError('Registration number already exists.')

    def validate_student_number(self, field):
        if Student.query.filter_by(student_number=field.data).first():
            raise ValidationError('Student number already exists.')
        
class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class RegisterSupervisorForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Length(max=15)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    
    submit = SubmitField('Register Supervisor')

    def validate_email(self, email):
        if Supervisor.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')
        

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
        

class AssignSupervisorsForm(FlaskForm):
    student = HiddenField()
    supervisors = SelectMultipleField('Select Supervisors', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign')
    