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
    """Lista a equipe de administradores no painel Tailwind."""
    # Aqui estava o erro da tabela vazia! Agora estamos buscando os dados corretamente:
    equipe = service.get_all_admins()
    return render_template("admin/list_team.html", users=equipe)


@bp_admin.route("/businesses", methods=["GET"])
@login_required
@role_required("admin")
def list_all_businesses():
    """Tela do administrador para visualizar TODOS os restaurantes cadastrados."""
    # Resolve a falta do gerenciamento de cada business
    todos_restaurantes = b_service.get_all_businesses()
    return render_template("admin/businesses.html", businesses=todos_restaurantes)


@bp_admin.route("/business_types", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_business_types():
    """Tela para criar e listar as Categorias Gastronômicas (Tags)."""
    # Resolve o Erro 404
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
            flash("Perfil atualizado com sucesso.", "success")
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