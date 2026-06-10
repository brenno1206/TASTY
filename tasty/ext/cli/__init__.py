import os
import click
from flask import current_app
from werkzeug.security import generate_password_hash
from sqlalchemy import select
from tasty.ext.db import db
from tasty.models import Level, Role, User, BusinessType, City, Business, Address, Photo
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
        import tasty.models  # Garante reconhecimento
        
        click.echo(f"Diretório atual: {os.getcwd()}")
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
        click.echo("Banco de dados removido com sucesso.")


    # ======================================================
    # POPULANDO DADOS EM AMBIENTE DE DESENVOLVIMENTO
    # ======================================================

    @app.cli.command("seed-dev")
    def seed_dev():
        """Popula o banco com cenário completo (Apenas em Development)."""
        
        # Trava de segurança
        ensure_safe_seed_environment()

        is_dev = (
            app.config.get("ENV") == "development" or
            app.debug is True or
            current_app.config.get("FLASK_ENV") == "development"
        )

        if not is_dev:
            raise click.ClickException(
                "OPERAÇÃO BLOQUEADA: este Comando só pode ser executado em ambiente de desenvolvimento."
            )

        confirm = click.confirm("Isso irá popular o Banco com Dados de teste (Grande Vitória). Deseja continuar?")
        if not confirm:
            return
        
        try:
            click.echo("Iniciando seed de desenvolvimento...")
            default_pwd = generate_password_hash("123456")

            # ---------------------------------------------------------
            # 1. NÍVEIS
            # ---------------------------------------------------------
            levels_data = [
                ("Max", "Acesso total ao Sistema."),
                ("Premium", "Nível intermediário."),
                ("Basic", "Nível padrão.")
            ]
            levels = {}
            for name, desc in levels_data:
                lv = db.session.execute(select(Level).where(Level.name == name)).scalar_one_or_none()
                if not lv:
                    lv = Level(name=name, description=desc)
                    db.session.add(lv)
                levels[name] = lv
            db.session.flush()

            # ---------------------------------------------------------
            # 2. PAPEIS (ROLES)
            # ---------------------------------------------------------
            roles_data = {"admin": "Max", "owner": "Premium", "client": "Basic"}
            roles = {}
            for role_name, level_key in roles_data.items():
                r = db.session.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
                if not r:
                    r = Role(name=role_name, level=levels[level_key])
                    db.session.add(r)
                roles[role_name] = r
            db.session.flush()

            # ---------------------------------------------------------
            # 3. TIPOS DE NEGÓCIO (Com códigos HTML para Emojis)
            # ---------------------------------------------------------
            bt_data = [
                ("Pizzaria", "Pizzas artesanais e massas", "&#127829;"),
                ("Hamburgueria", "Burgers e lanches", "&#127816;"),
                ("Comida Japonesa", "Sushis e temakis", "&#127843;"),
                ("Cozinha Brasileira", "Comida caseira e feijoada", "&#127858;"),
                ("Cafeteria", "Cafés e doces", "&#9749;"),
                ("Vegano", "Opções 100% vegetais", "&#127807;"),
                ("Churrascaria", "Carnes nobres", "&#127830;")
            ]
            b_types = {}
            for name, desc, emoji in bt_data:
                bt = db.session.execute(select(BusinessType).where(BusinessType.name == name)).scalar_one_or_none()
                if not bt:
                    bt = BusinessType(name=name, description=desc, emoji=emoji)
                    db.session.add(bt)
                b_types[name] = bt
            db.session.flush()

            # ---------------------------------------------------------
            # 4. CIDADES (Grande Vitória - ES)
            # ---------------------------------------------------------
            cities_data = ["Vila Velha", "Vitória", "Serra", "Cariacica"]
            cities = {}
            for c_name in cities_data:
                city = db.session.execute(select(City).where(City.name == c_name, City.state == "ES")).scalar_one_or_none()
                if not city:
                    city = City(name=c_name, state="ES", country="Brasil", region="Sudeste")
                    db.session.add(city)
                cities[c_name] = city
            db.session.flush()

            # ---------------------------------------------------------
            # 5. USUÁRIOS
            # ---------------------------------------------------------
            # - 2 Administradores
            admins_info = [
                ("Brenno Gomes Breda", "brenno@admin.com", "111.111.111-11"),
                ("Daphne Rocha Amigo", "daphne@admin.com", "222.222.222-22")
            ]
            for name, email, cpf in admins_info:
                u = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
                if not u:
                    u = User(name=name, email=email, cpf=cpf, password=default_pwd, role=roles["admin"], is_active=True)
                    db.session.add(u)

            # - 3 Clientes
            clients_info = [
                ("Isabel Emília", "isabel@client.com", "333.333.333-33"),
                ("Maria Carla", "maria@client.com", "444.444.444-44"),
                ("Rhuan Santos", "rhuan@client.com", "555.555.555-55")
            ]
            for name, email, cpf in clients_info:
                u = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
                if not u:
                    u = User(name=name, email=email, cpf=cpf, password=default_pwd, role=roles["client"], is_active=True)
                    db.session.add(u)

            # - 1 Dono de Restaurante (Owner genérico para atrelar os 10 negócios)
            owner = db.session.execute(select(User).where(User.email == "owner@tasty.com")).scalar_one_or_none()
            if not owner:
                owner = User(name="Grupo Gastronômico ES", email="owner@tasty.com", cpf="999.999.999-99", password=default_pwd, role=roles["owner"], is_active=True)
                db.session.add(owner)
            
            db.session.flush()

            # ---------------------------------------------------------
            # 6. RESTAURANTES (10 com CEPs Reais da Grande Vitória)
            # ---------------------------------------------------------
            businesses_data = [
                {
                    "trade": "Bonna Pizza Praia da Costa", "cnpj": "00.000.000/0001-01", "type": "Pizzaria",
                    "open": "18:00", "close": "23:59", "img": "https://images.unsplash.com/photo-1513104890138-7c749659a591",
                    "road": "Av. Antônio Gil Veloso", "num": 100, "district": "Praia da Costa", "zip": "29101-010", "city": "Vila Velha", "lat": -20.3297, "lng": -40.2818
                },
                {
                    "trade": "Burger Station Itapuã", "cnpj": "00.000.000/0001-02", "type": "Hamburgueria",
                    "open": "18:00", "close": "23:00", "img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd",
                    "road": "R. Jair de Andrade", "num": 500, "district": "Itapuã", "zip": "29101-700", "city": "Vila Velha", "lat": -20.3475, "lng": -40.2913
                },
                {
                    "trade": "Sushi Vitória Lounge", "cnpj": "00.000.000/0001-03", "type": "Comida Japonesa",
                    "open": "19:00", "close": "00:00", "img": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c",
                    "road": "Rua da Lama", "num": 120, "district": "Jardim da Penha", "zip": "29060-230", "city": "Vitória", "lat": -20.2925, "lng": -40.2942
                },
                {
                    "trade": "Cantina Italiana Triângulo", "cnpj": "00.000.000/0001-04", "type": "Pizzaria",
                    "open": "11:30", "close": "23:00", "img": "https://images.unsplash.com/photo-1551183053-bf91a1d81141",
                    "road": "Triângulo das Bermudas", "num": 10, "district": "Praia do Canto", "zip": "29055-000", "city": "Vitória", "lat": -20.3015, "lng": -40.2890
                },
                {
                    "trade": "Steakhouse Laranjeiras", "cnpj": "00.000.000/0001-05", "type": "Churrascaria",
                    "open": "11:00", "close": "16:00", "img": "https://images.unsplash.com/photo-1594046243098-0fceea9d451e",
                    "road": "Av. Central", "num": 1500, "district": "Parque Residencial Laranjeiras", "zip": "29165-130", "city": "Serra", "lat": -20.1985, "lng": -40.2605
                },
                {
                    "trade": "Lanchonete Campo Grande", "cnpj": "00.000.000/0001-06", "type": "Hamburgueria",
                    "open": "08:00", "close": "20:00", "img": "https://images.unsplash.com/photo-1626079218683-1b91bc62b712",
                    "road": "Av. Expedito Garcia", "num": 50, "district": "Campo Grande", "zip": "29146-201", "city": "Cariacica", "lat": -20.3540, "lng": -40.3800
                },
                {
                    "trade": "Moqueca Capixaba Raiz", "cnpj": "00.000.000/0001-07", "type": "Cozinha Brasileira",
                    "open": "11:00", "close": "17:00", "img": "https://images.unsplash.com/photo-1621852004158-f3bc188ace2d",
                    "road": "Av. Nossa Sra. dos Navegantes", "num": 800, "district": "Enseada do Suá", "zip": "29050-335", "city": "Vitória", "lat": -20.3150, "lng": -40.2905
                },
                {
                    "trade": "Vegan Life Coqueiral", "cnpj": "00.000.000/0001-08", "type": "Vegano",
                    "open": "10:00", "close": "22:00", "img": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
                    "road": "Av. Santa Leopoldina", "num": 300, "district": "Coqueiral de Itaparica", "zip": "29102-041", "city": "Vila Velha", "lat": -20.3590, "lng": -40.3010
                },
                {
                    "trade": "Mar Aberto Manguinhos", "cnpj": "00.000.000/0001-09", "type": "Cozinha Brasileira",
                    "open": "10:00", "close": "18:00", "img": "https://images.unsplash.com/photo-1615486171448-4fdca91e1d04",
                    "road": "Av. Atapuã", "num": 25, "district": "Manguinhos", "zip": "29173-025", "city": "Serra", "lat": -20.1850, "lng": -40.1890
                },
                {
                    "trade": "Café do Centro", "cnpj": "00.000.000/0001-10", "type": "Cafeteria",
                    "open": "07:00", "close": "19:00", "img": "https://images.unsplash.com/photo-1554118811-1e0d58224f24",
                    "road": "Rua Jerônimo Monteiro", "num": 850, "district": "Centro", "zip": "29100-021", "city": "Vila Velha", "lat": -20.3305, "lng": -40.2940
                }
            ]

            for b_data in businesses_data:
                b = db.session.execute(select(Business).where(Business.cnpj == b_data["cnpj"])).scalar_one_or_none()
                if not b:
                    b = Business(
                        corporate_name=f"{b_data['trade']} LTDA",
                        trade_name=b_data['trade'],
                        cnpj=b_data['cnpj'],
                        description="Venha conhecer os melhores sabores da Grande Vitória preparados com carinho e tradição.",
                        opening_time=b_data['open'],
                        closing_time=b_data['close'],
                        is_active=True
                    )
                    
                    b.owners.append(owner)
                    b.business_types.append(b_types[b_data["type"]])
                    
                    # Foto
                    b.photos.append(Photo(url=f"{b_data['img']}?auto=format&fit=crop&w=800&q=80", description="Foto de capa"))
                    
                    # Endereço
                    b.addresses.append(Address(
                        road=b_data['road'],
                        number=b_data['num'],
                        district=b_data['district'],
                        zipcode=b_data['zip'],
                        latitude=b_data['lat'],
                        longitude=b_data['lng'],
                        city=cities[b_data['city']]
                    ))

                    db.session.add(b)

            db.session.commit()
            click.echo("Seed de desenvolvimento concluído com sucesso!")
            click.echo("Acesse com: brenno@admin.com, isabel@client.com, owner@tasty.com (Senha: 123456)")
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO CRÍTICO no seed: {e}")