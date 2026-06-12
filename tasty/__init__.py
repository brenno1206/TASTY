from flask import Flask
import logging
from tasty.ext.cli import init_app as init_cli

def create_app(test_config=None):
    """Factory de aplicação Flask para criar e configurar a instância do app."""
    app = Flask(__name__)

    # ----------------------------------------------------------
    # Configuracao da aplicacao (variaveis de ambiente)
    # ----------------------------------------------------------
    app.logger.setLevel(logging.INFO)
    app.logger.info("Iniciando a aplicação Tasty...")
    from tasty.ext.config import init_app as init_config
    init_config(app)

    if test_config:
        app.config.update(test_config)
        app.logger.info("Configurações de teste aplicadas.")

    # ----------------------------------------------------------
    # Inicializacao do banco de dados
    # ----------------------------------------------------------
    from tasty.ext.db import init_app as init_db
    init_db(app)
    app.logger.info("Banco de dados inicializado com sucesso.")

    from tasty.ext.db import register_models
    register_models()
    app.logger.info("Modelos de banco de dados registrados.")
    
    # ----------------------------------------------------------
    # Painel Administrativo Automático (Flask-Admin)
    # ----------------------------------------------------------
    from tasty.ext.admin import init_app as init_admin
    init_admin(app)
    app.logger.info("Painel administrativo configurado.")

    # ----------------------------------------------------------
    # Outras extensoes
    # ----------------------------------------------------------
    init_cli(app)
    
    if not app.config.get("TESTING"):
        from tasty.ext.wtf import init_app as init_wtf
        init_wtf(app)
        app.logger.info("Extensão WTForms inicializada.")

    from tasty.ext.debugtoolbar import init_app as init_toolbar
    init_toolbar(app)
    app.logger.info("Toolbar de depuração inicializada.")

    # ----------------------------------------------------------
    # Blueprints (camada de apresentacao)
    # ----------------------------------------------------------
    from tasty.views import init_app as init_webpage
    init_webpage(app)
    app.logger.info("Blueprints de rotas registrados.")

    return app