import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from tasty.ext.db import db
from tasty.models import Role, Level, BusinessType, Business, User, City, Address
import tasty.services.user_service as user_service
import tasty.services.business_type_service as bt_service
import tasty.services.location_service as location_service
import tasty.services.business_service as b_service
import tasty.services.analytics_service as analytics_service
import tasty.services.swipe_service as swipe_service


# ---- Testes de User Service ----

def test_user_service_crud_real(app):
    """Testa o fluxo completo de usuário direto no Banco de Dados em Memória."""
    lvl = Level(name="Basic", description="Basic Lvl")
    role = Role(name="client", level=lvl)
    role_admin = Role(name="admin", level=lvl)
    db.session.add_all([lvl, role, role_admin])
    db.session.commit()

    data = {
        "name": "Usuário Real",
        "email": "real@teste.com",
        "password": "senha",
        "cpf": "123.456.789-00",
        "phone": "27999999999"
    }
    success, msg, code = user_service.create_client(data)
    assert success is True

    success_dup, _, _ = user_service.create_client(data)
    assert success_dup is False

    success, msg, code, user = user_service.login("real@teste.com", "senha")
    assert success is True

    s_login, _, _, _ = user_service.login("inexistente@teste.com", "senha")
    assert s_login is False
    s_login2, _, _, _ = user_service.login("real@teste.com", "senha_errada")
    assert s_login2 is False

    success, msg, code = user_service.change_user_password(user.id, "senha", "nova_senha")
    assert success is True

    user_service.create_admin({"name": "Adm", "email": "adm@t.com", "password": "1"})
    assert len(user_service.get_all_admins()) > 0
    assert len(user_service.get_admins_by_level("Basic")) > 0

    success, msg, code = user_service.update_client(user.id, {"name": "Usuário Atualizado"})
    assert success is True

    success, msg, code = user_service.delete_client(user.id)
    assert success is True
    
    user_db = db.session.execute(select(User).where(User.id == user.id)).scalar_one()
    assert user_db.is_active is False

def test_user_service_edge_cases(app):
    """Cobre as validações de dados incompletos ou ausentes dos serviços de usuário."""
    success, _, _ = user_service.create_client({})
    assert success is False
    
    success, _, _ = user_service.update_client(9999, {"name": "Fantasma"})
    assert success is False
    
    success, _, _ = user_service.delete_admin(9999)
    assert success is False

def test_user_service_edge_cases_and_exceptions(app, mocker):
    """Cobre as validações de dados inválidos e simula erros de banco no User Service."""
    success, _, code = user_service.create_client(None)
    assert success is False and code == 400
    
    success, _, code = user_service.update_client(9999, None)
    assert success is False and code == 404
    
    mocker.patch("tasty.ext.db.db.session.commit", side_effect=SQLAlchemyError("DB Error"))
    success, _, code = user_service.create_client({"name": "Erro", "email": "erro@x.com", "password": "1"})
    assert success is False and code == 500

    success, _, code = user_service.update_admin(9999, {"name": "Test"})
    assert success is False and code == 404

    success, _, code = user_service.delete_business_owner(9999)
    assert success is False and code == 404

def test_user_service_inner_branches(app):
    """Cobre as ramificações internas, populando listas de endereços e preferências no CRUD."""
    bt = BusinessType(name="Cafeteria Teste")
    db.session.add(bt)
    db.session.commit()
    
    payload = {
        "name": "Full User", "email": "full@x.com", "password": "1", "cpf": "999",
        "addresses": [{"road": "Rua 1", "number": 10, "district": "Centro", "zipcode": "123", "latitude": 0, "longitude": 0, "city_id": None}],
        "preferences": [bt.id]
    }
    
    success, _, _ = user_service.create_client(payload)
    assert success is True
    
    u = user_service.get_all_clients()[-1]
    
    update_payload = {
        "addresses": [{"road": "Rua 2"}],
        "preferences": [bt.id]
    }
    success_up, _, _ = user_service.update_client(u.id, update_payload)
    assert success_up is True

def test_user_service_owner_crud_failures(app, mocker):
    """Cobre as falhas na gestão de Owners no User Service, incluindo Not Found e exceções de banco."""
    lvl = Level(name="Test", description="Test")
    role = Role(name="owner", level=lvl)
    db.session.add_all([lvl, role])
    db.session.commit()
    user_service.create_business_owner({"name": "Real Owner", "email": "real_owner@t.com", "password": "1"})
    real_owner = user_service.get_all_business_owners()[-1]
    
    success, _, code = user_service.update_business_owner(9999, {"name": "Z"})
    assert success is False and code == 404
    
    mocker.patch("tasty.ext.db.db.session.commit", side_effect=SQLAlchemyError("Erro"))
    success, _, code = user_service.update_business_owner(real_owner.id, {"name": "Z"})
    assert success is False and code == 500

def test_user_service_admin_and_client_failures(app, mocker):
    """Mata os Miss forçando erros de commit nos CRUDs de Admin e Client."""
    user_service.create_admin({"name": "A", "email": "a@a.com", "password": "1"})
    user_service.create_client({"name": "C", "email": "c@c.com", "password": "1"})
    admin_id = user_service.get_all_admins()[-1].id
    client_id = user_service.get_all_clients()[-1].id
    
    mocker.patch("tasty.ext.db.db.session.commit", side_effect=SQLAlchemyError("Fail"))
    
    s, _, c = user_service.update_admin(admin_id, {"name": "X"})
    assert c == 500
    s, _, c = user_service.delete_admin(admin_id)
    assert c == 500
    
    s, _, c = user_service.update_client(client_id, {"name": "X"})
    assert c == 500
    s, _, c = user_service.delete_client(client_id)
    assert c == 500

def test_user_service_login_and_roles(app):
    """Cobre as validações de roles duplicadas, usuários inativos e sem nível de acesso no login."""
    user_service.get_or_create_level("Basic", "Desc")
    user_service.get_or_create_level("Basic", "Desc") 
    user_service.get_or_create_role("client", "Basic")
    user_service.get_or_create_role("client", "Basic") 
    
    pwd = generate_password_hash("123")
    u_inativo = User(name="I", email="inativo@teste.com", password=pwd, is_active=False)
    u_norole = User(name="N", email="norole@teste.com", password=pwd, is_active=True)
    db.session.add_all([u_inativo, u_norole])
    db.session.commit()
    
    s, _, c, _ = user_service.login("inativo@teste.com", "123")
    assert c == 403
    s, _, c, _ = user_service.login("norole@teste.com", "123")
    assert c == 404


# ---- Testes de Business Service ----

def test_business_service_full(app):
    """Cobre o ciclo de vida completo: criação, listagem, atualização e soft-delete de estabelecimentos."""
    lvl = Level(name="Premium", description="Lvl")
    role = Role(name="owner", level=lvl)
    city = City(name="Vila Velha", state="ES", country="Brasil")
    db.session.add_all([lvl, role, city])
    db.session.commit()

    user_service.create_business_owner({"name": "Dono", "email": "dono@t.com", "password": "1"})
    owner = user_service.get_all_business_owners()[0]

    biz_payload = {
        "corporate_name": "Pizzaria X LTDA",
        "trade_name": "Pizzaria X",
        "cnpj": "11.111.111/0001-11",
        "description": "Melhor pizza",
        "opening_time": "18:00",
        "closing_time": "23:00",
        "owners": [owner.id],
        "addresses": [{"road": "Rua A", "number": 10, "district": "Centro", "zipcode": "29100-000", "city_id": city.id}]
    }

    success, _, _ = b_service.create_business(biz_payload)
    assert success is True

    biz = b_service.get_all_businesses()[0]

    success_up, _, _ = b_service.update_business(biz.id, {"trade_name": "Pizzaria X Atualizada"})
    assert success_up is True

    success_del, _, _ = b_service.delete_business(biz.id)
    assert success_del is True

def test_business_service_negative_cases(app):
    """Testa erros de atualização e deleção ao fornecer IDs que não existem."""
    success, msg, code = b_service.update_business(9999, {"trade_name": "Ghost"})
    assert success is False
    assert code == 404
    
    success, msg, code = b_service.delete_business(9999)
    assert success is False

def test_business_service_inner_branches(app):
    """Cobre as validações estruturais de CNPJ e manipulação complexa de fotos e relações no Business Service."""
    u = User(name="Owner X", email="ox@x.com", password="123456", is_active=True)
    bt = BusinessType(name="Doceria Teste")
    db.session.add_all([u, bt])
    db.session.commit()
    
    s, _, code = b_service.create_business({"trade_name": "Sem CNPJ"})
    assert code == 400
    
    payload = {
        "corporate_name": "Doce", "trade_name": "Doce", "cnpj": "99.999.999/0001-99",
        "addresses": [{"road": "Rua", "number": 1}],
        "photos": [{"url": "http1", "description": "foto"}, "http2"], 
        "owners": [u.id],
        "business_types": [bt.id]
    }
    
    s, _, _ = b_service.create_business(payload)
    assert s is True
    
    s_dup, _, code_dup = b_service.create_business({"trade_name": "Cópia", "cnpj": "99.999.999/0001-99"})
    assert code_dup == 400
    
    b = b_service.get_all_businesses()[-1]
    
    update_payload = {
        "addresses": [{"road": "Rua Nova"}],
        "photos": ["http3"],
        "owners": [u.id],
        "business_types": [bt.id]
    }
    s_up, _, _ = b_service.update_business(b.id, update_payload)
    assert s_up is True


# ---- Testes de Business Type Service ----

def test_business_type_service_full(app):
    """Cobre o CRUD completo e positivo das categorias gastronômicas."""
    success, _, _ = bt_service.create_business_type({"name": "Japonesa", "emoji": "🍣"})
    assert success is True

    success_dup, _, _ = bt_service.create_business_type({"name": "Japonesa"})
    assert success_dup is False

    bt = bt_service.get_all_business_types()[0]
    
    success_up, _, _ = bt_service.update_business_type(bt.id, {"name": "Sushi", "emoji": "🍱"})
    assert success_up is True
    
    success_del, _, _ = bt_service.delete_business_type(bt.id)
    assert success_del is True

def test_forced_database_error(app, mocker):
    """Moca o commit do SQLAlchemy para forçar um erro de banco de dados e validar o exception."""
    mocker.patch("tasty.ext.db.db.session.commit", side_effect=SQLAlchemyError("Erro de DB"))
    
    success, msg, code = bt_service.create_business_type({"name": "Teste Erro", "emoji": "❌"})
    
    assert success is False
    assert code == 500
    assert "Erro interno" in msg

def test_business_type_service_failures(app, mocker):
    """Cobre falhas e exceções de banco para categorias gastronômicas."""
    bt_service.create_business_type({"name": "Categoria Real"})
    real_type = bt_service.get_all_business_types()[-1]
    
    s, _, c = bt_service.create_business_type(None)
    assert c == 400
    
    s, _, c = bt_service.update_business_type(9999, {"name": "X"})
    assert c == 404
    
    bt_service.create_business_type({"name": "Outra Categoria"})
    s, _, c = bt_service.update_business_type(real_type.id, {"name": "Outra Categoria"})
    assert c == 400
    
    s, _, c = bt_service.delete_business_type(9999)
    assert c == 404
    
    mocker.patch("tasty.ext.db.db.session.commit", side_effect=SQLAlchemyError("Erro"))
    s, _, c = bt_service.update_business_type(real_type.id, {"name": "Z"})
    assert c == 500
    
    s, _, c = bt_service.delete_business_type(real_type.id)
    assert c == 500


# ---- Testes de Location Service ----

def test_location_service_full(app, mocker):
    """Testa geocoding via mock, fórmula de haversine e gerenciamento básico de cidades."""
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = b'[{"lat": "-20.3297", "lon": "-40.2818"}]'
    mock_urlopen = mocker.patch("urllib.request.urlopen")
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    lat, lon = location_service.geocode_address("Av. Gil Veloso", "Praia da Costa", "29101-010")
    assert lat == -20.3297

    success, _, _ = location_service.create_city({"name": "Vitória", "state": "ES", "region": "Sudeste"})
    assert success is True

    city = location_service.get_all_cities()[0]
    success_up, _, _ = location_service.update_city(city.id, {"name": "Vitória Atualizada"})
    assert success_up is True
    assert location_service.get_city(city.id).name == "Vitória Atualizada"

def test_location_service_failures(app, mocker):
    """Cobre as contingências de falha de rede do Nominatim e erros do banco no Location Service."""
    mocker.patch("urllib.request.urlopen", side_effect=Exception("Timeout da API"))
    lat, lon = location_service.geocode_address("Rua", "Bairro", "123")
    
    assert lat == -20.3222
    assert lon == -40.3381
    
    dist_none = location_service.get_distance_between_user_and_business(999, 999)
    assert dist_none is None
    
    s, _, c = location_service.create_city({"name": "Sem Estado", "state": None})
    assert s is True
    
    mocker.patch("tasty.ext.db.db.session.commit", side_effect=SQLAlchemyError("Erro"))
    s, _, c = location_service.create_city({"name": "Fail", "state": "ES"})
    assert c == 500
    
    s, _, c = location_service.update_city(1, {"name": "Fail"})
    assert c == 500


# ---- Testes de Swipe e Analytics Service ----

def test_swipe_and_analytics_integration(app):
    """Mete a mão na massa simulando swipes reais e gerando telemetria agregada para analytics."""
    lvl = Level(name="Basic", description="Lvl")
    role_c = Role(name="client", level=lvl)
    role_o = Role(name="owner", level=lvl)
    db.session.add_all([lvl, role_c, role_o])
    db.session.commit()

    user_service.create_client({"name": "C", "email": "c@t.com", "password": "1"})
    user_service.create_business_owner({"name": "O", "email": "o@t.com", "password": "1"})
    
    client = user_service.get_all_clients()[0]
    owner = user_service.get_all_business_owners()[0]

    biz = Business(corporate_name="Comer LTDA", trade_name="Comer", cnpj="12.345/0001", is_active=True)
    biz.owners.append(owner)
    db.session.add(biz)
    db.session.commit()

    success, _, _ = swipe_service.swipe_business(client.id, biz.id, liked=True, super_like=True)
    assert success is True

    assert len(swipe_service.get_liked_businesses(client.id)) == 1
    
    next_feeds = swipe_service.get_next_businesses_for_user(client.id)
    assert isinstance(next_feeds, list)

    metrics_store = analytics_service.get_restaurant_metrics(biz.id)
    assert metrics_store["total_matches"] == 1
    assert metrics_store["super_likes"] == 1

    metrics_portfolio = analytics_service.get_owner_portfolio_metrics(owner.id)
    assert metrics_portfolio["active_stores"] == 1

    metrics_global = analytics_service.get_global_metrics()
    assert metrics_global["total_clients"] == 1

    success_reset, _, _ = swipe_service.reset_user_swipes(client.id)
    assert success_reset is True
    assert len(swipe_service.get_liked_businesses(client.id)) == 0

def test_swipe_service_robustness(app):
    """Testa fluxos críticos do Swipe Service como atualizações e registros inexistentes sem mocks."""
    u = User(name="C", email="c@x.com", password="1")
    b = Business(corporate_name="B", trade_name="B", cnpj="123", is_active=True)
    db.session.add_all([u, b])
    db.session.commit()
    
    success, _, code = swipe_service.swipe_business(u.id, 999, True)
    assert code == 404
    
    success, _, code = swipe_service.swipe_business(999, b.id, True)
    assert code == 404
    
    swipe_service.swipe_business(u.id, b.id, True)
    assert len(swipe_service.get_liked_businesses(u.id)) == 1
    
    swipe_service.swipe_business(u.id, b.id, False)
    assert len(swipe_service.get_liked_businesses(u.id)) == 0
    assert len(swipe_service.get_disliked_businesses(u.id)) == 1
    
    swipe_service.reset_user_swipes(u.id)
    assert len(swipe_service.get_disliked_businesses(u.id)) == 0

def test_swipe_service_recommendation_algorithm(app):
    """Cobre as ramificações matemáticas do algoritmo de recomendação mista (Tags + Distância)."""
    bt = BusinessType(name="Japonesa", emoji="🍣")
    b = Business(corporate_name="Sushi", trade_name="Sushi", cnpj="777", is_active=True)
    b.business_types.append(bt)
    b.addresses.append(Address(latitude=-20.0, longitude=-40.0))
    
    u = User(name="User", email="u@y.com", password="1", is_active=True)
    u.preferences.append(bt)
    u.addresses.append(Address(latitude=-20.0, longitude=-40.0))
    
    db.session.add_all([bt, b, u])
    db.session.commit()
    
    results = swipe_service.get_next_businesses_for_user(u.id)
    
    assert len(results) > 0
    assert hasattr(results[0], 'distance_km')

def test_swipe_service_exceptions(app, mocker):
    """Força falhas de banco de dados nas leituras e consultas de Swipe."""
    mocker.patch("tasty.services.swipe_service.db.session.execute", side_effect=SQLAlchemyError("DB Offline"))
    
    assert len(swipe_service.get_liked_businesses(1)) == 0
    assert len(swipe_service.get_disliked_businesses(1)) == 0
    assert len(swipe_service.get_next_businesses_for_user(1)) == 0