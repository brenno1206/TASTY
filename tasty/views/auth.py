from flask import (
    Blueprint,
    render_template,
    current_app,
    flash,
    redirect,
    url_for,
    request,
)

bp_auth = Blueprint("auth", __name__)

@bp_auth.route("/login")
def index():
    current_app.logger.debug("Renderizando LOGIN")
    return render_template("main/index.html")
