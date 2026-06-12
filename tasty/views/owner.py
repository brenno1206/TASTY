from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, current_app
from tasty.utils.decorators import login_required, role_required
import tasty.services.user_service as service
import tasty.services.analytics_service as analytics_service

bp_owner = Blueprint("owner", __name__, url_prefix="/owner")

@bp_owner.route("/dashboard")
@login_required
@role_required("owner")
def dashboard():
    """Renderiza o resumo operacional alimentado por estatísticas agregadas em tempo real."""
    owner_id = session["user_id"]
    
    metrics = analytics_service.get_owner_portfolio_metrics(owner_id)
    current_app.logger.info(f"Proprietário ID {owner_id} acessou o dashboard. Métricas carregadas: {metrics}")
    return render_template("owner/dashboard.html", stats=metrics)


@bp_owner.route("/api/analytics/summary", methods=["GET"])
@login_required
@role_required("owner")
def api_owner_summary():
    """Endpoint restrito para o proprietário exportar os dados consolidados da sua conta em JSON."""
    metrics = analytics_service.get_owner_portfolio_metrics(session["user_id"])
    current_app.logger.info(f"Proprietário ID {session.get('user_id')} exportou os dados consolidados do dashboard.")
    return jsonify(metrics), 200


@bp_owner.route("/api/analytics/restaurant/<int:business_id>", methods=["GET"])
@login_required
def api_restaurant_metrics(business_id):
    """Endpoint para desenvolvedores e proprietários auditarem a performance de uma filial isolada."""
    import tasty.services.business_service as b_service
    business = b_service.get_business(business_id)
    
    if not business:
        current_app.logger.warning(f"Proprietário ID {session.get('user_id')} tentou acessar métricas do estabelecimento ID {business_id}, mas não foi encontrado.")
        return jsonify({"error": "Estabelecimento não encontrado."}), 404
        
    if session.get("user_role") != "admin" and not any(o.id == session.get("user_id") for o in business.owners):
        current_app.logger.warning(f"Proprietário ID {session.get('user_id')} tentou acessar métricas do estabelecimento ID {business_id}, mas não tem permissão.")
        return jsonify({"error": "Acesso negado às métricas do estabelecimento."}), 403
        
    metrics = analytics_service.get_restaurant_metrics(business_id)
    current_app.logger.info(f"Proprietário ID {session.get('user_id')} acessou métricas do estabelecimento ID {business_id}.")
    return jsonify(metrics), 200


@bp_owner.route("/list", methods=["GET"])
@login_required
@role_required("admin")
def list_owners():
    """Lista todos os proprietários de negócios para o admin, com opções de editar ou excluir cada um."""
    owners = service.get_all_business_owners()
    current_app.logger.info(f"Admin acessou a lista de proprietários. Total: {len(owners)}")
    return render_template("owner/index.html", users=owners)

@bp_owner.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_owner(id):
    """Permite que o proprietário edite seu perfil. Admins também podem editar qualquer proprietário."""
    if session.get("user_role") != "admin" and session.get("user_id") != id:
        flash("Acesso negado.", "danger")
        current_app.logger.warning(f"Usuário ID {session.get('user_id')} tentou acessar edição do proprietário ID {id}, mas não tem permissão.")
        return redirect(url_for("owner.dashboard"))
    owner_user = service.get_business_owner(id)
    if not owner_user:
        flash("Dono de negócio não encontrado.", "warning")
        current_app.logger.warning(f"Usuário ID {session.get('user_id')} tentou acessar edição do proprietário ID {id}, mas não foi encontrado.")
        return redirect(url_for("owner.dashboard"))
    if request.method == "POST":
        data = dict(request.form)
        success, msg, code = service.update_business_owner(id, data)
        if success:
            flash("Perfil atualizado com sucesso.", "success")
            current_app.logger.info(f"Proprietário ID {id} atualizado com sucesso por usuário ID {session.get('user_id')}. Dados atualizados: {data}")
            return redirect(url_for("owner.dashboard"))
        flash(msg, "danger")
    current_app.logger.info(f"Usuário ID {session.get('user_id')} acessou a edição do proprietário ID {id}.")
    return render_template("owner/form.html", user=owner_user)

@bp_owner.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_owner(id):
    """Permite ao admin excluir (soft delete) um proprietário de negócio da plataforma. Cuidado: isso também pode afetar os restaurantes associados a esse proprietário."""
    success, msg, code = service.delete_business_owner(id)
    flash(msg, "success" if success else "danger")
    current_app.logger.info(f"Admin ID {session.get('user_id')} tentou excluir proprietário ID {id}. Sucesso: {success}. Mensagem: {msg}")
    return redirect(url_for("owner.list_owners"))