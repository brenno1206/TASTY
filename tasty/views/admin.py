from flask import Blueprint, render_template, request, flash, redirect, url_for
from tasty.utils.decorators import login_required, role_required
import tasty.services.user_service as service

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")

@bp_admin.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    return render_template("admin/dashboard.html")

@bp_admin.route("/users", methods=["GET"])
@login_required
@role_required("admin")
def list_admins():
    level = request.args.get("level")
    if level:
        admins = service.get_admins_by_level(level)
    else:
        admins = service.get_all_admins()
    return render_template("admin/index.html", users=admins)

@bp_admin.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_admin():
    if request.method == "POST":
        data = dict(request.form)
        success, msg, code = service.create_admin(data)
        if success:
            flash(msg, "success")
            return redirect(url_for("admin.list_admins"))
        flash(msg, "danger")
    
    return render_template("admin/form.html", action="Criar")

@bp_admin.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_admin(id):
    admin_user = service.get_admin(id)
    if not admin_user:
        flash("Administrador não encontrado.", "warning")
        return redirect(url_for("admin.list_admins"))

    if request.method == "POST":
        data = dict(request.form)
        success, msg, code = service.update_admin(id, data)
        
        if success:
            flash(msg, "success")
            return redirect(url_for("admin.list_admins"))
        flash(msg, "danger")

    return render_template("admin/form.html", user=admin_user, action="Editar")

@bp_admin.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_admin(id):
    success, msg, code = service.delete_admin(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.list_admins"))