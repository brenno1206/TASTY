from flask import Blueprint, render_template, current_app

bp_main = Blueprint("main", __name__)

@bp_main.route("/")
@bp_main.route("/index")
def index():
    """Página de aterrissagem pública (Landing Page Institucional)."""
    current_app.logger.debug("Renderizando index.html da página pública.")
    return render_template("index.html")