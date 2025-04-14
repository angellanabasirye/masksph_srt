from .models import db, Student, Supervisor, StudentMilestone, Milestone, User
from sqlalchemy import func
from app import db
from flask import request
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from .admin import admin



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
def register():
    error = None
    if request.method == 'POST':
        full_name = request.form['full_name']
        gender = request.form['gender']
        email = request.form['email']
        phone = request.form.get('phone')
        reg_number = request.form['registration_number']
        student_number = request.form['student_number']
        program = request.form['program']
        year_of_intake = request.form['year_of_intake']
        research_topic = request.form['research_topic']

        # Check uniqueness
        existing = Student.query.filter(
            (Student.registration_number == reg_number) |
            (Student.student_number == student_number)
        ).first()

        if existing:
            error = 'A student with this registration or student number already exists.'
        else:
            new_student = Student(
                full_name=full_name,
                gender=gender,
                email=email,
                phone=phone,
                registration_number=reg_number,
                student_number=student_number,
                program=program,
                year_of_intake=year_of_intake,
                research_topic=research_topic
            )

            db.session.add(new_student)
            db.session.commit()

            flash('Student registered successfully.')
            return redirect(url_for('main.students'))

    return render_template('register.html', error=error)

# ----------------------------------
# Register Supervisor
# ----------------------------------
@main.route('/register-supervisor', methods=['GET', 'POST'])
def register_supervisor():
    if request.method == 'POST':
        name = request.form['full_name']
        email = request.form['email']
        department = request.form['department']

        supervisor = Supervisor(full_name=name, email=email, department=department)
        db.session.add(supervisor)
        db.session.commit()

        flash('Supervisor registered successfully!')
        return redirect(url_for('main.index'))

    return render_template('register_supervisor.html')

# ----------------------------------
# View student-supervisor
# ----------------------------------
@main.route('/supervisor/<int:supervisor_id>/students')
def supervisor_students(supervisor_id):
    supervisor = Supervisor.query.get_or_404(supervisor_id)
    return render_template('supervisor_students.html', supervisor=supervisor, students=supervisor.students)

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
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    supervisors = Supervisor.query.order_by(Supervisor.full_name).all()

    if request.method == 'POST':
        student.full_name = request.form['full_name']
        student.email = request.form['email']
        student.program = request.form['program']
        student.phone = request.form.get('phone')
        student.reg_number = request.form['registration_number']
        student.student_number = request.form['student_number']
        student.supervisor_id = request.form.get('supervisor_id') or None
        db.session.commit()
        flash('Student updated successfully.')
        return redirect(url_for('main.students'))

    return render_template('edit_student.html', student=student, supervisors=supervisors)

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

@main.route('/assign-supervisors/<int:student_id>', methods=['GET', 'POST'])
def assign_supervisors_page(student_id):
    student = Student.query.get_or_404(student_id)
    all_supervisors = Supervisor.query.all()

    if request.method == 'POST':
        selected_ids = request.form.getlist('supervisors')
        selected_supervisors = Supervisor.query.filter(Supervisor.id.in_(selected_ids)).all()
        student.supervisors = selected_supervisors
        db.session.commit()
        flash('Supervisors assigned successfully.')
        return redirect(url_for('main.students'))

    return render_template('assign_supervisors.html', student=student, supervisors=all_supervisors)

@main.route('/create-admin')
def create_admin():
    from app import db
    admin = User(full_name="System Admin", email="admin@example.com", role="admin")
    admin.set_password("adminpass")
    db.session.add(admin)
    db.session.commit()
    return "Admin created!"

@main.route('/register_users', methods=['GET', 'POST'])
def register_users():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('main.register_users.html'))

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register_users.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('main.index'))
        flash('Invalid credentials.', 'danger')
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
    return render_template('dashboard.html', user=current_user)

# @admin.route('/manage-users')
# @login_required
# def manage_users():
#     if current_user.role != 'admin':
#         return "Unauthorized", 403

#     users = User.query.all()
#     return render_template('admin/manage_users.html', user=current_user, users=users)