from flask import Blueprint, render_template, current_app
import tasty.services.business_type_service as bt_service

bp_main = Blueprint("main", __name__)

@bp_main.route("/")
@bp_main.route("/index")
def index():
    """Página de aterrissagem pública (Landing Page Institucional)."""
    categorias_bd = bt_service.get_all_business_types()[:6]
    
    current_app.logger.info("Página inicial acessada. Total categorias carregadas: {}".format(len(categorias_bd)))
    return render_template("index.html", categorias=categorias_bd)