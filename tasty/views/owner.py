from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from tasty.utils.decorators import login_required, role_required
import tasty.services.user_service as service
import tasty.services.analytics_service as analytics_service  # <-- Importado

bp_owner = Blueprint("owner", __name__, url_prefix="/owner")

@bp_owner.route("/dashboard")
@login_required
@role_required("owner")
def dashboard():
    """Renderiza o resumo operacional alimentado por estatísticas agregadas em tempo real."""
    owner_id = session["user_id"]
    
    # Substitui os valores fixos do mockup por dados calculados diretamente do banco de dados
    metrics = analytics_service.get_owner_portfolio_metrics(owner_id)
    
    return render_template("owner/dashboard.html", stats=metrics)


# --- ROTAS DE TELEMETRIA PARA DESENVOLVEDORES (API JSON) ---

@bp_owner.route("/api/analytics/summary", methods=["GET"])
@login_required
@role_required("owner")
def api_owner_summary():
    """Endpoint restrito para o proprietário exportar os dados consolidados da sua conta em JSON."""
    metrics = analytics_service.get_owner_portfolio_metrics(session["user_id"])
    return jsonify(metrics), 200


@bp_owner.route("/api/analytics/restaurant/<int:business_id>", methods=["GET"])
@login_required
def api_restaurant_metrics(business_id):
    """Endpoint para desenvolvedores e proprietários auditarem a performance de uma filial isolada."""
    import tasty.services.business_service as b_service
    business = b_service.get_business(business_id)
    
    if not business:
        return jsonify({"error": "Estabelecimento não encontrado."}), 404
        
    # Bloqueio de Segurança: Se não for admin, confere se o requisitante é de fato um dos donos
    if session.get("user_role") != "admin" and not any(o.id == session.get("user_id") for o in business.owners):
        return jsonify({"error": "Acesso negado às métricas do estabelecimento."}), 403
        
    metrics = analytics_service.get_restaurant_metrics(business_id)
    return jsonify(metrics), 200


# (Mantenha o restante das rotas list_owners, edit_owner e delete_owner intocadas abaixo)
@bp_owner.route("/list", methods=["GET"])
@login_required
@role_required("admin")
def list_owners():
    owners = service.get_all_business_owners()
    return render_template("owner/index.html", users=owners)

@bp_owner.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_owner(id):
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
            return redirect(url_for("owner.dashboard"))
        flash(msg, "danger")
    return render_template("owner/form.html", user=owner_user)

@bp_owner.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_owner(id):
    success, msg, code = service.delete_business_owner(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("owner.list_owners"))