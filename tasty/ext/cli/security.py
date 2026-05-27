import click
from flask import current_app
from sqlalchemy.engine.url import make_url

def ensure_safe_seed_environment():
    """
    Garante que as operações de seed sejam feitas única e exclusivamente 
    em um ambiente de desenvolvimento isolado.
    """
    
    app_env = current_app.config.get("APP_ENV", "production") # Assume produção por padrão, é mais seguro

    if app_env != "development":
        raise click.ClickException(
            "OPERAÇÃO BLOQUEADA: Este comando só pode ser executado em ambiente de desenvolvimento. "
            f"Ambiente atual detectado: {app_env}"
        )

    if not current_app.config.get("ALLOW_SEED"):
        raise click.ClickException(
            "OPERAÇÃO BLOQUEADA: A configuração 'ALLOW_SEED' não está habilitada."
        )

    uri = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    
    if not uri:
        raise click.ClickException("Erro: Nenhuma URI de banco de dados configurada.")

    if not uri.startswith("sqlite:///"):
        raise click.ClickException(
            "OPERAÇÃO BLOQUEADA: Seed permitido apenas em bancos de dados SQLite (proteção contra execução remota)."
        )

    url = make_url(uri)

    # O formato da string do sqlite/// varia um pouco. Pegamos a database e garantimos que é uma string.
    db_name = str(url.database) if url.database else ""

    if not db_name.endswith("tasty_dev.db"):
        raise click.ClickException(
            f"OPERAÇÃO BLOQUEADA: Banco de dados inseguro para operação de seed: '{db_name}'. "
            "Esperava-se 'tasty_dev.db'."
        )