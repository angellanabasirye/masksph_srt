from sqlalchemy import func
# from app import db
from flask import request
from flask import Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import RegisterUserForm, RegisterStudentForm
from werkzeug.security import generate_password_hash
from app.forms import RegisterUserForm, RegisterStudentForm, RegisterSupervisorForm, AssignSupervisorsForm
from app.models import db, Student, StudentMilestone, Milestone, User, Subtask, StudentSubtask
import os
from werkzeug.utils import secure_filename
from app.data_utils import allowed_file, process_student_excel
from flask import Blueprint, render_template, send_from_directory, current_app
from app.forms import FacultyForm
from app.models import Faculty, Role, Milestone, Student

from collections import defaultdict
from datetime import datetime
from sqlalchemy import func, extract
from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

# ----------------------------------
# Home Page
# ----------------------------------

@main.route('/')
@login_required
def index():
    # Gather common statistics
    total_students = Student.query.count()
    total_supervisors = Faculty.query.filter(Faculty.roles.any(name='Supervisor')).count()
    unassigned_students = Student.query.filter(~Student.supervisors.any()).count()

    completed_students = 0
    students = Student.query.all()
    for student in students:
        assigned = student.student_milestones
        if assigned and all(sm.completed for sm in assigned):
            completed_students += 1

    average_completion = round((completed_students / total_students) * 100, 2) if total_students > 0 else 0

    # Yearly intake distribution
    try:
        year_data = (
            db.session.query(Student.year_of_intake, func.count())
            .group_by(Student.year_of_intake)
            .all()
        )
        year_of_intakes = [item[0] for item in year_data]
        intake_counts = [item[1] for item in year_data]
    except Exception:
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

    # Role-based redirection
    role = current_user.role.lower() if current_user.role else ""

    if role == 'student':
        return render_template('dashboards/student.html', user=current_user, stats=stats)
    elif role == 'supervisor':
        return render_template('dashboards/supervisor.html', user=current_user, stats=stats)
    elif role == 'coordinator':
        return render_template('dashboards/coordinator.html', user=current_user, stats=stats)
    elif role == 'admin':
        return render_template('dashboards/admin.html', user=current_user, stats=stats)
    else:
        flash("Unrecognized role. Please contact the system administrator.", "danger")
        return redirect(url_for('main.logout'))

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
            # Create user for the student
            user = User(
                full_name=form.full_name.data,
                email=form.email.data,
                role='student'
            )
            user.set_password('12345')
            db.session.add(user)
            db.session.flush()  # get user.id

            new_student = Student(
                user_id=user.id,
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
@main.route('/register_faculty', methods=['GET', 'POST'])
@login_required
def register_faculty():
    form = FacultyForm()

    form.roles.data = request.form.getlist("roles")
    selected_roles = form.roles.data  
    role_objects = Role.query.filter(Role.name.in_(selected_roles)).all()

    if form.validate_on_submit():
        email = form.email.data
        full_name = form.full_name.data

        existing_faculty = Faculty.query.filter_by(email=email).first()
        existing_user = User.query.filter_by(email=email).first()

        if existing_faculty or existing_user:
            flash("Faculty with this email already exists.", "danger")
            return redirect(url_for('main.register_faculty'))

        # Create User account
        new_user = User(
            full_name=full_name,
            email=email,
            role="faculty",
            password=generate_password_hash("12345") 
            
        )
        db.session.add(new_user)
        db.session.flush()  # so user.id is available

        # Create Faculty profile
        new_faculty = Faculty(
            full_name=full_name,
            email=email,
            phone=form.phone.data,
            gender=form.gender.data,
            department=form.department.data,
            professional_field=form.professional_field.data,
            user_id=new_user.id,
            roles=role_objects
        )
        db.session.add(new_faculty)
        db.session.commit()

        flash(f"Faculty {full_name} registered successfully.", "success")
        return redirect(url_for('main.faculty'))

    if form.errors:
        print("Form Errors:", form.errors)

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
def assign_supervisors(student_id):
    student = Student.query.get_or_404(student_id)

    supervisors = Faculty.query.filter(Faculty.roles.any(name='Supervisor')).all()

    form = AssignSupervisorsForm()
    form.supervisors.choices = [
        (s.id, f"{s.full_name} - {s.department or 'N/A'} - {s.professional_field or 'N/A'}")
        for s in supervisors
    ]

    if form.validate_on_submit():
        selected_supervisors = Faculty.query.filter(Faculty.id.in_(form.supervisors.data)).all()
        student.supervisors = selected_supervisors
        db.session.commit()
        flash("Supervisors assigned successfully.", "success")
        return redirect(url_for('main.students', student_id=student.id))

    return render_template('assign_supervisors.html', student=student, form=form)


# ----------------------------------
# View Students (with search + pagination)
# ----------------------------------
# @main.route('/students')
# def students():
#     search = request.args.get('search', '').strip()
#     selected_program = request.args.get('program')
#     selected_supervisor = request.args.get('supervisor', type=int)
#     page = request.args.get('page', 1, type=int)

#     supervisors = Faculty.query.filter(Faculty.roles.any(name='Supervisor')).order_by(Faculty.full_name).all()
#     programs = db.session.query(Student.program).distinct().all()

#     query = Student.query

#     if search:
#         query = query.filter(
#             db.or_(
#                 Student.full_name.ilike(f"%{search}%"),
#                 Student.student_number.ilike(f"%{search}%"),
#                 Student.registration_number.ilike(f"%{search}%")
#             )
#         )

#     if selected_program:
#         query = query.filter_by(program=selected_program)

#     if selected_supervisor:
#         query = query.filter_by(supervisor_id=selected_supervisor)

#     students = query.order_by(Student.full_name).paginate(page=page, per_page=10)

#     return render_template(
#         'students.html',
#         students=students,
#         search=search,
#         selected_program=selected_program,
#         selected_supervisor=selected_supervisor,
#         supervisors=supervisors,
#         programs=programs
#     )

@main.route('/students')
@login_required
def students():
    search = request.args.get('search')
    selected_program = request.args.get('program')
    selected_supervisor = request.args.get('supervisor')
    selected_year = request.args.get('year_of_intake')

    query = Student.query

    # Search filter
    if search:
        query = query.filter(
            Student.full_name.ilike(f'%{search}%') |
            Student.student_number.ilike(f'%{search}%') |
            Student.registration_number.ilike(f'%{search}%')
        )

    # Program filter
    if selected_program:
        query = query.filter_by(program=selected_program)

    # Supervisor filter
    if selected_supervisor:
        query = query.join(Student.supervisors).filter(Faculty.id == selected_supervisor)

    # Year of intake filter
    if selected_year:
        query = query.filter_by(year_of_intake=selected_year)

    # Only students with milestones assigned (optional logic)
    query = query.filter(Student.student_milestones.any())

    # Get distinct values for dropdown filters
    programs = db.session.query(Student.program).filter(Student.program.isnot(None)).distinct().all()
    supervisors = Faculty.query.filter(Faculty.roles.any(name='Supervisor')).all()
    years = db.session.query(Student.year_of_intake).filter(Student.year_of_intake.isnot(None)).distinct().order_by(Student.year_of_intake).all()
    years = [y[0] for y in years]

    return render_template(
        'students.html',
        students=query.all(),
        search=search,
        selected_program=selected_program,
        selected_supervisor=selected_supervisor,
        selected_year=selected_year,
        programs=programs,
        supervisors=supervisors,
        years=years
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

        # Reassign all milestones
        StudentMilestone.query.filter_by(student_id=student.id).delete()

        for milestone_id in selected_ids:
            sm = StudentMilestone(student_id=student.id, milestone_id=int(milestone_id), completed=False)
            db.session.add(sm)

        db.session.commit()
        flash('Milestones assigned successfully.')
        return redirect(url_for('main.students'))

    assigned_ids = {sm.milestone_id for sm in student.student_milestones}

    # Load subtasks with student status
    milestone_subtasks = {}
    for milestone in milestones:
        subtasks = Subtask.query.filter_by(milestone_id=milestone.id).order_by(Subtask.sequence_order).all()
        subtasks_with_status = []
        for st in subtasks:
            status_entry = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=st.id).first()
            subtasks_with_status.append({
                'subtask': st,
                'status': status_entry.status if status_entry else 'pending',
                'comment': status_entry.comment if status_entry else ''
            })
        milestone_subtasks[milestone.id] = subtasks_with_status

    return render_template(
        'assign_milestones.html',
        student=student,
        milestones=milestones,
        assigned_ids=assigned_ids,
        milestone_subtasks=milestone_subtasks
    )


@main.route('/seed-milestones')
def seed_milestones():
    default_milestones = [
        "Concept presentation and approval",
        "Proposal writing",
        "Proposal defence and approval",
        "Dissertation writing",
        "Dissertation Defence",
        "Compliance and Final dissertation submission"
    ]

    for name in default_milestones:
        if not Milestone.query.filter_by(name=name).first():
            db.session.add(Milestone(name=name))
    db.session.commit()
    return "Milestones seeded successfully."


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
            # flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))

        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html')


@main.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm = request.form.get('confirm_password')

        if not new_password or new_password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('main.change_password'))

        current_user.set_password(new_password)
        current_user.first_login = False
        db.session.commit()

        flash("Password changed successfully.", "success")

        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('main.dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('main.student_dashboard'))
        elif current_user.role == 'supervisor' or current_user.role == 'faculty':
            return redirect(url_for('main.supervisor_dashboard'))

    return render_template('change_password.html')



@main.route('/logout')
@login_required
def logout():
    logout_user()
    # flash('Logged out.', 'info')
    return redirect(url_for('main.login'))


# @main.route('/dashboard')
# @login_required
# def dashboard():
#     # Shared statistics
#     total_students = Student.query.count()
#     total_supervisors = Faculty.query.filter(Faculty.roles.any(name='Supervisor')).count()
#     unassigned_students = Student.query.filter(~Student.supervisors.any()).count()

#     completed_students = 0
#     for student in Student.query.all():
#         milestones = student.student_milestones
#         if milestones and all(sm.completed for sm in milestones):
#             completed_students += 1

#     average_completion = round((completed_students / total_students) * 100, 2) if total_students else 0

#     year_data = db.session.query(Student.year_of_intake, func.count()).group_by(Student.year_of_intake).all()
#     year_of_intakes = [item[0] for item in year_data]
#     intake_counts = [item[1] for item in year_data]

#     stats = {
#         'total_students': total_students,
#         'total_supervisors': total_supervisors,
#         'unassigned_students': unassigned_students,
#         'completed_students': completed_students,
#         'average_completion': average_completion,
#         'year_of_intakes': year_of_intakes,
#         'intake_counts': intake_counts,
#     }

#     # Dashboard Routing Logic
#     role = current_user.role

#     if role == 'admin':
#         return render_template('dashboards/admin.html', user=current_user, stats=stats)

#     elif role == 'student':
#         return render_template('dashboards/student.html', user=current_user, student=current_user.student_profile, stats=stats)

#     elif role == 'faculty':
#         faculty = Faculty.query.filter_by(email=current_user.email).first()
#         if faculty:
#             field = (faculty.professional_field or '').lower()
#             if field == 'coordinator':
#                 return render_template('dashboards/coordinator.html', user=current_user, stats=stats)
#             elif field == 'ip':
#                 return render_template('dashboards/ip.html', user=current_user, stats=stats)
#             else:
#                 return render_template('dashboards/supervisor.html', user=current_user, stats=stats)
#         else:
#             flash("Faculty profile not found. Contact administrator.", "danger")
#             return redirect(url_for('main.logout'))

#     flash("Unknown role. Contact administrator.", "danger")
#     return redirect(url_for('main.logout'))


@main.route('/dashboard')
@login_required
def dashboard():
    from collections import defaultdict

    total_students = Student.query.count()
    total_supervisors = Faculty.query.filter(Faculty.roles.any(name='Supervisor')).count()
    unassigned_students = Student.query.filter(~Student.supervisors.any()).count()

    completed_students = 0
    for student in Student.query.all():
        milestones = student.student_milestones
        if milestones and all(getattr(sm, 'completed', False) for sm in milestones):
            completed_students += 1

    average_completion = round((completed_students / total_students) * 100, 2) if total_students else 0

    # Year of intake stats
    year_data = db.session.query(Student.year_of_intake, func.count()).group_by(Student.year_of_intake).all()
    year_of_intakes = [item[0] for item in year_data if item[0]]
    intake_counts = [item[1] for item in year_data if item[0]]

    # Supervisor load
    supervisor_data = (
        db.session.query(Faculty.full_name, func.count(Student.id))
        .join(Faculty.students)
        .group_by(Faculty.id)
        .all()
    )
    supervisor_names = [s[0] for s in supervisor_data]
    supervisor_loads = [s[1] for s in supervisor_data]

    # Milestone progress by program
    program_groups = defaultdict(list)
    for student in Student.query.all():
        if student.program:
            program_groups[student.program].append(student)

    program_milestones = []
    for program, students in program_groups.items():
        milestone_summary = defaultdict(lambda: {'completed': 0, 'in_progress': 0, 'not_started': 0})
        for student in students:
            for sm in student.student_milestones:
                status = 'not_started'
                if getattr(sm, 'completed', False):
                    status = 'completed'
                elif getattr(sm, 'in_progress', False):
                    status = 'in_progress'
                milestone_summary[sm.milestone.name][status] += 1
        program_milestones.append({
            'name': program,
            'milestones': [
                {
                    'name': milestone,
                    'completed': data['completed'],
                    'in_progress': data['in_progress'],
                    'not_started': data['not_started']
                }
                for milestone, data in milestone_summary.items()
            ]
        })

    # Intake-level completion stats
    intake_stats = (
        db.session.query(
            Student.year_of_intake,
            func.count(Student.id).label('total'),
            func.count().filter(StudentMilestone.completed == True).label('completed')
        )
        .outerjoin(Student.student_milestones)
        .group_by(Student.year_of_intake)
        .all()
    )

    intake_years, total_counts, completed_counts, in_progress_counts, completion_rates = [], [], [], [], []
    for year, total, completed in intake_stats:
        year = year or "Unknown"
        completed = completed or 0
        in_progress = total - completed
        completion_rate = round((completed / total) * 100, 2) if total else 0

        intake_years.append(year)
        total_counts.append(total)
        completed_counts.append(completed)
        in_progress_counts.append(in_progress)
        completion_rates.append(completion_rate)

    stats = {
        'total_students': total_students,
        'total_supervisors': total_supervisors,
        'unassigned_students': unassigned_students,
        'completed_students': completed_students,
        'average_completion': average_completion,
        'year_of_intakes': year_of_intakes,
        'intake_counts': intake_counts,
        'supervisor_names': supervisor_names,
        'supervisor_loads': supervisor_loads,
        'program_milestones': program_milestones,
        'intake_years': intake_years,
        'total_counts': total_counts,
        'completed_counts': completed_counts,
        'in_progress_counts': in_progress_counts,
        'completion_rates': completion_rates
    }

    # Role-based dashboard rendering
    role = current_user.role
    if role == 'admin':
        return render_template('dashboards/admin.html', user=current_user, stats=stats)
    elif role == 'student':
        return render_template('dashboards/student.html', user=current_user, student=current_user.student_profile, stats=stats)
    elif role == 'faculty':
        faculty = Faculty.query.filter_by(email=current_user.email).first()
        if faculty:
            field = (faculty.professional_field or '').lower()
            if field == 'coordinator':
                return render_template('dashboards/coordinator.html', user=current_user, stats=stats)
            elif field == 'ip':
                return render_template('dashboards/ip.html', user=current_user, stats=stats)
            else:
                return render_template('dashboards/supervisor.html', user=current_user, stats=stats)
        else:
            flash("Faculty profile not found. Contact administrator.", "danger")
            return redirect(url_for('main.logout'))

    flash("Unknown role. Contact administrator.", "danger")
    return redirect(url_for('main.logout'))


from app.auth_utils import admin_required

# ----------------------------------
# View Supervisors
# ----------------------------------
@main.route('/supervisors')
def supervisors():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)

    # Base query: only Faculty members with 'Supervisor' role
    query = Faculty.query.filter(Faculty.roles.any(name='Supervisor'))

    # Add search filter
    if search_query:
        query = query.filter(
            (Faculty.full_name.ilike(f'%{search_query}%')) |
            (Faculty.email.ilike(f'%{search_query}%'))
        )

    # Paginate results
    supervisors = query.order_by(Faculty.full_name).paginate(page=page, per_page=10)

    return render_template('supervisors.html', supervisors=supervisors)

# ----------------------------------
# edit Supervisors
# ----------------------------------
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

# ----------------------------------
# delete Supervisors
# ----------------------------------
@main.route('/supervisors/delete/<int:supervisor_id>')
@login_required
def delete_supervisor(supervisor_id):
    supervisor = supervisors.query.get_or_404(supervisor_id)
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


@main.route('/my-progress')
@login_required
def my_progress():
    if current_user.role != 'student':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.dashboard'))

    student = current_user.student_profile
    if not student:
        flash("Student profile not found.", "danger")
        return redirect(url_for('main.dashboard'))

    milestones = Milestone.query.all()

    milestone_subtasks = {}
    for milestone in milestones:
        milestone_subtasks[milestone.id] = []
        for subtask in milestone.subtasks:
            student_subtask = StudentSubtask.query.filter_by(
                student_id=student.id,
                subtask_id=subtask.id
            ).first()
            milestone_subtasks[milestone.id].append({
                'subtask': subtask,
                'status': student_subtask.status if student_subtask else 'pending'
            })

    return render_template('student_progress.html', student=student, milestones=milestones, milestone_subtasks=milestone_subtasks)


@main.route('/update-subtasks', methods=['GET', 'POST'])
@login_required
def update_subtasks():
    student = Student.query.filter_by(email=current_user.email).first_or_404()
    milestones = Milestone.query.order_by(Milestone.id).all()

    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith("subtask_"):
                subtask_id = int(key.split("_")[1])
                entry = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=subtask_id).first()
                if entry:
                    entry.status = value
                    db.session.add(entry)
        db.session.commit()
        flash("Progress updated successfully.")
        return redirect(url_for('main.update_subtasks'))

    # Prepare subtasks grouped by milestone
    progress_data = []
    for milestone in milestones:
        subtasks = Subtask.query.filter_by(milestone_id=milestone.id).order_by(Subtask.sequence_order).all()
        subtask_entries = []
        for subtask in subtasks:
            student_subtask = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=subtask.id).first()
            subtask_entries.append({
                'subtask': subtask,
                'status': student_subtask.status if student_subtask else 'pending'
            })
        progress_data.append({
            'milestone': milestone,
            'subtasks': subtask_entries
        })

    return render_template('student/update_subtasks.html', progress_data=progress_data)

@main.route('/supervisor/students')
@login_required
def supervisor_students():
    faculty = Faculty.query.filter_by(email=current_user.email).first_or_404()
    students = faculty.students
    return render_template('supervisor/supervisor_students.html', students=students)



@main.route('/supervisor/student/<int:student_id>/progress', methods=['GET', 'POST'])
@login_required
def supervisor_student_progress(student_id):
    # 👇 Adjusted role check here
    if current_user.role not in ['supervisor', 'faculty']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.dashboard'))

    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        print("🔁 Received POST request")
        print("📥 Form data:", dict(request.form))

        updated = False
        for key, value in request.form.items():
            if key.startswith("subtask_"):
                try:
                    subtask_id = int(key.split("_")[1])
                    new_status = value.strip().lower()

                    entry = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=subtask_id).first()
                    if entry:
                        if new_status != entry.status:
                            entry.status = new_status
                            updated = True
                    else:
                        new_entry = StudentSubtask(
                            student_id=student.id,
                            subtask_id=subtask_id,
                            status=new_status
                        )
                        db.session.add(new_entry)
                        updated = True
                except (ValueError, IndexError):
                    continue

        if updated:
            db.session.commit()
            flash("✅ Subtask progress updated successfully.", "success")
        else:
            flash("⚠️ No changes were made to the subtask progress.", "info")

        return redirect(request.url)


    # Load milestones and progress
    milestones = Milestone.query.order_by(Milestone.id).all()
    progress_data = []
    for milestone in milestones:
        subtasks = Subtask.query.filter_by(milestone_id=milestone.id).order_by(Subtask.sequence_order).all()
        entries = []
        for subtask in subtasks:
            student_subtask = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=subtask.id).first()
            entries.append({
                'subtask': subtask,
                'status': student_subtask.status if student_subtask else 'pending',
                'comment': student_subtask.comment if student_subtask else None
            })
        progress_data.append({'milestone': milestone, 'subtasks': entries})

    return render_template(
        'supervisor/supervisor_progress.html',
        student=student,
        progress_data=progress_data
    )


@main.route('/supervisor/dashboard')
@login_required
def supervisor_dashboard():
    faculty = Faculty.query.filter_by(email=current_user.email).first_or_404()
    return render_template('supervisor/dashboard.html', user=faculty)

@main.route('/student/milestone/<int:milestone_id>')
@login_required
def student_milestone_detail(milestone_id):
    milestone = StudentMilestone.query.filter_by(id=milestone_id, student_id=current_user.student.id).first_or_404()
    return render_template('students/student_milestone_detail.html', milestone=milestone)

@main.route('/student/subtask/<int:subtask_id>/update', methods=['POST'])
@login_required
def update_subtask_status(subtask_id):
    valid_statuses = ['pending', 'in_progress', 'completed']
    status = request.form.get('status')

    if status not in valid_statuses:
        flash("Invalid status update.", "danger")
        return redirect(request.referrer)

    subtask = Subtask.query.get_or_404(subtask_id)
    subtask.status = status
    db.session.commit()

    flash("Subtask updated to '{}'.".format(status.replace('_', ' ').title()), "success")
    return redirect(request.referrer)



@main.route('/student/milestone/<int:milestone_id>/upload', methods=['POST'])
@login_required
def upload_submission(milestone_id):
    file = request.files['submission_file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Save submission info in DB if needed
        flash("Submission uploaded successfully.", "success")
    return redirect(request.referrer)


@main.route('/student/dashboard')
@login_required
def student_dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student:
        flash("Student profile not found.", "warning")
        return render_template('dashboards/student.html', user=current_user, student=None, milestones=[])

    # Query assigned milestones
    milestones = (
        StudentMilestone.query
        .filter_by(student_id=student.id)
        .options(
            db.joinedload(StudentMilestone.milestone).joinedload(Milestone.subtasks))
        .all()
    )

    print(f"[DEBUG] Current User: {current_user.full_name} ({current_user.id})")
    print(f"[DEBUG] Student Profile ID: {student.id}")
    print(f"[DEBUG] Retrieved {len(milestones)} milestones")

    return render_template(
        'dashboards/student.html',
        user=current_user,
        student=student,
        milestones=milestones
    )

