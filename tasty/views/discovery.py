from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from tasty.utils.decorators import login_required, role_required
import tasty.services.swipe_service as swipe_service
import tasty.services.user_service as user_service

bp_discovery = Blueprint("discovery", __name__, url_prefix="/discovery")

@bp_discovery.route("/feed", methods=["GET"])
@login_required
@role_required("client")
def feed():
    """Renderiza a página principal do feed de descoberta (Interface estilo Tinder)."""
    user_id = session["user_id"]
    
    # Validação de Onboarding: Bloqueia o uso do aplicativo se o cliente não tiver endereço ou preferências
    user = user_service.get_client(user_id)
    has_preferences = len(user.preferences) > 0
    has_location = len(user.addresses) > 0

    if not has_preferences or not has_location:
        flash("Por favor, conclua seu perfil e informe sua localização antes de explorar os restaurantes.", "warning")
        return redirect(url_for("client.onboarding"))

    # Carrega os próximos 20 estabelecimentos ativos que o usuário ainda não interagiu
    businesses = swipe_service.get_next_businesses_for_user(user_id, limit=20)
    
    return render_template("discovery/feed.html", businesses=businesses)


@bp_discovery.route("/swipe", methods=["POST"])
@login_required
@role_required("client")
def swipe():
    """
    Processa a ação de swipe via requisição assíncrona (Fetch/AJAX do front-end).
    Espera um JSON: { "business_id": 1, "liked": true, "super_like": false }
    """
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
    """Lista todos os estabelecimentos que o cliente curtiu (Lista de desejos/Matches)."""
    user_id = session["user_id"]
    liked_places = swipe_service.get_liked_businesses(user_id)
    return render_template("discovery/favorites.html", businesses=liked_places)


@bp_discovery.route("/reset", methods=["POST"])
@login_required
@role_required("client")
def reset_history():
    """Permite ao usuário limpar seu histórico e ver todos os restaurantes novamente."""
    user_id = session["user_id"]
    success, msg, code = swipe_service.reset_user_swipes(user_id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for("discovery.feed"))