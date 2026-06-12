import click
from werkzeug.security import generate_password_hash
from tasty.ext.db import db
from tasty.models import Level, Role, User, BusinessType, City, Business, Address, Photo
from tasty.ext.cli.security import ensure_safe_seed_environment

def init_app(app):
    """Registra os comandos CLI personalizados relacionados à administração do banco de dados e operações de seed."""
    app.logger.info("Registrando comandos CLI personalizados...")

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

            cities_data = ["Vila Velha", "Vitória", "Serra", "Cariacica", "Guarapari"]
            cities = {}
            for c_name in cities_data:
                city = City(name=c_name, state="ES", country="Brasil", region="Sudeste")
                db.session.add(city)
                cities[c_name] = city
            db.session.flush()

            admins_info = [
                ("Brenno Gomes Breda", "brenno@admin.com", "111.111.111-01", "Max"),
                ("Daphne Rocha", "daphne@admin.com", "111.111.111-02", "Max"),
                ("Rafael", "rafael@admin.com", "111.111.111-04", "Premium"),
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

            businesses_data = [
                {
                    "owner_email": "owner_a@tasty.com", 
                    "trade": "Bonna Pizza", 
                    "cnpj": "00.000.000/0001-01", 
                    "types": ["Pizzaria"], 
                    "open": "18:00", 
                    "close": "23:59", 
                    "road": "Av. Antônio Gil Veloso", "num": 100, "district": "Praia da Costa", "zip": "29101-010", "city": "Vila Velha", "lat": -20.3297, "lng": -40.2818,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1513104890138-7c749659a591", "desc": "Pizza saindo do forno de pedra"},
                        {"url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5", "desc": "Ambiente aconchegante da pizzaria artesanal"},
                        {"url": "https://images.unsplash.com/photo-1590947132387-155cc02f3212", "desc": "Detalhe da nossa Pizza Suprema de Pepperoni"},
                        {"url": "https://images.unsplash.com/photo-1574085426831-9886e346f0a3", "desc": "Cardápio de vinhos e pizzas da casa"}
                    ]
                },
                {
                    "owner_email": "owner_a@tasty.com", 
                    "trade": "Burger Station", 
                    "cnpj": "00.000.000/0001-02", 
                    "types": ["Hamburgueria", "Vegano", "Saudável"], 
                    "open": "18:00", 
                    "close": "23:00", 
                    "road": "R. Jair de Andrade", "num": 500, "district": "Itapuã", "zip": "29101-700", "city": "Vila Velha", "lat": -20.3475, "lng": -40.2913,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd", "desc": "Smash burger artesanal com queijo derretido"},
                        {"url": "https://images.unsplash.com/photo-1550547660-d9450f859349", "desc": "Nosso salão rústico em estilo industrial"},
                        {"url": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90", "desc": "Opção fit: Burger artesanal no prato com salada"}
                    ]
                },
                {
                    "owner_email": "owner_b@tasty.com", 
                    "trade": "Sushi Lounge", 
                    "cnpj": "00.000.000/0001-03", 
                    "types": ["Comida Japonesa"], 
                    "open": "19:00", 
                    "close": "00:00", 
                    "road": "Rua da Lama", "num": 120, "district": "Jardim da Penha", "zip": "29060-230", "city": "Vitória", "lat": -20.2925, "lng": -40.2942,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c", "desc": "Combo premium de sushis variados e sashimis"},
                        {"url": "https://images.unsplash.com/photo-1611143669185-af224c5e3252", "desc": "Balcão do sushiman iluminado com neon"},
                        {"url": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56", "desc": "Detalhe de temaki de salmão fresco e maçaricado"},
                        {"url": "https://images.unsplash.com/photo-1583623025817-d180a2221d0a", "desc": "Entrada charmosa com luminárias orientais"},
                        {"url": "https://images.unsplash.com/photo-1633478062482-790e3b5dd810", "desc": "Cardápio de combinados tradicionais"}
                    ]
                },
                {
                    "owner_email": "owner_b@tasty.com", 
                    "trade": "Vegan Life", 
                    "cnpj": "00.000.000/0001-04", 
                    "types": ["Vegano", "Saudável"], 
                    "open": "11:30", 
                    "close": "23:00", 
                    "road": "Triângulo", "num": 10, "district": "Praia do Canto", "zip": "29055-000", "city": "Vitória", "lat": -20.3015, "lng": -40.2890,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd", "desc": "Salada bowl super colorida e 100% plant-based"},
                        {"url": "https://images.unsplash.com/photo-1540914124281-342587941389", "desc": "Espaço clean repleto de plantas naturais"}
                    ]
                },
                {
                    "owner_email": "owner_b@tasty.com", 
                    "trade": "Steakhouse Laranjeiras", 
                    "cnpj": "00.000.000/0001-05", 
                    "types": ["Churrascaria"], 
                    "open": "11:00", 
                    "close": "16:00", 
                    "road": "Av. Central", "num": 1500, "district": "Laranjeiras", "zip": "29165-130", "city": "Serra", "lat": -20.1985, "lng": -40.2605,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1544025162-d76694265947", "desc": "Costela premium assada lentamente na brasa"},
                        {"url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1", "desc": "Espeto corrido servido direto na mesa do cliente"},
                        {"url": "https://images.unsplash.com/photo-1600891964599-f61ba0e24092", "desc": "Salão amplo ideal para almoços em família"},
                        {"url": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b", "desc": "Seleção de cortes nobres cruas em exposição"}
                    ]
                },
                {
                    "owner_email": "owner_c@tasty.com", 
                    "trade": "Los Tacos", 
                    "cnpj": "00.000.000/0001-06", 
                    "types": ["Comida Mexicana"], 
                    "open": "08:00", "close": "20:00", 
                    "road": "Av. Expedito Garcia", "num": 50, "district": "Campo Grande", "zip": "29146-201", "city": "Cariacica", "lat": -20.3540, "lng": -40.3800,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47", "desc": "Tacos crocantes com guacamole e pico de gallo"},
                        {"url": "https://images.unsplash.com/photo-1624462966581-bc6d768cbce5", "desc": "Burrito gigante recheado cortado ao meio"},
                        {"url": "https://images.unsplash.com/photo-1514933651103-005eec06c04b", "desc": "Bar temático decorado com caveiras mexicanas"},
                        {"url": "https://images.unsplash.com/photo-1536184057357-a650177b412e", "desc": "Nossa famosa torre de Nachos com queijo"},
                        {"url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624", "desc": "Menu ilustrado de tequilas e margaritas"}
                    ]
                },
                {
                    "owner_email": "owner_c@tasty.com", 
                    "trade": "Moqueca Raiz", 
                    "cnpj": "00.000.000/0001-07", 
                    "types": ["Cozinha Brasileira", "Frutos do Mar"], 
                    "open": "11:00", "close": "17:00", 
                    "road": "Navegantes", "num": 800, "district": "Enseada", "zip": "29050-335", "city": "Vitória", "lat": -20.3150, "lng": -40.2905,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb", "desc": "Moqueca capixaba tradicional fervendo na panela de barro"},
                        {"url": "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0", "desc": "Bobó de camarão cremoso servido com arroz"},
                        {"url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4", "desc": "Vista para o mar a partir do salão rústico"},
                        {"url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0", "desc": "Mesa posta montada para o festival de frutos do mar"}
                    ]
                },
                {
                    "owner_email": "owner_c@tasty.com", 
                    "trade": "Habib Arab", 
                    "cnpj": "00.000.000/0001-08", 
                    "types": ["Comida Árabe"], 
                    "open": "10:00", "close": "22:00", 
                    "road": "Santa Leopoldina", "num": 300, "district": "Coqueiral", "zip": "29102-041", "city": "Vila Velha", "lat": -20.3590, "lng": -40.3010,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1608897013039-887f21d8c804", "desc": "Prato combinado com hummus, falafel e kafta"},
                        {"url": "https://images.unsplash.com/photo-1541518763669-27fef04b14ea", "desc": "Lounge árabe reservado com tapetes e almofadas"},
                        {"url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641", "desc": "Esfihas abertas folheadas saindo do forno"}
                    ]
                },
                {
                    "owner_email": "owner_c@tasty.com", 
                    "trade": "Gelato Manguinhos", 
                    "cnpj": "00.000.000/0001-09", 
                    "types": ["Sorveteria", "Cafeteria"], 
                    "open": "10:00", "close": "18:00", 
                    "road": "Atapuã", "num": 25, "district": "Manguinhos", "zip": "29173-025", "city": "Serra", "lat": -20.1850, "lng": -40.1890,
                    "photos": [
                        {"url": "https://images.unsplash.com/photo-1567206563064-6f60f40a2b57", "desc": "Gelatos artesanais cremosos expostos na vitrine"},
                      #  {"url": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a", "desc": "Taça monumental de sundae com morango"},
                        {"url": "https://images.unsplash.com/photo-1445116572660-236099ec97a0", "desc": "Nossa bancada charmosa com cafeteria expressa"},
                       # {"url": "https://images.unsplash.com/photo-1517433456452-f9633a875f6f", "desc": "Espaço externo de frente para a praia"},
                        {"url": "https://images.unsplash.com/photo-1559925393-8be0ec4767c8", "desc": "Quadro negro com as opções de sabores diários"}
                    ]
                }
            ]

            for b_data in businesses_data:
                b = Business(
                    corporate_name=f"{b_data['trade']} LTDA", trade_name=b_data['trade'], cnpj=b_data['cnpj'],
                    description="Venha conhecer os melhores sabores da Região Metropolitana.", opening_time=b_data['open'],
                    closing_time=b_data['close'], is_active=True
                )
                b.owners.append(owner_users[b_data["owner_email"]])
                for t_name in b_data["types"]:
                    b.business_types.append(b_types[t_name])
                
                for photo_info in b_data["photos"]:
                    b.photos.append(Photo(url=f"{photo_info['url']}?auto=format&fit=crop&w=800&q=80", description=photo_info['desc']))
                
                b.addresses.append(Address(road=b_data['road'], number=b_data['num'], district=b_data['district'], zipcode=b_data['zip'], latitude=b_data['lat'], longitude=b_data['lng'], city=cities[b_data['city']]))
                db.session.add(b)

            db.session.commit()
            
            click.echo("\n" + "="*70)
            click.echo("SEED DE DESENVOLVIMENTO MASSIVO CONCLUÍDO COM SUCESSO!")
            click.echo("Senha Universal Para Todas as Contas: 123456")
            click.echo("="*70 + "\n")
            
            click.echo("---   ADMINISTRADORES (Acessam: /admin/dashboard) ---")
            for name, email, _, lvl in admins_info:
                click.echo(f"  [Nível: {lvl.ljust(7)}] {email.ljust(25)} -> {name}")
                
            click.echo("\n---  CLIENTES (Acessam: /client/dashboard | /discovery/feed) ---")
            for name, email, _, road, _, dist, _, _, _, _ in clients_info:
                click.echo(f"  {email.ljust(25)} -> Radar: {road}, {dist}")
                
            click.echo("\n---  PARCEIROS COMERCIAIS (Acessam: /owner/dashboard | /my-business/list) ---")
            for name, email, _ in owners_info:
                click.echo(f"  {email.ljust(25)} -> {name}")
            click.echo("\n" + "="*70)
            
        except Exception as e:
            db.session.rollback()
            click.echo(f"ERRO CRÍTICO no seed: {e}")