# app/auth_utils.py

from functools import wraps
from flask import session, redirect, url_for, flash
from .models import User  # use relative import if models are in the same package

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            flash("Access denied. Administrator only.", "danger")
            return redirect(url_for('main.dashboard'))  # or your default route
        return f(*args, **kwargs)
    return decorated_function
