from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from tasty.utils.decorators import login_required, role_required
import tasty.services.business_service as b_service
import tasty.services.business_type_service as bt_service 

bp_business_panel = Blueprint("business_panel", __name__, url_prefix="/my-business")

@bp_business_panel.route("/list", methods=["GET"])
@login_required
@role_required("owner")
def list_my_businesses():
    """Lista todos os restaurantes associados ao proprietário logado."""
    all_places = b_service.get_all_businesses()
    user_id = session["user_id"]
    
    my_places = [b for b in all_places if any(owner.id == user_id for owner in b.owners)]
    current_app.logger.info(f"Proprietário ID {user_id} acessou a lista de seus estabelecimentos. Total encontrados: {len(my_places)}.")
    return render_template("owner/my_businesses.html", businesses=my_places)


@bp_business_panel.route("/register", methods=["GET", "POST"])
@login_required
@role_required("owner")
def register_business():
    """Permite ao proprietário cadastrar um novo restaurante na plataforma."""
    if request.method == "POST":
        data = {
            "corporate_name": request.form.get("corporate_name"),
            "trade_name": request.form.get("trade_name"),
            "cnpj": request.form.get("cnpj"),
            "description": request.form.get("description"),
            "opening_time": request.form.get("opening_time"),
            "closing_time": request.form.get("closing_time"),
            "owners": [session["user_id"]],
            
            "business_types": [int(t) for t in request.form.getlist("business_types") if t.isdigit()],
            
            "addresses": [{
                "road": request.form.get("road"),
                "number": int(request.form.get("number")) if request.form.get("number") else None,
                "district": request.form.get("district"),
                "zipcode": request.form.get("zipcode"),
                "latitude": float(request.form.get("latitude")) if request.form.get("latitude") else None,
                "longitude": float(request.form.get("longitude")) if request.form.get("longitude") else None,
                "city_id": int(request.form.get("city_id")) if request.form.get("city_id") else None
            }],
            "photos": request.form.getlist("photos_urls")
        }

        success, msg, code = b_service.create_business(data)
        if success:
            flash("Estabelecimento cadastrado com sucesso!", "success")
            current_app.logger.info(f"Proprietário ID {session.get('user_id')} cadastrou novo estabelecimento: {data['corporate_name']}.")
            return redirect(url_for("business_panel.list_my_businesses"))
        flash(msg, "danger")

    tipos = bt_service.get_all_business_types()
    current_app.logger.info(f"Proprietário ID {session.get('user_id')} acessou a página de cadastro de estabelecimento. Total categorias disponíveis: {len(tipos)}.")
    return render_template("owner/business_form.html", action="Cadastrar", business_types=tipos)


@bp_business_panel.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("owner")
def edit_business(id):
    """Permite editar os detalhes operacionais do restaurante."""
    business = b_service.get_business(id)
    user_id = session["user_id"]

    if not business or not any(owner.id == user_id for owner in business.owners):
        flash("Estabelecimento não encontrado ou permissão negada.", "danger")
        current_app.logger.warning(f"Proprietário ID {user_id} tentou acessar edição do estabelecimento ID {id}, mas não foi encontrado ou permissão negada.")
        return redirect(url_for("business_panel.list_my_businesses"))

    if request.method == "POST":
        data = {
            "corporate_name": request.form.get("corporate_name"),
            "trade_name": request.form.get("trade_name"),
            "description": request.form.get("description"),
            "opening_time": request.form.get("opening_time"),
            "closing_time": request.form.get("closing_time"),
            
            "business_types": [int(t) for t in request.form.getlist("business_types") if t.isdigit()]
        }
        
        if request.form.get("road"):
            data["addresses"] = [{
                "road": request.form.get("road"),
                "number": int(request.form.get("number")) if request.form.get("number") else None,
                "district": request.form.get("district"),
                "zipcode": request.form.get("zipcode"),
                "latitude": float(request.form.get("latitude")) if request.form.get("latitude") else None,
                "longitude": float(request.form.get("longitude")) if request.form.get("longitude") else None,
                "city_id": int(request.form.get("city_id")) if request.form.get("city_id") else None
            }]

        success, msg, code = b_service.update_business(id, data)
        if success:
            flash("Informações salvas com sucesso.", "success")
            current_app.logger.info(f"Proprietário ID {user_id} editou estabelecimento ID {id}. Dados atualizados: {data}")
            return redirect(url_for("business_panel.list_my_businesses"))
        flash(msg, "danger")

    tipos = bt_service.get_all_business_types()
    current_app.logger.info(f"Proprietário ID {session.get('user_id')} acessou a edição do estabelecimento ID {id}. Total categorias disponíveis: {len(tipos)}.")
    return render_template("owner/business_form.html", business=business, action="Editar", business_types=tipos)


@bp_business_panel.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("owner")
def delete_business(id):
    """Permite ao proprietário excluir um restaurante que ele possui."""
    business = b_service.get_business(id)
    user_id = session["user_id"]

    if not business or not any(owner.id == user_id for owner in business.owners):
        flash("Permissão negada.", "danger")
        current_app.logger.warning(f"Proprietário ID {user_id} tentou excluir estabelecimento ID {id}, mas não foi encontrado ou permissão negada.")
        return redirect(url_for("business_panel.list_my_businesses"))

    success, msg, code = b_service.delete_business(id)
    flash(msg, "success" if success else "danger")
    current_app.logger.info(f"Proprietário ID {user_id} excluiu estabelecimento ID {id}. Sucesso: {success}. Mensagem: {msg}")
    return redirect(url_for("business_panel.list_my_businesses"))