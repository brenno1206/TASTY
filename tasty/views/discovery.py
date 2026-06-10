from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from tasty.utils.decorators import login_required, role_required
import tasty.services.swipe_service as swipe_service
import tasty.services.user_service as user_service
import tasty.services.business_service as business_service
from tasty.services.location_service import get_distance_between_user_and_business

bp_discovery = Blueprint("discovery", __name__, url_prefix="/discovery")

@bp_discovery.route("/feed", methods=["GET"])
@login_required
@role_required("client")
def feed():
    user_id = session["user_id"]
    
    user = user_service.get_client(user_id)
    has_preferences = len(user.preferences) > 0
    has_location = len(user.addresses) > 0 and user.addresses[0].latitude is not None

    if not has_preferences or not has_location:
        flash("Por favor, conclua seu perfil e informe sua localização exata para explorarmos as distâncias.", "warning")
        return redirect(url_for("client.onboarding"))

    businesses = swipe_service.get_next_businesses_for_user(user_id, limit=20)
    
    for b in businesses:
        dist = get_distance_between_user_and_business(user_id, b.id)
        b.distance_km = dist if dist is not None else "--"
    
    return render_template("discovery/feed.html", businesses=businesses)


@bp_discovery.route("/swipe", methods=["POST"])
@login_required
@role_required("client")
def swipe():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Dados inválidos."}), 400

    user_id = session["user_id"]
    business_id = data.get("business_id")
    liked = data.get("liked")
    super_like = data.get("super_like", False)

    if business_id is None or liked is None:
        return jsonify({"success": False, "message": "Campos obrigatórios ausentes."}), 400

    success, msg, code = swipe_service.swipe_business(
        user_id=user_id,
        business_id=business_id,
        liked=liked,
        super_like=super_like
    )

    return jsonify({"success": success, "message": msg}), code


@bp_discovery.route("/favorites", methods=["GET"])
@login_required
@role_required("client")
def favorites():
    user_id = session["user_id"]
    liked_places = swipe_service.get_liked_businesses(user_id)
    
    for b in liked_places:
        dist = get_distance_between_user_and_business(user_id, b.id)
        b.distance_km = dist if dist is not None else "--"

    return render_template("discovery/favorites.html", businesses=liked_places)

# --- NOVA ROTA DE DETALHES ---
@bp_discovery.route("/restaurant/<int:id>", methods=["GET"])
@login_required
@role_required("client")
def restaurant_details(id):
    """Página de perfil detalhada de um restaurante que deu Match."""
    business = business_service.get_business(id)
    if not business:
        flash("Restaurante não encontrado ou inativo.", "danger")
        return redirect(url_for("discovery.favorites"))
        
    user_id = session["user_id"]
    dist = get_distance_between_user_and_business(user_id, business.id)
    business.distance_km = dist if dist is not None else "--"
    
    return render_template("discovery/details.html", business=business)


@bp_discovery.route("/reset", methods=["POST"])
@login_required
@role_required("client")
def reset_history():
    user_id = session["user_id"]
    success, msg, code = swipe_service.reset_user_swipes(user_id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("discovery.feed"))