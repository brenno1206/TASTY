from flask import Blueprint, render_template, current_app
import tasty.services.business_type_service as bt_service

bp_main = Blueprint("main", __name__)

@bp_main.route("/")
@bp_main.route("/index")
def index():
    """Página de aterrissagem pública (Landing Page Institucional)."""
    current_app.logger.debug("Renderizando index.html da página pública.")
    
    # Busca as categorias reais do banco de dados. 
    # Usamos [:6] para garantir que o layout em grid da página inicial não seja quebrado 
    # caso o banco de dados possua dezenas de categorias no futuro.
    categorias_bd = bt_service.get_all_business_types()[:6]
    
    return render_template("index.html", categorias=categorias_bd)