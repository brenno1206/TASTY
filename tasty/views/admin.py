from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from tasty.utils.decorators import login_required, role_required

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
    current_app.logger.info(f"Admin Dashboard acessado por usuário ID {session.get('user_id')}. Métricas carregadas: {stats}")
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
        current_app.logger.warning(f"Admin ID {admin_id} com sessão inválida ou sem role/level. Forçando logout.")
        return redirect(url_for("auth.login"))

    all_admins = service.get_all_admins()

    level_weights = {
        "max": 4,
        "premium": 3,
        "basic": 2,
        "support": 1
    }

    def get_level_name(admin_user):
        if admin_user.role and admin_user.role.level:
            lvl = admin_user.role.level
            return str(lvl.name if hasattr(lvl, 'name') else lvl).strip().lower()
        return ""

    current_lvl = get_level_name(current_admin)
    current_weight = level_weights.get(current_lvl, 0)

    filtered_admins = [current_admin]

    for u in all_admins:
        if u.id == current_admin.id:
            continue
            
        target_lvl = get_level_name(u)
        target_weight = level_weights.get(target_lvl, 0)
        
        if target_weight < current_weight:
            filtered_admins.append(u)
    current_app.logger.info(f"Admin ID {admin_id} listou a equipe. Total admins: {len(all_admins)}, Exibidos: {len(filtered_admins)}.")
    return render_template("admin/list_team.html", users=filtered_admins)


@bp_admin.route("/businesses", methods=["GET"])
@login_required
@role_required("admin")
def list_all_businesses():
    """Tela do administrador para visualizar TODOS os restaurantes cadastrados."""
    todos_restaurantes = b_service.get_all_businesses()
    current_app.logger.info(f"Admin ID {session.get('user_id')} listou todos os restaurantes. Total: {len(todos_restaurantes)}.")
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
                current_app.logger.info(f"Admin ID {session.get('user_id')} criou nova categoria gastronômica: {name}.")
                return redirect(url_for("admin.manage_business_types"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erro ao criar categoria gastronômica: {str(e)}")
                flash(f"Erro ao salvar categoria: {str(e)}", "danger")

    categorias = bt_service.get_all_business_types()
    current_app.logger.info(f"Admin ID {session.get('user_id')} acessou a gestão de categorias gastronômicas. Total categorias: {len(categorias)}.")
    return render_template("admin/business_types.html", types=categorias)


@bp_admin.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_admin(id):
    """Edita os dados de um administrador da equipe."""
    admin_user = service.get_admin(id)
    if not admin_user:
        flash("Administrador não encontrado.", "warning")
        current_app.logger.warning(f"Admin ID {session.get('user_id')} tentou editar admin ID {id}, mas não foi encontrado.")
        return redirect(url_for("admin.list_admins"))

    if request.method == "POST":
        data = dict(request.form)
        success, msg, code = service.update_admin(id, data)
        if success:
            current_app.logger.info(f"Administrador atualizado com sucesso (ID: {id}).")
            flash("Perfil atualizado com sucesso.", "success")
            current_app.logger.info(f"Admin ID {session.get('user_id')} editou admin ID {id}. Dados atualizados: {data}")
            return redirect(url_for("admin.list_admins"))
        flash(msg, "danger")

    current_app.logger.info(f"Admin ID {session.get('user_id')} acessou a edição do admin ID {id}.")
    return render_template("admin/form.html", user=admin_user)


@bp_admin.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_admin(id):
    """Desativa um administrador."""
    success, msg, code = service.delete_admin(id)
    flash(msg, "success" if success else "danger")
    current_app.logger.info(f"Admin ID {session.get('user_id')} tentou desativar admin ID {id}. Sucesso: {success}. Mensagem: {msg}")
    return redirect(url_for("admin.list_admins"))