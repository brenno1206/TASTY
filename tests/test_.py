import pytest
from tasty.app import create_app


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200


@pytest.fixture
def app():
    return create_app()


def test_not_found(client):
    response = client.get("/url-inexistente")
    assert response.status_code == 404


# pytest --cov=tasty
# Esse comando gera um relatório indicando quais partes do código foram executadas durante os testes.
