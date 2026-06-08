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
            if not level_max: 
                level_max = Level(name="Max", description="Acesso total ao Sistema.")
                db.session.add(level_max)
                click.echo("- Nível 'Max' criado.")
            
            role_root = Role.query.filter_by(name="Root").first()
            if not role_root:
                role_root = Role(name="Root")
                db.session.add(role_root)
                click.echo("- Papel 'Root' criado.")

            db.session.flush() # Sincroniza IDs antes de criar o usuario e o vinculo

            user = User.query.filter_by(email="root@dev.com").first()
            if not user:
                user = User(
                    name="Daphne Rocha Amigo",
                    email="root@dev.com",
                    cpf="123.456.789-00",
                    is_active=True
                )
                db.session.add(user)
                click.echo(f"- Usuário {user.name} criado.")
            else:
                click.echo(f"- Usuário {user.name} já existe.")

            db.session.flush()

            if not user.Role_id:
                user.Role_id = role_root.id
                db.session.add(user)

                click.echo("- Permissões de Root vinculadas com sucesso.")
            else:
                click.echo("- O Usuário já possui permissões de Root.")

            db.session.commit()
            click.echo("Operação finalizada com sucesso.")
                
        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO ao Criar Root: {e}")
            raise click.ClickException(str(e))
            
        click.echo("Função create-root executada.")


    # ======================================================
    # POPULANDO DADOS EM AMBIENTE DE DESENVOLVIMENTO
    # ======================================================

    @app.cli.command("seed-dev")
    def seed_dev():
        """Popula o banco com cenário completo (Apenas em Development)."""
        
        # 1. Trava de segurança imediata
        ensure_safe_seed_environment()

        is_dev = (
            app.config.get("ENV") == "development" or
            app.debug is True or
            current_app.config.get("FLASK_ENV") == "development"
        )

        if not is_dev:
            raise click.ClickException(
                "OPERAÇÃO BLOQUEADA: este Comando só pode ser executado em ambiente de desenvolvimento"
            )

        confirm = click.confirm("Isso irá popular o Banco com Dados de teste. Deseja continuar?")

        if not confirm:
            return
        
        # 2. Se a verificação passar, continua com o processo de popular o banco.
        try:
            click.echo("Verificação de segurança aprovada. Iniciando seed de desenvolvimento...")

            # 1. Níveis
            levels_data = [
                ("Max", "Acesso total ao Sistema: recomendado apenas para root."),
                ("Premium", "Nível intermediário de acesso."),
                ("Basic", "Nível padrão de acesso.")
            ]

            levels = {}
            for name, desc in levels_data:
                lv = Level.query.filter_by(name=name).first()

                if not lv:
                    lv = Level(name=name, description=desc)
                    db.session.add(lv)

                levels[name] = lv

            # 2. Papeis
            role_names = ["Root", "Sustainer", "Administrador", "Cliente"]

            role_data = {
                "Root": "Max", 
                "Sustainer": "Premium", 
                "Administrador": "Premium", 
                "Cliente": "Basic"
            }

            roles = {}

            for role_name, levels_data in role_data.items():
                r = Role.query.filter_by(name=role_name).first()

                if not r:
                    r = Role(
                        name=role_name,
                        level=levels[levels_data]
                    )

                    db.session.add(r)

                roles[role_name] = r

            # 3. Tipos de Negócio
            bt_data = [
                ("Pizzaria", "Estabelecimentos especializados em pizzas e massas."),
                ("Hamburgueria", "Estabelecimentos especializados em hamburgueres artesanais e lanches rápidos."),
                ("Restaurante", "Alimentação variada com serviço de pratos executivos."),
                ("Comida Japonesa", "Especializados em sushi, temakis e outros pratos da culinária japonesa."),
                ("Bar", "Estabelecimento focado em bebidas, petiscos e ambiente para socialização."),
                ("Comida Vegana", "Alimentação baseada em ingredientes vegetais, com opções saudáveis e sustentáveis.")
            ]
            b_types = {}

            for name, desc in bt_data:
                bt = BusinessType.query.filter_by(name=name).first()

                if not bt:
                    bt = BusinessType(name=name, description=desc)
                    db.session.add(bt)

                b_types[name] = bt

            # 4. Localização (Cidade)
            city = City.query.filter_by(name="Vila Velha", state="ES").first()

            if not city:
                city = City(name="Vila Velha", state="ES", country="Brasil", region="Sudeste")
                db.session.add(city)

            db.session.flush()

            # 5. Usuários (Root e Proprietário)
            root_user = User.query.filter_by(email="root@dev.com").first()

            if not root_user:
                root_user = User(
                    name="Daphne Rocha Amigo",
                    email="root@dev.com",
                    cpf="123.456.789-00",
                    is_active=True
                )
                db.session.add(root_user)

            brenno = User.query.filter_by(email="reno@email.com").first()

            if not brenno:
                brenno = User(
                    name="Brenno Reno",
                    email="reno@email.com",
                    cpf="111.111.111-11",
                    is_active=True
                )
                db.session.add(brenno)
            
            db.session.flush()

            # 6. Empresa e seu Endereço
            buz = Business.query.filter_by(cnpj="12.345.678/0001-99").first()

            if not buz:
                buz = Business(
                    owners=[brenno],
                    trade_name="Bonna Pizza Express",
                    corporate_name="Brenno Pizzas LTDA",
                    cnpj="12.345.678/0001-99",
                    business_type=b_types["Pizzaria"]
                )

                db.session.add(buz)
                db.session.flush()

                addr = Address(
                    road="Av. Beira Mar",
                    number=400,
                    district="Itapuã",
                    zipcode="29101-000",
                    city=city,
                    business=buz
                )

                db.session.add(addr)

            # 7. Associações de Acesso (Role | User)
            root_user.role = roles["Root"]
            brenno.role = roles["Administrador"]

            db.session.commit()


            # Criando Perfis !!! PAREI AQUI !!!

            vitoria = City.query.filter_by(name="Vitória", state="ES")

        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO no seed: {e}")
        
        # ... aqui vai o código para popular os dados ...
        
        click.echo("Seed de desenvolvimento concluído!")