# app/admin.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, Log, ActivityLog
from app.extensions import db
import csv
import io

# Renamed to match what __init__.py expects
admin_bp = Blueprint('admin', __name__, template_folder='templates')


@admin_bp.route('/manage-users', methods=['GET'])
@login_required
def manage_users():
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    page = request.args.get('page', 1, type=int)

    query = User.query

    if search:
        query = query.filter(
            (User.full_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )

    if role:
        query = query.filter_by(role=role)

    users = query.order_by(User.full_name).paginate(page=page, per_page=10)

    try:
        logs = Log.query.order_by(Log.timestamp.desc()).limit(10).all()
    except Exception:
        logs = []

    return render_template('admin/manage_users.html', users=users, logs=logs)


@admin_bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        user.role = request.form['role']

        log = ActivityLog(
            user_id=current_user.id,
            action=f"Edited user: {user.email}"
        )
        db.session.add(log)
        db.session.commit()

        # flash('User updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/edit_user.html', user=current_user, user_to_edit=user)


@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    log = ActivityLog(user_id=current_user.id, action=f"Deleted user: {user.email}")
    db.session.add(log)

    db.session.delete(user)
    db.session.commit()
    # flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        # flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            # flash('A user with that email already exists.', 'warning')
            return redirect(url_for('admin.add_user'))

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)

        log = ActivityLog(user_id=current_user.id, action=f"Added user: {user.email}")
        db.session.add(log)
        db.session.add(user)
        db.session.commit()

        # flash('New user added successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/add_user.html', user=current_user)


@admin_bp.route('/download-logs')
@login_required
def download_logs():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['User', 'Action', 'Timestamp'])

    for log in logs:
        cw.writerow([log.user.full_name, log.action, log.timestamp.strftime('%Y-%m-%d %H:%M:%S')])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=activity_logs.csv"
    output.headers["Content-type"] = "text/csv"
    return output
