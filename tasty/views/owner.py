from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from tasty.utils.decorators import login_required, role_required
import tasty.services.user_service as service

bp_owner = Blueprint("owner", __name__, url_prefix="/owner")

@bp_owner.route("/dashboard")
@login_required
@role_required("owner")
def dashboard():
    return render_template("owner/dashboard.html")

@bp_owner.route("/list", methods=["GET"])
@login_required
@role_required("admin")
def list_owners():
    owners = service.get_all_business_owners()
    return render_template("owner/index.html", users=owners)

@bp_owner.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_owner(id):
    # Proteção: Apenas o próprio dono ou um admin podem editar
    if session.get("user_role") != "admin" and session.get("user_id") != id:
        flash("Acesso negado.", "danger")
        return redirect(url_for("owner.dashboard"))

    owner_user = service.get_business_owner(id)
    if not owner_user:
        flash("Dono de negócio não encontrado.", "warning")
        return redirect(url_for("owner.dashboard"))

    if request.method == "POST":
        data = dict(request.form)
        success, msg, code = service.update_business_owner(id, data)
        
        if success:
            flash("Perfil atualizado com sucesso.", "success")
            return redirect(request.referrer or url_for("owner.dashboard"))
        flash(msg, "danger")

    return render_template("owner/form.html", user=owner_user)

@bp_owner.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_owner(id):
    success, msg, code = service.delete_business_owner(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("owner.list_owners"))