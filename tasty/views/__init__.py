from tasty.views.auth import bp_auth
from tasty.views.admin import bp_admin
from tasty.views.client import bp_client
from tasty.views.owner import bp_owner
from tasty.views.business_panel import bp_business_panel
from tasty.views.discovery import bp_discovery
from tasty.views.main import bp_main


def init_app(app):
    """Registra os blueprints de rotas na aplicação Flask."""
    app.register_blueprint(bp_auth)
    app.logger.info("Blueprint de autenticação registrado.")
    app.register_blueprint(bp_admin)
    app.logger.info("Blueprint administrativo registrado.")
    app.register_blueprint(bp_client)
    app.logger.info("Blueprint de cliente registrado.")
    app.register_blueprint(bp_owner)
    app.logger.info("Blueprint de proprietário registrado.")
    app.register_blueprint(bp_business_panel)
    app.logger.info("Blueprint do painel de negócios registrado.")
    app.register_blueprint(bp_discovery)
    app.logger.info("Blueprint de descoberta registrado.")
    app.register_blueprint(bp_main)
    app.logger.info("Blueprint principal registrado.")