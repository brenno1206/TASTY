import json

def test_save_onboarding_success(auth_client, mocker):
    """Garante que o onboarding do cliente processa endereço e preferências com sucesso."""
    mocker.patch('tasty.views.client.geocode_address', return_value=(-20.3297, -40.2818))
    mocker.patch('tasty.services.user_service.update_client', return_value=(True, "Onboarding concluído", 200))

    cli = auth_client(role="client")
    
    payload = {
        "preferences": [1, 2, 3],
        "address": {
            "road": "Av. Antônio Gil Veloso",
            "number": 100,
            "district": "Praia da Costa",
            "zipcode": "29101-010"
        }
    }

    response = cli.post(
        "/client/onboarding",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200
    assert response.json["message"] == "Onboarding concluído com sucesso."


def test_swipe_action_registration(auth_client, mocker):
    """Testa a rota de swipe capturando o payload JSON de interação."""
    mocker.patch('tasty.services.swipe_service.swipe_business', return_value=(True, "Swipe registrado", 200))

    cli = auth_client(role="client")
    
    payload = {
        "business_id": 5,
        "liked": True,
        "super_like": False
    }

    response = cli.post(
        "/discovery/swipe",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200
    assert response.json["success"] is True

def test_client_edit_profile_failures(auth_client, mocker):
    """Cobre as falhas de validação de senha e banco de dados na edição de perfil."""
    cli = auth_client(user_id=1, role="client")
    
    mock_user = mocker.MagicMock(id=1)
    mocker.patch('tasty.views.client.service.get_client', return_value=mock_user)
    
    mocker.patch('tasty.views.client.service.change_user_password', return_value=(False, "Senha atual errada", 400))
    response_bad_pw = cli.post("/client/1/edit", data={"old_password": "errada", "new_password": "nova"})
    assert response_bad_pw.status_code == 302 # Redireciona de volta para tentar de novo
    
    mocker.patch('tasty.views.client.service.change_user_password', return_value=(True, "OK", 200))
    mocker.patch('tasty.views.client.service.update_client', return_value=(False, "Erro DB", 500))
    
    response_bad_db = cli.post("/client/1/edit", data={"name": "Quebra DB"})
    assert response_bad_db.status_code == 200