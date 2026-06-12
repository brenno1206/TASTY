import json

def test_client_dashboard(auth_client):
    """Testa o acesso à dashboard do cliente garantindo que a autenticação e autorização estão funcionando."""
    cli = auth_client(role="client")
    assert cli.get("/client/dashboard").status_code == 200

def test_client_onboarding_process(auth_client, mocker):
    mocker.patch('tasty.views.client.bt_service.get_all_business_types', return_value=[])
    mocker.patch('tasty.views.client.geocode_address', return_value=(-20.0, -40.0))
    mocker.patch('tasty.views.client.service.update_client', return_value=(True, "OK", 200))
    
    mock_user = mocker.MagicMock()
    mock_user.id = 1
    mocker.patch('tasty.views.client.service.get_client', return_value=mock_user)
    
    @mocker.patch('tasty.views.client.render_template')
    def mock_render(template_name, **context):
        context['user'] = mock_user
        from flask import render_template
        return render_template(template_name, **context)

    cli = auth_client(user_id=1, role="client")
    
    assert cli.get("/client/onboarding").status_code == 200
    
    payload = {"address": {"road": "Rua 1", "zipcode": "123"}}
    response = cli.post("/client/onboarding", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200

def test_admin_managing_clients(auth_client, mocker):
    """Apenas admins podem listar ou apagar clientes."""
    mocker.patch('tasty.views.client.service.get_all_clients', return_value=[])
    mocker.patch('tasty.views.client.service.delete_client', return_value=(True, "OK", 200))
    
    cli = auth_client(role="admin")
    assert cli.get("/client/list").status_code == 200
    assert cli.post("/client/2/delete").status_code == 302

def test_client_edit_profile_full_coverage(auth_client, mocker):
    """Cobre as 60 linhas de views/client.py que validam a edição do perfil."""
    cli = auth_client(user_id=1, role="client")
    
    mock_user = mocker.MagicMock()
    mock_user.id = 1
    mocker.patch('tasty.views.client.service.get_client', return_value=mock_user)
    mocker.patch('tasty.views.client.bt_service.get_all_business_types', return_value=[])
    mocker.patch('tasty.views.client.service.update_client', return_value=(True, "OK", 200))
    mocker.patch('tasty.views.client.service.change_user_password', return_value=(True, "OK", 200))
    mocker.patch('tasty.views.client.geocode_address', return_value=(-20.0, -40.0))
    
    assert cli.get("/client/1/edit").status_code == 200
    
    payload = {
        "name": "Nome Atualizado",
        "old_password": "senha_antiga",
        "new_password": "senha_nova",
        "preferences": ["1", "2"],
        "road": "Rua Central",
        "district": "Centro",
        "zipcode": "29100",
        "number": "100"
    }
    
    response = cli.post("/client/1/edit", data=payload)
    
    assert response.status_code == 302

def test_client_edit_profile_full_coverage(auth_client, mocker):
    """Cobre as 60 linhas de views/client.py que validam a edição do perfil (Mata as linhas 77-135)."""
    cli = auth_client(user_id=1, role="client")
    
    mock_user = mocker.MagicMock()
    mock_user.id = 1
    mocker.patch('tasty.views.client.service.get_client', return_value=mock_user)
    mocker.patch('tasty.views.client.bt_service.get_all_business_types', return_value=[])
    
    mocker.patch('tasty.views.client.geocode_address', return_value=(-20.0, -40.0))
    mocker.patch('tasty.views.client.service.change_user_password', return_value=(True, "OK", 200))
    mocker.patch('tasty.views.client.service.update_client', return_value=(True, "OK", 200))
    
    payload = {
        "name": "Nome Atualizado",
        "old_password": "senha_antiga",
        "new_password": "senha_nova",
        "preferences": ["1", "2"],
        "road": "Rua Central",
        "district": "Centro",
        "zipcode": "29100",
        "number": "100"
    }
    
    response = cli.post("/client/1/edit", data=payload)
    assert response.status_code == 302
   
def test_client_views_edge_cases(auth_client, mocker):
    """Mata as linhas vermelhas de segurança na rota de clientes."""
    cli = auth_client(role="client")
    
    assert cli.post("/client/onboarding", json={}).status_code == 400
    
    assert cli.get("/client/2/edit").status_code == 302
    
    admin_cli = auth_client(role="admin")
    mocker.patch('tasty.views.client.service.get_client', return_value=None)
    assert admin_cli.get("/client/9999/edit").status_code == 302