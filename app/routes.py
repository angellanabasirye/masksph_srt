from sqlalchemy import func
# from app import db
from flask import request
from flask import render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import RegisterUserForm, RegisterStudentForm
from werkzeug.security import generate_password_hash
from app.forms import RegisterUserForm, RegisterStudentForm, RegisterSupervisorForm, AssignSupervisorsForm
from app.models import db, Student, StudentMilestone, Milestone, User, Subtask, StudentSubtask
import os
from werkzeug.utils import secure_filename
from app.data_utils import allowed_file, process_student_excel
from flask import render_template, send_from_directory, current_app
from app.forms import FacultyForm
from app.models import Faculty, Role, SubtaskComment, StudentSubtask, SubtaskStatus
from collections import defaultdict
from datetime import datetime
from sqlalchemy import func, extract
from flask import render_template, flash, redirect, url_for ,jsonify
from flask_login import login_required, current_user
from app.utils.notifications import get_student_unread_count
from app.constants import SUBTASK_STATUSES, MILESTONE_STATUSES
from app.forms import LoginForm

from flask import Blueprint

main = Blueprint('main', __name__)
student_actions = Blueprint('student_actions', __name__)

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
        return render_template('dashboards/student.html', user=current_user, stats=stats, unread_count=0)
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

    # 🔴 Remove this line
    # query = query.filter(Student.student_milestones.any())

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

            # Role-based redirection
            if user.role == 'faculty':
                faculty = Faculty.query.filter_by(email=user.email).first()
                if faculty:
                    field = (faculty.professional_field or '').lower()
                    if field == 'coordinator':
                        return redirect(url_for('main.dashboard'))  # Coordinator
                    else:
                        return redirect(url_for('main.supervisor_dashboard'))  # Supervisor
                else:
                    flash("Faculty profile not found.", "danger")
                    return redirect(url_for('main.logout'))

            elif user.role == 'student':
                return redirect(url_for('main.dashboard'))  # Student

            elif user.role == 'admin':
                return redirect(url_for('main.dashboard'))  # Admin

            else:
                flash("Unrecognized role.", "danger")
                return redirect(url_for('main.logout'))

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

@main.route('/dashboard')
@login_required
def dashboard():
    from collections import defaultdict
    from sqlalchemy import func
    from app.models import Student, Faculty, StudentMilestone, SubtaskComment, StudentSubtask

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

    unread_count = 0
    role = current_user.role

    if role == 'student' and hasattr(current_user, 'student_profile'):
        unread_count = SubtaskComment.query.join(
            StudentSubtask, SubtaskComment.subtask_id == StudentSubtask.subtask_id
        ).filter(
            StudentSubtask.student_id == current_user.student_profile.id,
            SubtaskComment.is_read == False,
            SubtaskComment.user_id != current_user.id
        ).count()

    elif role == 'faculty':
        faculty = Faculty.query.filter_by(email=current_user.email).first()
        if faculty:
            student_ids = [s.id for s in faculty.students]
            unread_count = SubtaskComment.query.join(
                StudentSubtask, SubtaskComment.subtask_id == StudentSubtask.subtask_id
            ).filter(
                StudentSubtask.student_id.in_(student_ids),
                SubtaskComment.is_read == False,
                SubtaskComment.user_id != current_user.id
            ).count()

    if role == 'admin':
        return render_template('dashboards/admin.html', user=current_user, stats=stats)
    elif role == 'student':
        return render_template('dashboards/student.html', user=current_user, student=current_user.student, stats=stats, unread_count=0)
    elif role == 'faculty':
        faculty = Faculty.query.filter_by(email=current_user.email).first()
        if faculty:
            field = (faculty.professional_field or '').lower()
            if field == 'coordinator':
                return render_template('dashboards/coordinator.html', user=current_user, stats=stats, unread_count=unread_count)
            elif field == 'ip':
                return render_template('dashboards/ip.html', user=current_user, stats=stats, unread_count=unread_count)
            else:
                return render_template('dashboards/supervisor.html', user=current_user, stats=stats, unread_count=0)
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

ALLOWED_BULK_EXTENSIONS = {'xlsx', 'csv'}

def allowed_bulk_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_BULK_EXTENSIONS


@main.route('/upload-bulk-students', methods=['POST'])
def upload_bulk_students():
    file = request.files.get('bulk_file')

    if file and allowed_bulk_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config['BULK_UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # Process Excel/CSV file
        result = process_student_excel(save_path)

        # Flash result messages
        if result.get('success'):
            flash(f"{result['success']} students registered successfully.", "success")
        if result.get('failed') and result.get('errors'):
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

    student = current_user.student
    if not student:
        flash("Student profile not found.", "danger")
        return redirect(url_for('main.dashboard'))

    milestones = Milestone.query.all()

    progress_data = []
    for milestone in milestones:
        subtasks = []
        for subtask in milestone.subtasks:
            student_entry = StudentSubtask.query.filter_by(
                student_id=student.id,
                subtask_id=subtask.id
            ).first()
            subtasks.append({
                "subtask": subtask,
                "status": student_entry.status if student_entry else "pending"
            })
        progress_data.append({
            "milestone": milestone,
            "subtasks": subtasks
        })

    return render_template(
        'students/student_progress.html',
        student=student,
        progress_data=progress_data
    )

@main.route('/student/subtask/<int:subtask_id>/update', methods=['POST'])
@login_required
def update_subtask_status(subtask_id):
    # Ensure the user is a student and has a student profile
    student = Student.query.filter_by(user_id=current_user.id).first_or_404()

    # Get the new status from the form
    status = request.form.get('status')

    # Validate status input
    if status not in ['pending', 'in_progress', 'ready']:
        return jsonify(success=False, error="Invalid status."), 400

    # Fetch the student-subtask entry
    subtask_status = StudentSubtask.query.filter_by(
        student_id=student.id,
        subtask_id=subtask_id
    ).first()

    if not subtask_status:
        return jsonify(success=False, error="Subtask entry not found."), 404

    # Update logic
    if status == 'ready':
        subtask_status.student_marked_ready = True
        subtask_status.status = 'ready'
    else:
        subtask_status.status = status
        subtask_status.student_marked_ready = False

    db.session.commit()

    return jsonify(success=True, status=status), 200


@main.route('/supervisor/students')
@login_required
def supervisor_students():
    faculty = Faculty.query.filter_by(email=current_user.email).first_or_404()
    students = faculty.students
    return render_template('supervisor/supervisor_students.html', students=students)

@main.route('/supervisor/student/<int:student_id>/progress', methods=['GET', 'POST'])
@login_required
def supervisor_student_progress(student_id):
    # Role check
    if current_user.role not in ['supervisor', 'faculty']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.dashboard'))

    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        subtask_id = request.form.get('subtask_id')
        new_status = request.form.get('status', '').strip().lower()

        if subtask_id and new_status == 'completed':
            try:
                subtask_id = int(subtask_id)
                entry = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=subtask_id).first()

                if entry:
                    if entry.status == 'ready':
                        entry.status = 'completed'
                        db.session.commit()
                        flash("✅ Subtask marked as completed.", "success")
                    else:
                        flash("⚠️ Subtask is not ready for completion.", "warning")
                else:
                    flash("⚠️ No such subtask entry found.", "danger")

            except ValueError:
                flash("⚠️ Invalid subtask ID.", "danger")

        return redirect(request.url)

    # Load milestones and progress
    milestones = Milestone.query.order_by(Milestone.id).all()
    progress_data = []

    for milestone in milestones:
        subtasks = Subtask.query.filter_by(milestone_id=milestone.id).order_by(Subtask.sequence_order).all()
        entries = []

        for subtask in subtasks:
            student_subtask = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=subtask.id).first()

            comments = []
            latest_comment = None

            if student_subtask:
                # Fetch all comments for this student's subtask
                comments = SubtaskComment.query.filter_by(subtask_id=subtask.id).order_by(SubtaskComment.timestamp).all()

                # Mark unread comments as read (for supervisor viewing)
                updated = False
                for comment in comments:
                    if not comment.is_read and comment.user_id != current_user.id:
                        comment.is_read = True
                        updated = True
                if updated:
                    db.session.commit()

                # Get the latest comment
                if comments:
                    latest_comment = comments[-1]

            entries.append({
                'subtask': subtask,
                'status': student_subtask.status if student_subtask else 'pending',
                'comments': comments,
                'latest_comment': latest_comment
            })

        progress_data.append({
            'milestone': milestone,
            'subtasks': entries
        })

    return render_template(
        'supervisor/supervisor_progress.html',
        student=student,
        progress_data=progress_data
    )

@main.route('/supervisor/dashboard')
@login_required
def supervisor_dashboard():
    faculty = Faculty.query.filter_by(email=current_user.email).first_or_404()
    students = faculty.students
    unread_count = SubtaskComment.query.filter_by(user_id=current_user.id, is_read=False).count()

    # Count how many subtasks are marked "ready" for supervisor to review
    student_ids = [s.id for s in students]
    ready_subtask_count = (
        StudentSubtask.query
        .filter(StudentSubtask.student_id.in_(student_ids))
        .filter_by(status='ready')
        .count()
    )

    progress_data = []
    intake_counts = {}

    total_subtasks = Subtask.query.count()

    for student in students:
        subtasks = StudentSubtask.query.filter_by(student_id=student.id).all()

        completed = sum(1 for s in subtasks if s.status == 'completed')
        in_progress = sum(1 for s in subtasks if s.status == 'in_progress')
        ready = sum(1 for s in subtasks if s.status == 'ready')
        not_started = total_subtasks - (completed + in_progress + ready)

        percent = round((completed / total_subtasks) * 100, 1) if total_subtasks > 0 else 0

        progress_data.append({
            "name": student.full_name,
            "completed": completed,
            "in_progress": in_progress,
            "ready": ready,
            "not_started": not_started,
            "percent": percent,
            "topic": student.research_topic or "N/A",
            "intake": student.year_of_intake or "Unknown"
        })

        if student.year_of_intake:
            intake_counts[student.year_of_intake] = intake_counts.get(student.year_of_intake, 0) + 1

        # Find the first student with a ready subtask
        first_ready_student_id = None
        for student in students:
            ready_exists = StudentSubtask.query.filter_by(student_id=student.id, status='ready').first()
            if ready_exists:
                first_ready_student_id = student.id
                break

    return render_template(
        'supervisor/dashboard.html',
        user=faculty,
        progress_data=progress_data,
        intake_counts=intake_counts,
        unread_count=unread_count,
        ready_subtask_count=ready_subtask_count,
        first_ready_student_id=first_ready_student_id
    )


@main.route('/student/milestone/<int:milestone_id>')
@login_required
def student_milestone_detail(milestone_id):
    milestone = StudentMilestone.query.filter_by(id=milestone_id, student_id=current_user.student.id).first_or_404()
    return render_template('students/student_milestone_detail.html', milestone=milestone)


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
    unread_count = get_student_unread_count(current_user.id)

    if not student:
        flash("Student profile not found.", "warning")
        return render_template('dashboards/student.html', user=current_user, unread_count=0, student=None, milestones=[])

    # Query assigned milestones with subtasks
    milestones = (
        StudentMilestone.query
        .filter_by(student_id=student.id)
        .options(db.joinedload(StudentMilestone.milestone).joinedload(Milestone.subtasks))
        .all()
    )

    progress_data = []

    for student_milestone in milestones:
        milestone = student_milestone.milestone
        subtasks = milestone.subtasks
        entries = []

        for subtask in subtasks:
            status_row = SubtaskStatus.query.filter_by(
                student_id=student.id,
                subtask_id=subtask.id
            ).first()
            entries.append({
                'subtask': subtask,
                'status': status_row.status if status_row else 'not_started',
                'student_marked_ready': status_row.student_marked_ready if status_row else False
            })

        progress_data.append({'milestone': milestone, 'subtasks': entries})

    print(f"[DEBUG] Current User: {current_user.full_name} ({current_user.id})")
    print(f"[DEBUG] Student Profile ID: {student.id}")
    print(f"[DEBUG] Retrieved {len(progress_data)} milestone blocks")

    return render_template(
        'dashboards/student.html',
        user=current_user,
        student=student,
        progress_data=progress_data,
        unread_count=0
    )

@main.route('/supervisor/milestone-review')
@login_required
def supervisor_milestone_review():
    faculty = Faculty.query.filter_by(email=current_user.email).first_or_404()

    student_data = []
    for student in faculty.students:
        milestones_data = []
        total_subtasks = 0
        completed_subtasks = 0

        all_milestones = Milestone.query.order_by(Milestone.id).all()

        for milestone in all_milestones:
            subtasks = Subtask.query.filter_by(milestone_id=milestone.id).order_by(Subtask.sequence_order).all()
            subtask_info = []

            milestone_total = 0
            milestone_completed = 0

            for subtask in subtasks:
                progress = StudentSubtask.query.filter_by(student_id=student.id, subtask_id=subtask.id).first()
                status = progress.status if progress else 'pending'

                milestone_total += 1
                total_subtasks += 1

                if status == 'completed':
                    milestone_completed += 1
                    completed_subtasks += 1

                subtask_info.append({
                    'name': subtask.name,
                    'status': status.capitalize()
                })

            if milestone_total > 0:
                percent = round((milestone_completed / milestone_total) * 100, 1)
            else:
                percent = 0.0

            if milestone_completed == milestone_total and milestone_total > 0:
                milestone_status = "Completed"
            elif milestone_completed > 0:
                milestone_status = "In Progress"
            else:
                milestone_status = "Not Started"

            milestones_data.append({
                'name': milestone.name,
                'subtasks': subtask_info,
                'status': milestone_status,
                'percent': percent
            })

        overall_percent = round((completed_subtasks / total_subtasks) * 100, 1) if total_subtasks > 0 else 0

        student_data.append({
            'student': student,
            'milestones': milestones_data,
            'completion': overall_percent
        })

    return render_template('supervisor/milestone_review.html', students=student_data)


ALLOWED_SUBMISSION_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_submission_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_SUBMISSION_EXTENSIONS

@main.route('/student/milestone/<int:milestone_id>/upload', methods=['POST'])
@login_required
def student_upload_submission(milestone_id):
    student = Student.query.filter_by(email=current_user.email).first_or_404()
    file = request.files.get('submission_file')

    if not file or file.filename == '':
        flash("No file selected.", "danger")
        return redirect(request.referrer)

    if file and allowed_submission_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # Save to DB
        upload = MilestoneUpload(
            milestone_id=milestone_id,
            student_id=student.id,
            filename=filename
        )
        db.session.add(upload)
        db.session.commit()

        flash("File uploaded successfully.", "success")
        return redirect(request.referrer)
    else:
        flash("Invalid file type. Only PDF, DOC, and DOCX are allowed.", "warning")
        return redirect(request.referrer)
               
@main.route('/supervisor/feedback')
@login_required
def supervisor_feedback_panel():
    faculty = Faculty.query.filter_by(email=current_user.email).first_or_404()

    show_unread_only = request.args.get('unread') == '1'
    student_id = request.args.get('student_id', type=int)

    feedback_data = []

    students = faculty.students
    if student_id:
        students = [s for s in students if s.id == student_id]

    for student in students:
        student_entries = []
        student_subtasks = StudentSubtask.query.filter_by(student_id=student.id).all()

        for entry in student_subtasks:
            comments_query = SubtaskComment.query.filter_by(subtask_id=entry.subtask_id)
            if show_unread_only:
                comments_query = comments_query.filter(SubtaskComment.is_read == False)

            comments = comments_query.order_by(SubtaskComment.timestamp.desc()).all()

            if comments:
                student_entries.append({
                    'subtask_id': entry.subtask_id,
                    'subtask': entry.subtask,
                    'comments': comments
                })

        if student_entries:
            feedback_data.append({
                'student': student,
                'entries': student_entries
            })

    return render_template(
        'supervisor/supervisor_feedback_panel.html',
        feedback_data=feedback_data,
        unread=show_unread_only,
        selected_student=student_id,
        all_students=faculty.students
    )

@main.route('/supervisor/mark-all-feedback-read', methods=['POST'])
@login_required
def mark_all_feedback_read():
    faculty = Faculty.query.filter_by(user_id=current_user.id).first_or_404()
    for student in faculty.students:
        student_subtasks = StudentSubtask.query.filter_by(student_id=student.id).all()
        for subtask in student_subtasks:
            unread_comments = SubtaskComment.query.filter_by(
                subtask_id=subtask.subtask_id,
                is_read=False
            ).filter(SubtaskComment.user_id != current_user.id).all()

            for comment in unread_comments:
                comment.is_read = True
    db.session.commit()
    flash("✅ All unread comments marked as read.", "success")
    return redirect(url_for('main.supervisor_feedback_panel'))

@main.route('/supervisor/student/<int:student_id>/add-comment', methods=['POST'])
@login_required
def add_subtask_comment(student_id):
    print("current_user.id =", current_user.id)
    print("current_user.role =", current_user.role)

    subtask_id = request.form.get('subtask_id')
    content = request.form.get('content', '').strip()

    if not content:
        flash("Comment cannot be empty.", "warning")
        return redirect(url_for('main.supervisor_student_progress', student_id=student_id))

    comment = SubtaskComment(
        subtask_id=subtask_id,
        user_id=current_user.id,
        content=content,
    )
    db.session.add(comment)
    db.session.commit()

    flash("✅ Comment added.", "success")
    return redirect(url_for('main.supervisor_student_progress', student_id=student_id))

@main.route('/ajax/add-comment', methods=['POST'])
@login_required
def add_subtask_comment_ajax():
    data = request.get_json()
    subtask_id = data.get('subtask_id')
    content = data.get('content', '').strip()

    if not subtask_id or not content:
        return jsonify(success=False, message="Missing subtask ID or empty comment.")

    subtask = Subtask.query.get(subtask_id)
    if not subtask:
        return jsonify(success=False, message="Subtask not found.")

    comment = SubtaskComment(
        subtask_id=subtask.id,
        user_id=current_user.id,
        content=content,
        is_read=False
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify(success=True, message="Comment added successfully.")

