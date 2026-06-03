from flask import Flask
import logging
from tasty.ext.cli import init_app as init_cli


def create_app(test_config=None):
    app = Flask(__name__)

    # Configuracao recomendada para desenvolvimento:
    # Mostra mensagens DEBUG e INFO no console

    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    # ----------------------------------------------------------
    # Configuracao da aplicacao (variaveis de ambiente)
    # ----------------------------------------------------------

    from tasty.ext.config import init_app as init_config
    init_config(app)

    if test_config:
        app.config.update(test_config)

    # ----------------------------------------------------------
    # Inicializacao do banco de dados
    # ----------------------------------------------------------

    from tasty.ext.db import init_app as init_db
    init_db(app)

    # Registro dos modelos no metadata do SQLAlchemy
    from tasty.ext.db import register_models
    register_models()
    
    init_cli(app)

    # ----------------------------------------------------------
    # Outras extensoes
    # ----------------------------------------------------------
    
    if not app.config.get("TESTING"):
        from tasty.ext.wtf import init_app as init_wtf
        init_wtf(app)

    from tasty.ext.debugtoolbar import init_app as init_toolbar
    init_toolbar(app)

    # ----------------------------------------------------------
    # Blueprints (camada de apresentacao)
    # ----------------------------------------------------------
    
    from tasty.views import init_app as init_webpage
    init_webpage(app)

    return app