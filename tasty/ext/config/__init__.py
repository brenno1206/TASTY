import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta

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
    database_name = os.environ.get("DATABASE_NAME", "tasty_dev.db")

    instance_dir = Path(app.instance_path)
    instance_dir.mkdir(parents=True, exist_ok=True)

    db_path = instance_dir / database_name

    # 🔥 IMPORTANTE: formato Windows-safe absoluto
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.as_posix()

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

    # ---------------------------------------------------------
    # SEGURANÇA E SESSÃO
    # ---------------------------------------------------------
    # Define o tempo de vida da sessão (ex: 2 horas)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    
    # Proteções adicionais contra interceptação de cookies
    app.config['SESSION_COOKIE_HTTPONLY'] = True 
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'