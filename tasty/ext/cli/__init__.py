import os
import click
from flask import current_app
from werkzeug.security import generate_password_hash
from sqlalchemy import select
from tasty.ext.db import db
from tasty.models import Level, Role, User, BusinessType, City, Business, Address, Photo
from tasty.ext.cli.security import ensure_safe_seed_environment

def init_app(app):

    @app.cli.command("create-db")
    def create_db():
        """Cria todas as tabelas do BD"""
        import tasty.models
        db.create_all()
        click.echo("Banco de dados materializado com sucesso!")

    @app.cli.command("drop-db")
    @click.confirmation_option(prompt="Tem certeza que deseja apagar TUDO?")
    def drop_db():
        """Remove todas as tabelas do banco."""
        db.drop_all()
        click.echo("Banco de dados removido com sucesso.")

    @app.cli.command("seed-dev")
    def seed_dev():
        """Popula o banco com cenário massivo estruturado por níveis."""
        ensure_safe_seed_environment()

        if not (app.config.get("ENV") == "development" or app.debug is True):
            raise click.ClickException("OPERAÇÃO BLOQUEADA: Apenas em dev.")

        if not click.confirm("Deseja popular o banco de dados?"):
            return
        
        try:
            click.echo("Iniciando seed de desenvolvimento...")
            default_pwd = generate_password_hash("123456")

            # 1. NÍVEIS
            levels_data = [
                ("Max", "Acesso total (Root)."),
                ("Premium", "Acesso avançado."),
                ("Basic", "Acesso padrão."),
                ("Support", "Acesso restrito.")
            ]
            levels = {}
            for name, desc in levels_data:
                lv = Level(name=name, description=desc)
                db.session.add(lv)
                levels[name] = lv
            db.session.flush()

            # 2. PAPEIS (ROLES) - Todos com name="admin" usando o modelo flexível!
            roles_admin = {
                "Max": Role(name="admin", level=levels["Max"]),
                "Premium": Role(name="admin", level=levels["Premium"]),
                "Basic": Role(name="admin", level=levels["Basic"]),
                "Support": Role(name="admin", level=levels["Support"])
            }
            for r in roles_admin.values():
                db.session.add(r)

            role_owner = Role(name="owner", level=levels["Premium"])
            role_client = Role(name="client", level=levels["Basic"])
            db.session.add_all([role_owner, role_client])
            db.session.flush()

            # 3. TIPOS DE NEGÓCIO
            bt_data = [
                ("Pizzaria", "Pizzas artesanais", "&#127829;"),
                ("Hamburgueria", "Burgers e lanches", "&#127816;"),
                ("Comida Japonesa", "Sushis e temakis", "&#127843;"),
                ("Cozinha Brasileira", "Comida caseira", "&#127858;"),
                ("Cafeteria", "Cafés e doces", "&#9749;"),
                ("Vegano", "Opções vegetais", "&#127807;"),
                ("Churrascaria", "Carnes nobres", "&#127830;"),
                ("Comida Mexicana", "Tacos e burritos", "&#127790;"),
                ("Frutos do Mar", "Moquecas e peixes", "&#129422;"),
                ("Comida Árabe", "Kibes e esfihas", "&#129366;"),
                ("Sorveteria", "Sobremesas geladas", "&#127846;"),
                ("Saudável", "Saladas e bowls", "&#129367;")
            ]
            b_types = {}
            for name, desc, emoji in bt_data:
                bt = BusinessType(name=name, description=desc, emoji=emoji)
                db.session.add(bt)
                b_types[name] = bt
            db.session.flush()

            # 4. CIDADES
            cities_data = ["Vila Velha", "Vitória", "Serra", "Cariacica", "Guarapari"]
            cities = {}
            for c_name in cities_data:
                city = City(name=c_name, state="ES", country="Brasil", region="Sudeste")
                db.session.add(city)
                cities[c_name] = city
            db.session.flush()

            # 5. USUÁRIOS: 10 Admins
            admins_info = [
                ("Brenno Gomes Breda", "brenno@admin.com", "111.111.111-01", "Max"),
                ("Daphne Rocha", "daphne@admin.com", "111.111.111-02", "Max"),
                ("Prof. Abrantes Araújo", "abrantes@admin.com", "111.111.111-03", "Max"),
                ("Jean-Remi", "jeanremi@admin.com", "111.111.111-04", "Premium"),
                ("Admin Suporte 1", "suporte1@admin.com", "111.111.111-05", "Support"),
                ("Admin Suporte 2", "suporte2@admin.com", "111.111.111-06", "Support"),
                ("Admin Qualidade 1", "qa1@admin.com", "111.111.111-07", "Basic"),
                ("Admin Qualidade 2", "qa2@admin.com", "111.111.111-08", "Basic"),
                ("Gerente Operacional", "gerente@admin.com", "111.111.111-09", "Premium"),
                ("Auditor Geral", "auditor@admin.com", "111.111.111-10", "Max")
            ]
            for name, email, cpf, lvl in admins_info:
                u = User(name=name, email=email, cpf=cpf, password=default_pwd, role=roles_admin[lvl], is_active=True)
                db.session.add(u)

            # 6. USUÁRIOS: 10 Clientes
            clients_info = [
                ("Isabel Emília Sterim Saade", "isabel@client.com", "222.222.222-01", "Rua Castelo Branco", 101, "Praia da Costa", "29101-000", -20.3297, -40.2818, "Vila Velha"),
                ("Maria Carla dos Santos Bellote", "maria@client.com", "222.222.222-02", "Av. Dante Michelini", 202, "Enseada do Suá", "29050-000", -20.3150, -40.2905, "Vitória"),
                ("Rhuan Santos Wolfgramm", "rhuan@client.com", "222.222.222-03", "Av. Central", 303, "Laranjeiras", "29165-000", -20.1985, -40.2605, "Serra"),
                ("Lucas Ferreira", "lucas@client.com", "222.222.222-04", "BR-262", 404, "Jardim América", "29140-000", -20.3540, -40.3800, "Cariacica"),
                ("Camila Neves", "camila@client.com", "222.222.222-05", "Av. Beira Mar", 505, "Centro", "29200-000", -20.6660, -40.4990, "Guarapari"),
                ("Thiago Barbosa", "thiago@client.com", "222.222.222-06", "Rua Ceará", 606, "Itapuã", "29101-700", -20.3475, -40.2913, "Vila Velha"),
                ("Beatriz Lima", "beatriz@client.com", "222.222.222-07", "Rua da Lama", 707, "Jardim da Penha", "29060-230", -20.2925, -40.2942, "Vitória"),
                ("Gustavo Almeida", "gustavo@client.com", "222.222.222-08", "Av. Eudes Scherrer", 808, "Laranjeiras", "29165-130", -20.1900, -40.2600, "Serra"),
                ("Fernanda Costa", "fernanda@client.com", "222.222.222-09", "Rodovia do Sol", 909, "Coqueiral", "29102-041", -20.3590, -40.3010, "Vila Velha"),
                ("Ricardo Mendes", "ricardo@client.com", "222.222.222-10", "Av. Rio Branco", 100, "Praia do Canto", "29055-000", -20.3015, -40.2890, "Vitória")
            ]
            for name, email, cpf, road, num, district, zipc, lat, lng, city_name in clients_info:
                u = User(name=name, email=email, cpf=cpf, password=default_pwd, role=role_client, is_active=True)
                u.addresses.append(Address(road=road, number=num, district=district, zipcode=zipc, latitude=lat, longitude=lng, city=cities[city_name]))
                u.preferences.extend([b_types["Pizzaria"], b_types["Hamburgueria"], b_types["Comida Japonesa"]])
                db.session.add(u)

            # 7. USUÁRIOS: 3 Owners
            owners_info = [
                ("Grupo A (2 Restaurantes)", "owner_a@tasty.com", "333.333.333-01"),
                ("Grupo B (3 Restaurantes)", "owner_b@tasty.com", "333.333.333-02"),
                ("Grupo C (4 Restaurantes)", "owner_c@tasty.com", "333.333.333-03")
            ]
            owner_users = {}
            for name, email, cpf in owners_info:
                u = User(name=name, email=email, cpf=cpf, password=default_pwd, role=role_owner, is_active=True)
                db.session.add(u)
                owner_users[email] = u
            
            db.session.flush()

            # 8. RESTAURANTES
            photo_pool = [
                "https://images.unsplash.com/photo-1513104890138-7c749659a591",
                "https://images.unsplash.com/photo-1568901346375-23c9450c58cd",
                "https://images.unsplash.com/photo-1579871494447-9811cf80d66c",
                "https://images.unsplash.com/photo-1551183053-bf91a1d81141",
                "https://images.unsplash.com/photo-1594046243098-0fceea9d451e"
            ]

            businesses_data = [
                {"owner_email": "owner_a@tasty.com", "trade": "Bonna Pizza", "cnpj": "00.000.000/0001-01", "types": ["Pizzaria"], "open": "18:00", "close": "23:59", "num_photos": 4, "road": "Av. Antônio Gil Veloso", "num": 100, "district": "Praia da Costa", "zip": "29101-010", "city": "Vila Velha", "lat": -20.3297, "lng": -40.2818},
                {"owner_email": "owner_a@tasty.com", "trade": "Burger Station", "cnpj": "00.000.000/0001-02", "types": ["Hamburgueria"], "open": "18:00", "close": "23:00", "num_photos": 3, "road": "R. Jair de Andrade", "num": 500, "district": "Itapuã", "zip": "29101-700", "city": "Vila Velha", "lat": -20.3475, "lng": -40.2913},
                {"owner_email": "owner_b@tasty.com", "trade": "Sushi Lounge", "cnpj": "00.000.000/0001-03", "types": ["Comida Japonesa"], "open": "19:00", "close": "00:00", "num_photos": 5, "road": "Rua da Lama", "num": 120, "district": "Jardim da Penha", "zip": "29060-230", "city": "Vitória", "lat": -20.2925, "lng": -40.2942},
                {"owner_email": "owner_b@tasty.com", "trade": "Vegan Life", "cnpj": "00.000.000/0001-04", "types": ["Vegano"], "open": "11:30", "close": "23:00", "num_photos": 2, "road": "Triângulo", "num": 10, "district": "Praia do Canto", "zip": "29055-000", "city": "Vitória", "lat": -20.3015, "lng": -40.2890},
                {"owner_email": "owner_b@tasty.com", "trade": "Steakhouse Laranjeiras", "cnpj": "00.000.000/0001-05", "types": ["Churrascaria"], "open": "11:00", "close": "16:00", "num_photos": 4, "road": "Av. Central", "num": 1500, "district": "Laranjeiras", "zip": "29165-130", "city": "Serra", "lat": -20.1985, "lng": -40.2605},
                {"owner_email": "owner_c@tasty.com", "trade": "Los Tacos", "cnpj": "00.000.000/0001-06", "types": ["Comida Mexicana"], "open": "08:00", "close": "20:00", "num_photos": 5, "road": "Av. Expedito Garcia", "num": 50, "district": "Campo Grande", "zip": "29146-201", "city": "Cariacica", "lat": -20.3540, "lng": -40.3800},
                {"owner_email": "owner_c@tasty.com", "trade": "Moqueca Raiz", "cnpj": "00.000.000/0001-07", "types": ["Cozinha Brasileira"], "open": "11:00", "close": "17:00", "num_photos": 4, "road": "Navegantes", "num": 800, "district": "Enseada", "zip": "29050-335", "city": "Vitória", "lat": -20.3150, "lng": -40.2905},
                {"owner_email": "owner_c@tasty.com", "trade": "Habib Arab", "cnpj": "00.000.000/0001-08", "types": ["Comida Árabe"], "open": "10:00", "close": "22:00", "num_photos": 3, "road": "Santa Leopoldina", "num": 300, "district": "Coqueiral", "zip": "29102-041", "city": "Vila Velha", "lat": -20.3590, "lng": -40.3010},
                {"owner_email": "owner_c@tasty.com", "trade": "Gelato Manguinhos", "cnpj": "00.000.000/0001-09", "types": ["Sorveteria"], "open": "10:00", "close": "18:00", "num_photos": 5, "road": "Atapuã", "num": 25, "district": "Manguinhos", "zip": "29173-025", "city": "Serra", "lat": -20.1850, "lng": -40.1890}
            ]

            photo_idx = 0
            for b_data in businesses_data:
                b = Business(
                    corporate_name=f"{b_data['trade']} LTDA", trade_name=b_data['trade'], cnpj=b_data['cnpj'],
                    description="Venha conhecer os melhores sabores da Região Metropolitana.", opening_time=b_data['open'],
                    closing_time=b_data['close'], is_active=True
                )
                b.owners.append(owner_users[b_data["owner_email"]])
                for t_name in b_data["types"]:
                    b.business_types.append(b_types[t_name])
                
                for _ in range(b_data["num_photos"]):
                    img_url = photo_pool[photo_idx % len(photo_pool)]
                    b.photos.append(Photo(url=f"{img_url}?auto=format&fit=crop&w=800&q=80", description="Foto"))
                    photo_idx += 1
                
                b.addresses.append(Address(road=b_data['road'], number=b_data['num'], district=b_data['district'], zipcode=b_data['zip'], latitude=b_data['lat'], longitude=b_data['lng'], city=cities[b_data['city']]))
                db.session.add(b)

            db.session.commit()
            
            click.echo("\n" + "="*70)
            click.echo("✅ SEED DE DESENVOLVIMENTO MASSIVO CONCLUÍDO COM SUCESSO!")
            click.echo("🔑 Senha Universal Para Todas as Contas: 123456")
            click.echo("="*70 + "\n")
            
            click.echo("--- 🛡️  ADMINISTRADORES (Acessam: /admin/dashboard) ---")
            for name, email, _, lvl in admins_info:
                click.echo(f"  [Nível: {lvl.ljust(7)}] {email.ljust(25)} -> {name}")
                
            click.echo("\n--- 🍔 CLIENTES (Acessam: /client/dashboard | /discovery/feed) ---")
            for name, email, _, road, _, dist, _, _, _, _ in clients_info:
                click.echo(f"  {email.ljust(25)} -> Radar: {road}, {dist}")
                
            click.echo("\n--- 🏪 PARCEIROS COMERCIAIS (Acessam: /owner/dashboard | /my-business/list) ---")
            for name, email, _ in owners_info:
                click.echo(f"  {email.ljust(25)} -> {name}")
            click.echo("\n" + "="*70)
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO CRÍTICO no seed: {e}")