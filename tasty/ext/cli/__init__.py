import click
from flask import current_app
from tasty.ext.db import db
from tasty.models import *
from tasty.ext.cli.security import ensure_safe_seed_environment
import os

# ==========================================================
# INIT
# ========================================================== 

def init_app(app):

    # ======================================================
    # CREATE DB
    # ======================================================

    @app.cli.command("create-db")
    def create_db():
        """Cria todas as tabelas do BD"""
        import tasty.models
        print("Estou aqui:", os.getcwd())
        print("Novo print:", app.config["SQLALCHEMY_DATABASE_URI"])
        db.create_all()
        click.echo("Banco de dados materializado com sucesso!")

    # ======================================================
    # DROP DB
    # ======================================================
    @app.cli.command("drop-db")
    @click.confirmation_option(prompt="Tem certeza que deseja apagar TUDO?")
    def drop_db():
        """
        Remove todas as tabelas do banco (Cuidado!).
        """
        db.drop_all()
        click.echo("Banco de dados removido.")
    
    # ======================================================
    # CREATE ROOT
    # ======================================================
    @app.cli.command("create-root")
    def create_root():
        """
        Cria o usuario Root e as permissoes basicas de sistema (Seguro para Producao).
        """
        pass

    # ======================================================
    # POPULANDO DADOS EM AMBIENTE DE DESENVOLVIMENTO
    # ======================================================
    @app.cli.command("seed-dev")
    def seed_dev():
        """
        Popula o banco com cenario completo (Apenas em Development).
        """
        pass