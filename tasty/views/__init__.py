from tasty.views.auth import bp_auth
from tasty.views.admin import bp_admin
from tasty.views.client import bp_client
from tasty.views.owner import bp_owner
from tasty.views.business_panel import bp_business_panel
from tasty.views.discovery import bp_discovery
from tasty.views.main import bp_main


def init_app(app):
    app.logger.info("Criando Blueprint auth")
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_client)
    app.register_blueprint(bp_owner)
    app.register_blueprint(bp_business_panel)
    app.register_blueprint(bp_discovery)
    app.register_blueprint(bp_main)