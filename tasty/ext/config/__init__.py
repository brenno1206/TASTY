import os
from dotenv import load_dotenv


def init_app(app):
    # Carrega variaveis do ambiente (ja selecionado via tasks.py)
    load_dotenv(override=True)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG") == "1"

    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
    app.config["MAIL_PORT"] = os.environ.get("MAIL_PORT")
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS") == "True"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

    if app.debug:
        app.config["DEBUG_TB_TEMPLATE_EDITOR_ENABLED"] = True
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
