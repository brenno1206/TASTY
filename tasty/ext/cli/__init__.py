import os
import click
from flask import current_app
from tasty.ext.db import db
from tasty.models import *
from tasty.ext.cli.security import ensure_safe_seed_environment

# ==========================================================
# INIT APP
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
        
        click.echo(f"Diretório atual: {os.getcwd()}")
        click.echo(f"Utilizando banco de dados: {current_app.config['SQLALCHEMY_DATABASE_URI']}")
        click.echo(f"Instance path: {current_app.instance_path}")
        click.echo(f"DB URI: {current_app.config['SQLALCHEMY_DATABASE_URI']}")
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
    # CREATE LEVELS
    # ======================================================

    @app.cli.command("create-levels")
    def create_levels():
        """Cria os Levels e as permissões básicas de sistema."""

        try:
            click.echo("Configurando Levels do sistema...")
            max = Level(name="Max", description="Acesso total ao sistema.")
            premium = Level(name="Premium", description="Acesso Intermediário ao sistema.")
            basic = Level(name="Basic", description="Acesso básico ao sistema")
            db.session.add(max)
            db.session.add(premium)
            db.session.add(basic)
            db.session.flush()
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO: {e}")
            
        # Aqui você chamará o modelo de usuário e salvará o root
        # Ex: from tasty.models.user import User ...
        click.echo("Função create-root executada.")

    # ======================================================
    # CREATE ROLES
    # ======================================================
    
    @app.cli.command("create-roots")
    def create_levels():
        """Cria os Roles e as permissões básicas de sistema."""

        try:
            click.echo("Configurando Roles do sistema...")
            max = Level(name="Max", description="Acesso total ao sistema.")
            premium = Level(name="Premium", description="Acesso Intermediário ao sistema.")
            basic = Level(name="Basic", description="Acesso básico ao sistema")
            db.session.add(max)
            db.session.add(premium)
            db.session.add(basic)
            db.session.flush()
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO: {e}")
            
        # Aqui você chamará o modelo de usuário e salvará o root
        # Ex: from tasty.models.user import User ...
        click.echo("Função create-root executada.")
    
    # ======================================================
    # CREATE ROOT
    # ======================================================
    @app.cli.command("create-root")
    def create_root():
        """Cria o usuário Root e as permissões básicas de sistema."""

        try:
            click.echo("Configurando acesso Root do sistema...")

            level_max = Level.query.filter_by(name="Max").first()
            if not level_root: 
                level_root = Level(name="Max", description="Acesso total ao Sistema.")
                db.session.add(level_root)
                click.echo("- Nível 'Max' criado.")
            
            role_root = Role.query.filter_by(name="Root").first()
            if not role_root:
                role_root = Role(name="Root")
                db.session.add(role_root)
                click.echo("- Papel 'Root' criado.")

            db.session.flush()

        # PAREI AQUI !!!!
                
        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO: {e}")
            
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