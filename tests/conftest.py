import pytest
from tasty import create_app
from tasty.ext.db import db

# pytest --cov=tasty  

@pytest.fixture(scope="session")
def app():
    """Cria a aplicação apenas UMA VEZ para toda a sessão, evitando duplicidade de extensões globais."""
    app = create_app()
    
    app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False, 
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:" 
    })
    
    yield app

@pytest.fixture(autouse=True)
def setup_database(app):
    """Cria e destrói o banco de dados limpo automaticamente ANTES e DEPOIS de CADA teste."""
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Gera o cliente web virtual nativo para disparar as requisições."""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """
    Fábrica de clientes autenticados.
    Permite logar instantaneamente injetando os dados direto no cookie de sessão do Flask.
    """
    def _login(user_id=1, role="client", name="Test User"):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_role"] = role
            sess["user_name"] = name
        return client
    return _login