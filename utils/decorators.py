from functools import wraps
from flask import session, redirect, url_for, flash, request


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return wrapped


def owner_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("owner_id"):
            flash("Please sign in to your owner account.", "warning")
            return redirect(url_for("owner.login"))
        return f(*args, **kwargs)
    return wrapped


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin sign-in required.", "warning")
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return wrapped
