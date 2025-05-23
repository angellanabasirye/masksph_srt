from sqlalchemy import func
# from app import db
from flask import request
from flask import Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import RegisterUserForm, RegisterStudentForm
from werkzeug.security import generate_password_hash
from app.forms import RegisterUserForm, RegisterStudentForm, RegisterSupervisorForm, AssignSupervisorsForm
from app.models import db, Student, Supervisor, StudentMilestone, Milestone, User
import os
from werkzeug.utils import secure_filename
from app.data_utils import allowed_file, process_student_excel
from flask import Blueprint, render_template, send_from_directory, current_app
from app.forms import FacultyForm
from app.models import Faculty, Role


# from app.auth_utils import role_required

main = Blueprint('main', __name__)

# ----------------------------------
# Home Page
# ----------------------------------

@main.route('/')
@login_required
def index():

    # Calculate statistics first (common data)
    total_students = Student.query.count()
    total_supervisors = Supervisor.query.count()
    unassigned_students = Student.query.filter(~Student.supervisors.any()).count()

    completed_students = 0
    students = Student.query.all()
    for student in students:
        assigned = student.student_milestones
        if assigned and all(sm.completed for sm in assigned):
            completed_students += 1

    average_completion = round((completed_students / total_students) * 100, 2) if total_students > 0 else 0

    try:
        year_data = (
            db.session.query(Student.year_of_intake, func.count())
            .group_by(Student.year_of_intake)
            .all()
        )
        year_of_intakes = [item[0] for item in year_data]
        intake_counts = [item[1] for item in year_data]
    except AttributeError:
        year_of_intakes = []
        intake_counts = []

    stats = {
        'total_students': total_students,
        'total_supervisors': total_supervisors,
        'unassigned_students': unassigned_students,
        'completed_students': completed_students,
        'average_completion': average_completion,
        'year_of_intakes': year_of_intakes,
        'intake_counts': intake_counts,
    }

    # Role-based dashboard routing
    if current_user.role == 'student':
        return render_template('dashboards/student.html', user=current_user, stats=stats)
    elif current_user.role == 'supervisor':
        return render_template('dashboards/supervisor.html', user=current_user, stats=stats)
    elif current_user.role == 'coordinator':
        return render_template('dashboards/coordinator.html', user=current_user, stats=stats)
    elif current_user.role == 'admin':
        return render_template('dashboards/admin.html', user=current_user, stats=stats)

    # Default fallback (optional)
    return render_template('index.html', stats=stats, user=current_user)

# ----------------------------------
# Register Student
# ----------------------------------
@main.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    form = RegisterStudentForm()
    if form.validate_on_submit():
        reg_number = form.registration_number.data
        student_number = form.student_number.data

        existing = Student.query.filter(
            (Student.registration_number == reg_number) |
            (Student.student_number == student_number)
        ).first()

        if existing:
            flash('A student with this registration or student number already exists.', 'danger')
        else:
            new_student = Student(
                full_name=form.full_name.data,
                gender=form.gender.data,
                email=form.email.data,
                phone=form.phone.data,
                registration_number=reg_number,
                student_number=student_number,
                program=form.program.data,
                year_of_intake=form.year_of_intake.data,
                research_topic=form.research_topic.data
            )
            db.session.add(new_student)
            db.session.commit()
            flash('Student registered successfully.', 'success')
            return redirect(url_for('main.students'))

    return render_template('register.html', form=form, edit_mode=False)


# ----------------------------------
# Register faculty
# ----------------------------------
@main.route('/register-faculty', methods=['GET', 'POST'])
@login_required
def register_faculty():
    form = FacultyForm()

    # Bind submitted roles manually
    if request.method == 'POST':
        form.roles.data = request.form.getlist('roles[]')

    if form.validate_on_submit():
        print("Roles selected:", form.roles.data)
        print("Saving:", form.full_name.data)

        if Faculty.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'danger')
        else:
            new_faculty = Faculty(
                full_name=form.full_name.data,
                email=form.email.data,
                phone=form.phone.data,
                gender=form.gender.data,
                department=form.department.data,
                professional_field=form.professional_field.data
            )
            selected_roles = Role.query.filter(Role.name.in_(form.roles.data)).all()
            new_faculty.roles.extend(selected_roles)

            db.session.add(new_faculty)
            db.session.commit()
            flash('Faculty registered successfully.', 'success')
            return redirect(url_for('main.faculty'))

    else:
        print("Form failed to validate")
        print("Form errors:", form.errors)

    return render_template('register_faculty.html', form=form)


# ----------------------------------
# View faculty list
# ----------------------------------
@main.route('/faculty')
@login_required
def faculty():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    query = Faculty.query
    if search:
        query = query.filter(
            (Faculty.full_name.ilike(f"%{search}%")) |
            (Faculty.email.ilike(f"%{search}%"))
        )

    faculties = query.order_by(Faculty.full_name).paginate(page=page, per_page=10)
    return render_template('faculty.html', faculties=faculties)

# ----------------------------------
# Edit faculty
# ----------------------------------
@main.route('/faculty/edit/<int:faculty_id>', methods=['GET', 'POST'])
@login_required
def edit_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    form = FacultyForm(obj=faculty)

    if request.method == 'POST':
        form.roles.data = request.form.getlist('roles[]')

    if form.validate_on_submit():
        faculty.full_name = form.full_name.data
        faculty.email = form.email.data
        faculty.phone = form.phone.data
        faculty.gender = form.gender.data
        faculty.department = form.department.data
        faculty.professional_field = form.professional_field.data

        selected_roles = Role.query.filter(Role.name.in_(form.roles.data)).all()
        faculty.roles = selected_roles

        db.session.commit()
        flash('Faculty updated successfully.', 'success')
        return redirect(url_for('main.faculty'))

    return render_template('register_faculty.html', form=form, editing=True)

# ----------------------------------
# delete faculty member
# ----------------------------------
@main.route('/faculty/delete/<int:faculty_id>')
@login_required
def delete_faculty(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    db.session.delete(faculty)
    db.session.commit()
    flash('Faculty member deleted successfully.', 'success')
    return redirect(url_for('main.faculty'))


# ----------------------------------
# View assign supervisor
# ----------------------------------
@main.route('/assign-supervisors/<int:student_id>', methods=['GET', 'POST'])
def assign_supervisors_form(student_id):
    student = Student.query.get_or_404(student_id)
    form = AssignSupervisorsForm()

    # Set the choices dynamically
    form.supervisors.choices = [(s.id, s.full_name) for s in Supervisor.query.all()]

    if form.validate_on_submit():
        selected_ids = form.supervisors.data
        selected_supervisors = Supervisor.query.filter(Supervisor.id.in_(selected_ids)).all()
        student.supervisors = selected_supervisors
        db.session.commit()
        flash('Supervisors assigned successfully.', 'success')
        return redirect(url_for('main.students'))

    return render_template('assign_supervisors.html', student=student, form=form)


# ----------------------------------
# View Students (with search + pagination)
# ----------------------------------
@main.route('/students')
def students():
    search = request.args.get('search', '').strip()
    selected_program = request.args.get('program')
    selected_supervisor = request.args.get('supervisor', type=int)
    page = request.args.get('page', 1, type=int)

    supervisors = Supervisor.query.order_by(Supervisor.full_name).all()
    programs = db.session.query(Student.program).distinct().all()

    query = Student.query

    if search:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.student_number.ilike(f"%{search}%"),
                Student.registration_number.ilike(f"%{search}%")
            )
        )

    if selected_program:
        query = query.filter_by(program=selected_program)

    if selected_supervisor:
        query = query.filter_by(supervisor_id=selected_supervisor)

    students = query.order_by(Student.full_name).paginate(page=page, per_page=10)

    return render_template(
        'students.html',
        students=students,
        search=search,
        selected_program=selected_program,
        selected_supervisor=selected_supervisor,
        supervisors=supervisors,
        programs=programs
    )


# ----------------------------------
# Edit Student
# ----------------------------------
@main.route('/edit-student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = RegisterStudentForm(obj=student)

    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(student)
        try:
            db.session.commit()
            flash('Student updated successfully.', 'success')
            return redirect(url_for('main.students'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving student: {str(e)}", 'danger')

    return render_template('register.html', form=form, edit_mode=True, student=student)


# ----------------------------------
# Delete Student
# ----------------------------------
@main.route('/delete-student/<int:student_id>')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.')
    return redirect(url_for('main.students'))

# ----------------------------------
# Manage Milestones
# ----------------------------------
@main.route('/milestones', methods=['GET', 'POST'])
def milestones():
    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        milestone = Milestone(name=name, description=desc)
        db.session.add(milestone)
        db.session.commit()
        flash("Milestone added successfully.")
        return redirect(url_for('main.milestones'))

    all_milestones = Milestone.query.all()
    return render_template('milestones.html', milestones=all_milestones)

# ----------------------------------
# Assign Milestones to Students
# ----------------------------------
@main.route('/assign-milestones/<int:student_id>', methods=['GET', 'POST'])
def assign_milestones(student_id):
    student = Student.query.get_or_404(student_id)
    milestones = Milestone.query.all()

    if request.method == 'POST':
        selected_ids = request.form.getlist('milestones')

        # Remove existing ones to prevent duplicates
        StudentMilestone.query.filter_by(student_id=student.id).delete()

        for milestone_id in selected_ids:
            sm = StudentMilestone(student_id=student.id, milestone_id=int(milestone_id), completed=False)
            db.session.add(sm)

        db.session.commit()
        flash('Milestones assigned successfully.')
        return redirect(url_for('main.students'))

    assigned_ids = {sm.milestone_id for sm in student.student_milestones}
    return render_template('assign_milestones.html', student=student, milestones=milestones, assigned_ids=assigned_ids)

# ----------------------------------
# View Student Progress
# ----------------------------------
@main.route('/student-progress/<int:student_id>', methods=['GET', 'POST'])
def student_progress(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        completed_ids = request.form.getlist('completed')
        for sm in student.student_milestones:
            sm.completed = str(sm.milestone_id) in completed_ids
        db.session.commit()
        flash("Progress updated.")

    total = len(student.student_milestones)
    completed = sum(1 for sm in student.student_milestones if sm.completed)
    percent = int((completed / total) * 100) if total > 0 else 0

    return render_template('student_progress.html', student=student, percent=percent)


@main.route('/create-admin')
def create_admin():
    from app.extensions import db
    admin = User(full_name="System Admin", email="admin@example.com", role="admin")
    admin.set_password("adminpass")
    db.session.add(admin)
    db.session.commit()
    return "Admin created!"

@main.route('/register_user', methods=['GET', 'POST'])
def register_user():
    form = RegisterUserForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully. Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register_user.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for('main.login'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))  # Adjust route as needed
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('main.login'))
        
    get_flashed_messages()
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('main.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    # Calculate statistics (shared across dashboards)
    total_students = Student.query.count()
    total_supervisors = Supervisor.query.count()
    unassigned_students = Student.query.filter(~Student.supervisors.any()).count()

    completed_students = 0
    students = Student.query.all()
    for student in students:
        assigned = student.student_milestones
        if assigned and all(sm.completed for sm in assigned):
            completed_students += 1

    average_completion = round((completed_students / total_students) * 100, 2) if total_students > 0 else 0

    try:
        year_data = (
            db.session.query(Student.year_of_intake, func.count())
            .group_by(Student.year_of_intake)
            .all()
        )
        year_of_intakes = [item[0] for item in year_data]
        intake_counts = [item[1] for item in year_data]
    except AttributeError:
        year_of_intakes = []
        intake_counts = []

    stats = {
        'total_students': total_students,
        'total_supervisors': total_supervisors,
        'unassigned_students': unassigned_students,
        'completed_students': completed_students,
        'average_completion': average_completion,
        'year_of_intakes': year_of_intakes,
        'intake_counts': intake_counts,
    }

    role = current_user.role
    if role == 'admin':
        return render_template('dashboards/admin.html', user=current_user, stats=stats)
    elif role == 'coordinator':
        return render_template('dashboards/coordinator.html', user=current_user, stats=stats)
    elif role == 'supervisor':
        return render_template('dashboards/supervisor.html', user=current_user, stats=stats)
    elif role == 'student':
        return render_template('dashboards/student.html', user=current_user, stats=stats)
    else:
        flash('Unknown role. Contact administrator.', 'danger')
        return redirect(url_for('main.logout'))


from app.auth_utils import admin_required


@main.route('/supervisors')
@login_required
def supervisors():
    search_query = request.args.get('search', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Supervisor.query
    if search_query:
        search = f"%{search_query}%"
        query = query.filter((Supervisor.full_name.ilike(search)) | (Supervisor.email.ilike(search)))

    paginated_supervisors = query.order_by(Supervisor.full_name).paginate(page=page, per_page=per_page)
    return render_template('supervisors.html', supervisors=paginated_supervisors)

@main.route('/supervisors/edit/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def edit_supervisor(supervisor_id):
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    form = RegisterSupervisorForm(obj=supervisor)

    if form.validate_on_submit():
        supervisor.full_name = form.full_name.data
        supervisor.email = form.email.data
        supervisor.phone = form.phone.data
        supervisor.gender = form.gender.data
        supervisor.department = form.department.data
        db.session.commit()
        flash('Supervisor updated successfully.', 'success')
        return redirect(url_for('main.supervisors'))

    return render_template('register_supervisor.html', form=form, editing=True)


@main.route('/supervisors/delete/<int:supervisor_id>')
@login_required
def delete_supervisor(supervisor_id):
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    db.session.delete(supervisor)
    db.session.commit()
    flash('Supervisor deleted.', 'success')
    return redirect(url_for('main.supervisors'))


from flask import send_from_directory, current_app

@main.route('/download-template')
def download_excel_template():  
    return send_from_directory(
        directory=current_app.static_folder,
        path='student_bulk_template.xlsx',
        as_attachment=True
    )

@main.route('/upload-bulk-students', methods=['POST'])
def upload_bulk_students():
    file = request.files.get('bulk_file')
    
    if file and allowed_file(file.filename):
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(filepath)

        result = process_student_excel(filepath)
        
        # Display feedback
        if result['success']:
            flash(f"{result['success']} students registered successfully.", "success")
        if result['failed']:
            for error in result['errors']:
                flash(error, "danger")
    else:
        flash("Invalid file. Only .xlsx or .csv formats are allowed.", "danger")

    return redirect(url_for('main.register'))

@main.route('/debug-static')
def debug_static():
    return f"Static folder path: {current_app.static_folder}"
