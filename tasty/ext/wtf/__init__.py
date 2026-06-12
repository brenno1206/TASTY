from flask_wtf import CSRFProtect

csrf = CSRFProtect()

def init_app(app):
    """Inicializa a extensão Flask-WTF (CSRF Protection) com o aplicativo Flask."""
    app.logger.info("Inicializando Flask-WTF (CSRF Protection)...")
    if not app.config.get("TESTING"):
        csrf.init_app(app)