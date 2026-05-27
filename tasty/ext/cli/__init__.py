import os
import click
from flask import current_app
from tasty.ext.db import db
from tasty.ext.cli.security import ensure_safe_seed_environment

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
        # Apenas importar os models aqui garante que o SQLAlchemy os reconheça
        import tasty.models  
        
        print(f"Diretório atual: {os.getcwd()}")
        print(f"Utilizando banco de dados: {current_app.config['SQLALCHEMY_DATABASE_URI']}")
        
        db.create_all()
        click.echo("Banco de dados materializado com sucesso!")

    # ======================================================
    # DROP DB
    # ======================================================
    @app.cli.command("drop-db")
    @click.confirmation_option(prompt="Tem certeza que deseja apagar TUDO? Esta ação não pode ser desfeita.")
    def drop_db():
        """Remove todas as tabelas do banco."""
        db.drop_all()
        click.echo("Banco de dados removido.")
    
    # ======================================================
    # CREATE ROOT
    # ======================================================
    @app.cli.command("create-root")
    def create_root():
        """Cria o usuário Root e as permissões básicas de sistema."""
        # Aqui você chamará o modelo de usuário e salvará o root
        # Ex: from tasty.models.user import User ...
        click.echo("Função create-root executada.")

    # ======================================================
    # POPULANDO DADOS EM AMBIENTE DE DESENVOLVIMENTO
    # ======================================================
    @app.cli.command("seed-dev")
    def seed_dev():
        """Popula o banco com cenário completo (Apenas em Development)."""
        
        # 1. Trava de segurança imediata
        ensure_safe_seed_environment()
        
        # 2. Se a verificação passar, continua com o processo de popular o banco.
        click.echo("Verificação de segurança aprovada. Iniciando seed de desenvolvimento...")
        
        # ... aqui vai o código para popular os dados ...
        
        click.echo("Seed de desenvolvimento concluído!")