from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import admin_bp
# from app import db
from app.models import User
from flask import Blueprint

# admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied.')
        return redirect(url_for('main.index'))  # or home route
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied.')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('admin.manage_users'))
