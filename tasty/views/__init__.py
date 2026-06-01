from tasty.views.main import bp_main
from tasty.views.auth import bp_auth

def init_app(app):
    app.register_blueprint(bp_main)
    app.logger.info("Criando Blueprint main")
    app.register_blueprint(bp_auth)
    app.logger.info("Criando Blueprint auth")
