from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from tasty.utils.decorators import login_required, role_required

# Importação de todos os serviços necessários
import tasty.services.user_service as service
import tasty.services.analytics_service as analytics_service
import tasty.services.business_service as b_service
import tasty.services.business_type_service as bt_service
from tasty.models import BusinessType
from tasty.ext.db import db

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")

@bp_admin.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    """Painel principal com as métricas globais."""
    stats = analytics_service.get_global_metrics()
    return render_template("admin/dashboard.html", stats=stats)


@bp_admin.route("/list", methods=["GET"])
@login_required
@role_required("admin")
def list_admins():
    """Lista a equipe garantindo o admin logado no topo e apenas subordinados abaixo."""
    admin_id = session.get("user_id")
    current_admin = service.get_admin(admin_id)
    
    if not current_admin or not current_admin.role or not current_admin.role.level:
        session.clear()
        flash("Sessão inválida ou sem permissões. Por favor, faça login novamente.", "danger")
        return redirect(url_for("auth.login"))

    all_admins = service.get_all_admins()

    # Mapeamento de hierarquia estruturado
    level_weights = {
        "max": 4,
        "premium": 3,
        "basic": 2,
        "support": 1
    }

    # Helper seguro para extrair o nome do nível em minúsculo
    def get_level_name(admin_user):
        if admin_user.role and admin_user.role.level:
            lvl = admin_user.role.level
            return str(lvl.name if hasattr(lvl, 'name') else lvl).strip().lower()
        return ""

    current_lvl = get_level_name(current_admin)
    current_weight = level_weights.get(current_lvl, 0)

    # CORREÇÃO: Força o administrador logado a ser o PRIMEIRO elemento do array
    filtered_admins = [current_admin]

    for u in all_admins:
        # Pula o próprio usuário logado para ele não aparecer duplicado na lista
        if u.id == current_admin.id:
            continue
            
        target_lvl = get_level_name(u)
        target_weight = level_weights.get(target_lvl, 0)
        
        # REGRA ESTRITA: Só adiciona se o nível do alvo for estritamente menor (<)
        # Isso remove outros "Max" da lista da Daphne e outros "Basic" da lista do qa1
        if target_weight < current_weight:
            filtered_admins.append(u)

    return render_template("admin/list_team.html", users=filtered_admins)


@bp_admin.route("/businesses", methods=["GET"])
@login_required
@role_required("admin")
def list_all_businesses():
    """Tela do administrador para visualizar TODOS os restaurantes cadastrados."""
    todos_restaurantes = b_service.get_all_businesses()
    return render_template("admin/businesses.html", businesses=todos_restaurantes)


@bp_admin.route("/business_types", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_business_types():
    """Tela para criar e listar as Categorias Gastronômicas (Tags)."""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        emoji = request.form.get("emoji")
        
        if not name:
            flash("O nome da categoria é obrigatório.", "danger")
        else:
            try:
                nova_cat = BusinessType(name=name, description=description, emoji=emoji)
                db.session.add(nova_cat)
                db.session.commit()
                flash(f"Categoria '{name}' criada com sucesso!", "success")
                return redirect(url_for("admin.manage_business_types"))
            except Exception as e:
                db.session.rollback()
                flash(f"Erro ao salvar categoria: {str(e)}", "danger")

    categorias = bt_service.get_all_business_types()
    return render_template("admin/business_types.html", types=categorias)


@bp_admin.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_admin(id):
    """Edita os dados de um administrador da equipe."""
    admin_user = service.get_admin(id)
    if not admin_user:
        flash("Administrador não encontrado.", "warning")
        return redirect(url_for("admin.list_admins"))

    if request.method == "POST":
        data = dict(request.form)
        success, msg, code = service.update_admin(id, data)
        if success:
            flash("Perfil updated com sucesso.", "success")
            return redirect(url_for("admin.list_admins"))
        flash(msg, "danger")

    return render_template("admin/form.html", user=admin_user)


@bp_admin.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_admin(id):
    """Desativa um administrador."""
    success, msg, code = service.delete_admin(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("admin.list_admins"))