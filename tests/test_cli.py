import pytest
import click
from tasty.ext.cli.security import ensure_safe_seed_environment

def test_cli_seed_and_db_commands(app, mocker):
    """Testa a geração massiva de dados e os comandos de banco do terminal."""
    mocker.patch("tasty.ext.cli.ensure_safe_seed_environment", return_value=None)
    
    mocker.patch("tasty.ext.cli.generate_password_hash", return_value="hash_falso")

    app.config["ENV"] = "development"
    app.debug = True
    
    runner = app.test_cli_runner()
    
    res_drop = runner.invoke(args=["drop-db"], input="y\n")
    assert res_drop.exit_code == 0
    res_create = runner.invoke(args=["create-db"])
    assert res_create.exit_code == 0
    
    res_seed = runner.invoke(args=["seed-dev"], input="y\ny\n")    
    
    assert res_seed.exit_code == 0
    assert "SUCESSO" in res_seed.output

def test_security_blocks_production_seed(app):
    """Garante que o seed seja bloqueado em ambientes incorretos (Cobre security.py)."""
    
    app.config["APP_ENV"] = "production"
    with pytest.raises(click.ClickException, match="OPERAÇÃO BLOQUEADA"):
        with app.app_context():
            ensure_safe_seed_environment()
            
    app.config["APP_ENV"] = "development"
    app.config["ALLOW_SEED"] = False
    with pytest.raises(click.ClickException, match="ALLOW_SEED"):
        with app.app_context():
            ensure_safe_seed_environment()

    app.config["ALLOW_SEED"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://user:pass@localhost/db"
    with pytest.raises(click.ClickException, match="SQLite"):
        with app.app_context():
            ensure_safe_seed_environment()