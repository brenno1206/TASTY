from flask import (
    Blueprint,
    render_template,
    current_app,
    redirect,
    url_for,
    session,
    request,
    jsonify,
)

from tasty.views.auth import login_required
from tasty.models import User, BusinessType, Address
from tasty.services.swipe_service import get_next_businesses_for_user
from tasty.ext.db import db
from sqlalchemy import select
bp_main = Blueprint("main", __name__)

@bp_main.route("/")
@bp_main.route("/index")
def index():
    current_app.logger.debug("Renderizando index.html")
    return render_template("index.html")

@bp_main.route("/home", methods=["GET"])
@bp_main.route("/dashboard")
@login_required
def home():
    
    user_id = session.get("user_id")
    # mudar isso pra ser em services
    stmt = select(User).where(User.id == user_id)
    user = db.session.execute(stmt).scalar_one_or_none()
    # ate aqui
    if not user:
        return redirect(url_for("auth.login"))

    role = user.role.name if user.role else None


    # =========================
    # CLIENT
    # =========================
    if role == "client":

        has_preferences = len(user.preferences) > 0
        has_location = len(user.addresses) > 0

        # onboarding obrigatório
        if not has_preferences or not has_location:
            return redirect(url_for("main.client_onboarding"))

        # feed swipe
        businesses = get_next_businesses_for_user(user.id)

        return render_template(
            "client/home.html",
            user=user,
            businesses=businesses
        )

    # =========================
    # BUSINESS OWNER
    # =========================
    if role == "owner":

        return render_template(
            "owner/dashboard.html",
            user=user,
            businesses=user.owned_businesses
        )

    # =========================
    # ADMIN
    # =========================
    if role == "admin":

        return render_template(
            "admin/dashboard.html",
            user=user
        )

    # fallback seguro
    return redirect(url_for("auth.login"))

@bp_main.route("/client/onboarding", methods=["GET"])
@login_required
def client_onboarding():
    return render_template("client/onboarding.html")



@bp_main.route("/client/onboarding", methods=["POST"])
@login_required
def client_onboarding_save():
    user_id = session.get("user_id")

    data = request.get_json()

    preferences_ids = data.get("preferences", [])
    address_data = data.get("address")

    user = db.session.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # =========================
    # 1. PREFERÊNCIAS
    # =========================
    if preferences_ids:
        types = db.session.execute(
            select(BusinessType).where(BusinessType.id.in_(preferences_ids))
        ).scalars().all()

        user.preferences.clear()
        user.preferences.extend(types)

    # =========================
    # 2. LOCALIZAÇÃO
    # =========================
    if address_data:
        user.addresses.clear()

        user.addresses.append(Address(**address_data))

    db.session.commit()

    return jsonify({
        "message": "Onboarding concluído com sucesso"
    }), 200

    '''
    FRONTEND ENVIO
    fetch("/client/onboarding", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        preferences: [1, 2, 3],
        address: {
        road: "Rua X",
        number: 123,
        district: "Centro",
        zipcode: "29100-000",
        city_id: 5
        }
    })
    })
    '''