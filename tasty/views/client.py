from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from tasty.utils.decorators import login_required, role_required
import tasty.services.user_service as service
import tasty.services.business_type_service as bt_service # <-- Adicionado

bp_client = Blueprint("client", __name__, url_prefix="/client")

@bp_client.route("/dashboard")
@login_required
@role_required("client")
def dashboard():
    return render_template("client/dashboard.html")

@bp_client.route("/onboarding", methods=["GET"])
@login_required
@role_required("client")
def onboarding():
    """Renderiza a interface injetando as categorias reais do banco de dados."""
    # Busca os tipos para o usuário escolher
    tipos_disponiveis = bt_service.get_all_business_types()
    return render_template("client/onboarding.html", business_types=tipos_disponiveis)

@bp_client.route("/onboarding", methods=["POST"])
@login_required
@role_required("client")
def save_onboarding():
    user_id = session.get("user_id")
    data = request.get_json()

    if not data:
        return jsonify({"error": "Nenhum dado fornecido."}), 400

    update_data = {}
    if data.get("preferences"):
        update_data["preferences"] = data.get("preferences")
    if data.get("address"):
        update_data["addresses"] = [data.get("address")]

    success, msg, code = service.update_client(user_id, update_data)

    if success:
        return jsonify({"message": "Onboarding concluído com sucesso."}), 200
        
    return jsonify({"error": msg}), code


@bp_client.route("/list", methods=["GET"])
@login_required
@role_required("admin") 
def list_clients():
    clients = service.get_all_clients()
    return render_template("client/index.html", users=clients)

@bp_client.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(id):
    # Proteção: Apenas o próprio cliente ou um admin podem editar este perfil
    if session.get("user_role") != "admin" and session.get("user_id") != id:
        flash("Acesso negado.", "danger")
        return redirect(url_for("client.dashboard"))

    client_user = service.get_client(id)
    if not client_user:
        flash("Cliente não encontrado.", "warning")
        return redirect(url_for("client.dashboard"))

    if request.method == "POST":
        data = dict(request.form)
        success, msg, code = service.update_client(id, data)
        
        if success:
            flash("Perfil atualizado com sucesso.", "success")
            return redirect(request.referrer or url_for("client.dashboard"))
        flash(msg, "danger")

    return render_template("client/form.html", user=client_user)

@bp_client.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_client(id):
    success, msg, code = service.delete_client(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("client.list_clients"))