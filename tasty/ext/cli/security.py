from flask import current_app
from sqlalchemy.engine.url import make_url
import click


def ensure_safe_seed_environment():
    app_env = current_app.config.get("APP_ENV")

    if app_env != "development":
        raise click.ClickException(
            "OPERACAO BLOQUEADA: Este comando so pode ser executado em ambiente de desenvolvimento."
        )

    if not current_app.config.get("ALLOW_SEED"):
        raise click.ClickException(
            "ALLOW_SEED desabilitado."
        )

    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]

    if not uri.startswith("sqlite:///"):
        raise click.ClickException(
            "Seed permitido apenas em SQLite."
        )

    url = make_url(uri)

    db_name = url.database or ""

    if not db_name.endswith("delivery_dev.db"):
        raise click.ClickException(
            f"Banco inseguro: {db_name}"
        )