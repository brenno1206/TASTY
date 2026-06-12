from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, current_app
from tasty.utils.decorators import login_required, role_required
import tasty.services.user_service as service
import tasty.services.business_type_service as bt_service
from tasty.services.location_service import geocode_address

bp_client = Blueprint("client", __name__, url_prefix="/client")

@bp_client.route("/dashboard")
@login_required
@role_required("client")
def dashboard():
    """Dashboard principal do cliente, mostrando recomendações e status do onboarding."""
    current_app.logger.info(f"Cliente ID {session.get('user_id')} acessou o dashboard.")
    return render_template("client/dashboard.html")

@bp_client.route("/onboarding", methods=["GET"])
@login_required
@role_required("client")
def onboarding():
    """Página de onboarding para clientes, onde podem definir preferências e endereço."""
    tipos_disponiveis = bt_service.get_all_business_types()
    current_app.logger.info(f"Cliente ID {session.get('user_id')} acessou a página de onboarding.")
    return render_template("client/onboarding.html", business_types=tipos_disponiveis)

@bp_client.route("/onboarding", methods=["POST"])
@login_required
@role_required("client")
def save_onboarding():
    """Processa os dados do onboarding, incluindo preferências gastronômicas e endereço."""
    user_id = session.get("user_id")
    data = request.get_json()

    if not data:
        current_app.logger.warning(f"Cliente ID {user_id} enviou dados de onboarding vazios ou inválidos.")
        return jsonify({"error": "Nenhum dado fornecido."}), 400

    update_data = {}
    if data.get("preferences"):
        update_data["preferences"] = data.get("preferences")
        
    address_data = data.get("address")
    if address_data:
        if not address_data.get("latitude") or not address_data.get("longitude"):
            lat, lon = geocode_address(
                road=address_data.get("road", ""),
                district=address_data.get("district", ""),
                zipcode=address_data.get("zipcode", "")
            )
            address_data["latitude"] = lat
            address_data["longitude"] = lon
            
        update_data["addresses"] = [address_data]

    success, msg, code = service.update_client(user_id, update_data)

    if success:
        current_app.logger.info(f"Cliente ID {user_id} concluiu o onboarding.")
        return jsonify({"message": "Onboarding concluído com sucesso."}), 200
        
    current_app.logger.warning(f"Cliente ID {user_id} falhou ao concluir o onboarding. Erro: {msg}")
    return jsonify({"error": msg}), code

@bp_client.route("/list", methods=["GET"])
@login_required
@role_required("admin") 
def list_clients():
    """Lista todos os clientes para o admin, com opções de editar ou excluir cada um."""
    clients = service.get_all_clients()
    current_app.logger.info(f"Admin ID {session.get('user_id')} acessou a lista de clientes.")
    return render_template("client/index.html", users=clients)

@bp_client.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(id):
    """Permite que o cliente edite seu perfil, incluindo preferências gastronômicas e endereço. Admins também podem editar qualquer cliente."""
    if session.get("user_role") != "admin" and session.get("user_id") != id:
        flash("Acesso negado.", "danger")
        current_app.logger.warning(f"Usuário ID {session.get('user_id')} tentou acessar edição do cliente ID {id}, mas não tem permissão.")
        return redirect(url_for("client.dashboard"))

    client_user = service.get_client(id)
    if not client_user:
        flash("Cliente não encontrado.", "warning")
        current_app.logger.warning(f"Usuário ID {session.get('user_id')} tentou acessar edição do cliente ID {id}, mas o cliente não foi encontrado.")
        return redirect(url_for("client.dashboard"))

    if request.method == "POST":
        data = dict(request.form)
        
        old_pw = data.pop("old_password", "").strip()
        new_pw = data.pop("new_password", "").strip()
        
        if old_pw and new_pw:
            pw_ok, pw_msg, pw_code = service.change_user_password(id, old_pw, new_pw)
            if not pw_ok:
                flash(pw_msg, "danger")
                current_app.logger.warning(f"Cliente ID {id} tentou alterar senha, mas falhou. Erro: {pw_msg}")
                return redirect(request.url)
            else:
                flash("Senha alterada com sucesso.", "success")

        prefs = request.form.getlist("preferences")
        if prefs:
            data["preferences"] = [int(p) for p in prefs if p.isdigit()]
        else:
            data["preferences"] = []

        if data.get("road"):
            road = data.pop("road", "")
            district = data.pop("district", "")
            zipcode = data.pop("zipcode", "")
            lat, lon = geocode_address(road=road, district=district, zipcode=zipcode)

            data["addresses"] = [{
                "road": road,
                "number": int(data.pop("number")) if data.get("number") else None,
                "district": district,
                "zipcode": zipcode,
                "latitude": lat,
                "longitude": lon,
            }]

        success, msg, code = service.update_client(id, data)
        
        if success:
            flash("Perfil atualizado com sucesso.", "success")
            current_app.logger.info(f"Cliente ID {id} atualizou seu perfil. Dados atualizados: {data}")
            return redirect(request.url)
        flash(msg, "danger")

    tipos_disponiveis = bt_service.get_all_business_types()
    
    current_app.logger.info(f"Cliente ID {session.get('user_id')} acessou a edição do cliente ID {id}. Total categorias disponíveis: {len(tipos_disponiveis)}.")
    return render_template("client/form.html", user=client_user, business_types=tipos_disponiveis)

@bp_client.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_client(id):
    """Permite que o admin aplique soft-delete em um cliente, desativando sua conta e ocultando seus dados."""
    success, msg, code = service.delete_client(id)
    current_app.logger.info(f"Admin ID {session.get('user_id')} aplicou soft-delete no cliente ID {id}.")
    flash(msg, "success" if success else "danger")
    return redirect(url_for("client.list_clients"))