from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    """Inicializa a extensão SQLAlchemy com o aplicativo Flask."""
    app.logger.info("Inicializando extensão SQLAlchemy...")
    db.init_app(app)

def register_models():
    """
    Importa todos os modulos que definem modelos para que sejam registrados
    no metadata do SQLAlchemy antes de operacoes como create_all().
    """
    import tasty.models