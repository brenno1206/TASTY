import json

def test_discovery_feed_and_favorites(auth_client, mocker):
    """Cobre as rotas de feed e favoritos do Discovery simulando um cliente com preferências e endereço."""
    mock_user = mocker.MagicMock()
    mock_user.preferences = [1, 2] 
    mock_user.addresses = [mocker.MagicMock(latitude=-20.0)]
    
    mocker.patch('tasty.views.discovery.user_service.get_client', return_value=mock_user)
    mocker.patch('tasty.views.discovery.swipe_service.get_next_businesses_for_user', return_value=[])
    mocker.patch('tasty.views.discovery.swipe_service.get_liked_businesses', return_value=[])
    mocker.patch('tasty.views.discovery.get_distance_between_user_and_business', return_value=5.0)
    
    cli = auth_client(role="client")
    assert cli.get("/discovery/feed").status_code == 200
    assert cli.get("/discovery/favorites").status_code == 200

def test_discovery_swipe_action(auth_client, mocker):
    """Cobre a rota de swipe do Discovery garantindo que o serviço de swipe seja chamado e o JSON de resposta seja correto."""
    mocker.patch('tasty.views.discovery.swipe_service.swipe_business', return_value=(True, "OK", 200))
    cli = auth_client(role="client")
    
    payload = {"business_id": 1, "liked": True}
    response = cli.post("/discovery/swipe", data=json.dumps(payload), content_type="application/json")
    
    assert response.status_code == 200
    assert response.json["success"] is True

def test_discovery_restaurant_details_and_reset(auth_client, mocker):
    """Cobre a rota de detalhes de restaurante e reset de swipes do Discovery garantindo que os serviços sejam chamados e as páginas renderizadas."""
    mocker.patch('tasty.views.discovery.business_service.get_business', return_value=mocker.MagicMock())
    mocker.patch('tasty.views.discovery.get_distance_between_user_and_business', return_value=1.5)
    mocker.patch('tasty.views.discovery.swipe_service.reset_user_swipes', return_value=(True, "OK", 200))
    
    cli = auth_client(role="client")
    assert cli.get("/discovery/restaurant/10").status_code == 200
    assert cli.post("/discovery/reset").status_code == 302

def test_discovery_edge_cases(auth_client, mocker):
    """Cobre as falhas na rota de descoberta (Discovery)."""
    cli = auth_client(user_id=1, role="client")

    assert cli.post("/discovery/swipe", json={}).status_code == 400

    mocker.patch("tasty.services.swipe_service.swipe_business", return_value=(False, "Erro", 500))
    assert cli.post("/discovery/swipe", json={"business_id": 1, "liked": True}).status_code == 500

    mocker.patch("tasty.services.swipe_service.reset_user_swipes", return_value=(False, "Erro", 500))
    assert cli.post("/discovery/reset").status_code == 302
    
    mocker.patch("tasty.services.business_service.get_business", return_value=None)
    assert cli.get("/discovery/restaurant/9999").status_code == 302