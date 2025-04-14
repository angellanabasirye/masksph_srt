# app/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from . import db
from .models import User, ActivityLog
import csv
import io
from flask import make_response

admin = Blueprint('admin', __name__, template_folder='templates')

from .models import User, db

@admin.route('/manage-users')
@login_required
def manage_users():
    users = User.query.all()
    user_filter = request.args.get('user_filter')

    if user_filter:
        logs = ActivityLog.query.filter_by(user_id=user_filter).order_by(ActivityLog.timestamp.desc()).all()
    else:
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(50).all()

    return render_template('admin/manage_users.html', user=current_user, users=users, logs=logs)


@admin.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
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

        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/edit_user.html', user=current_user, user_to_edit=user)

@admin.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    log = ActivityLog(user_id=current_user.id, action=f"Deleted user: {user.email}")
    db.session.add(log)

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))



@admin.route('/add-user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('A user with that email already exists.', 'warning')
            return redirect(url_for('admin.add_user'))

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)

        new_user = User(...)  
        log = ActivityLog(user_id=current_user.id, action=f"Added user: {new_user.email}")
        db.session.add(log)

        db.session.add(user)
        db.session.commit()
        flash('New user added successfully!', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/add_user.html', user=current_user)


@admin.route('/download-logs')
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