from flask import (
    Blueprint,
    render_template,
    current_app,
    flash,
    redirect,
    url_for,
    request,
)

bp_main = Blueprint("main", __name__)

@bp_main.route("/")
@bp_main.route("/index")
def index():
    current_app.logger.debug("Renderizando index.html")
    return render_template("index.html")