import os
from dotenv import load_dotenv

# Força o carregamento do contexto de dev antes de iniciar a configuração
load_dotenv(".env.dev", override=True)

def init_app(app):
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # ======================================================
    # CONFIGURAÇÕES DE AMBIENTE E SEGURANÇA
    # ======================================================
    app.config['APP_ENV'] = os.environ.get('APP_ENV', 'production')
    
    # Converte valores como '1', 'true', 'yes' para o booleano True e o resto para False
    allow_seed_str = str(os.environ.get('ALLOW_SEED', '0')).lower()
    app.config['ALLOW_SEED'] = allow_seed_str in ['1', 'true', 'yes']

    # ======================================================
    # MODO 1: DATABASE URL EXPLÍCITO (PROD / TEST / REMOTO)
    # ======================================================
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    # ======================================================
    # MODO 2: SQLITE LOCAL (DEV / TEST LOCAL)
    # ======================================================
    else:
        database_name = os.environ.get("DATABASE_NAME")

        if not database_name:
            raise RuntimeError("DATABASE_URL ou DATABASE_NAME deve ser configurado.")

        # Garante que a pasta instance existe antes de criar o banco SQLite
        os.makedirs(app.instance_path, exist_ok=True)
        db_path = os.path.join(app.instance_path, database_name)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    # As configurações abaixo agora serão executadas em ambos os modos
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    if app.debug:
        app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        app.config['DEBUG_TB_PANELS'] = (
            'flask_debugtoolbar.panels.versions.VersionDebugPanel',
            'flask_debugtoolbar.panels.timer.TimerDebugPanel',
            'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
            'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
            'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
            'flask_debugtoolbar.panels.template.TemplateDebugPanel',
            'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
            'flask_debugtoolbar.panels.logger.LoggingPanel',
            'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
        )