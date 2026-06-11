from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from tasty.utils.decorators import login_required, role_required
import tasty.services.user_service as service
import tasty.services.business_type_service as bt_service
from tasty.services.location_service import geocode_address  # <-- Importado o geocoder

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
        
    address_data = data.get("address")
    if address_data:
        # Se a latitude ou longitude estiverem nulas/ausentes, o Backend processa a conversão!
        if not address_data.get("latitude") or not address_data.get("longitude"):
            lat, lon = geocode_address(
                road=address_data.get("road", ""),
                district=address_data.get("district", ""),
                zipcode=address_data.get("zipcode", "")
            )
            # Atualiza o dicionário com as coordenadas obtidas da API
            address_data["latitude"] = lat
            address_data["longitude"] = lon
            
        update_data["addresses"] = [address_data]

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
    # Proteção: Apenas o próprio cliente ou um admin podem editar
    if session.get("user_role") != "admin" and session.get("user_id") != id:
        flash("Acesso negado.", "danger")
        return redirect(url_for("client.dashboard"))

    client_user = service.get_client(id)
    if not client_user:
        flash("Cliente não encontrado.", "warning")
        return redirect(url_for("client.dashboard"))

    if request.method == "POST":
        data = dict(request.form)
        
        # --- 1. TRATAMENTO DE SENHA ---
        old_pw = data.pop("old_password", "").strip()
        new_pw = data.pop("new_password", "").strip()
        
        if old_pw and new_pw:
            pw_ok, pw_msg, pw_code = service.change_user_password(id, old_pw, new_pw)
            if not pw_ok:
                flash(pw_msg, "danger")
                return redirect(request.url)
            else:
                flash("Senha alterada com sucesso.", "success")

        # --- 2. TRATAMENTO DE PREFERÊNCIAS GASTRONÔMICAS ---
        # Captura os múltiplos IDs enviados pelos checkboxes no formulário
        prefs = request.form.getlist("preferences")
        if prefs:
            data["preferences"] = [int(p) for p in prefs if p.isdigit()]
        else:
            # Caso o usuário tenha desmarcado tudo, enviamos uma lista vazia
            data["preferences"] = []

        # --- 3. TRATAMENTO DE ENDEREÇO E GEOCODIFICAÇÃO ---
        # Verifica se um endereço está sendo enviado
        if data.get("road"):
            # Extrai os dados puros do formulário
            lat_str = data.pop("latitude", None)
            lon_str = data.pop("longitude", None)
            
            lat = float(lat_str) if lat_str else None
            lon = float(lon_str) if lon_str else None
            
            road = data.pop("road", "")
            district = data.pop("district", "")
            zipcode = data.pop("zipcode", "")

            # Geocodificação de fallback se o usuário atualizou a rua, mas não enviou coordenadas manuais
            if not lat or not lon:
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
            return redirect(request.url)
        flash(msg, "danger")

    # --- RENDERIZAÇÃO DO GET ---
    # Busca todas as tags para o front-end desenhar os cartões clicáveis
    tipos_disponiveis = bt_service.get_all_business_types()
    
    return render_template("client/form.html", user=client_user, business_types=tipos_disponiveis)

@bp_client.route("/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_client(id):
    success, msg, code = service.delete_client(id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("client.list_clients"))