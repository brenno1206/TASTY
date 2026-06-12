from functools import wraps
from flask import session, flash, redirect, url_for, request

def login_required(f):
    """Garante que o usuário está logado antes de acessar a rota."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """Garante que o usuário logado tem o papel (role) correto."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("user_role") != role_name:
                flash("Você não tem permissão para acessar esta área.", "danger")
                user_role = session.get("user_role")
                if user_role:
                    return redirect(url_for(f"{user_role}.dashboard"))
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator