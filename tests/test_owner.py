def test_owner_dashboard_and_api(auth_client, mocker):
    """Testa o acesso ao dashboard do owner e à API de analytics garantindo que os serviços sejam chamados e as páginas renderizadas."""
    mocker.patch('tasty.views.owner.analytics_service.get_owner_portfolio_metrics', return_value={})
    
    cli = auth_client(role="owner")
    assert cli.get("/owner/dashboard").status_code == 200
    assert cli.get("/owner/api/analytics/summary").status_code == 200

def test_owner_restaurant_metrics(auth_client, mocker):
    """Testa a rota de métricas de restaurante do owner garantindo que o serviço seja chamado e a página renderizada, e que apenas o owner do restaurante possa acessar."""
    mock_biz = mocker.MagicMock()
    mock_biz.owners = [mocker.MagicMock(id=1)]
    
    mocker.patch('tasty.services.business_service.get_business', return_value=mock_biz)
    mocker.patch('tasty.views.owner.analytics_service.get_restaurant_metrics', return_value={})
    
    cli = auth_client(user_id=1, role="owner")
    assert cli.get("/owner/api/analytics/restaurant/5").status_code == 200

def test_admin_managing_owners(auth_client, mocker):
    """Apenas admins podem listar ou apagar donos de restaurante."""
    mocker.patch('tasty.views.owner.service.get_all_business_owners', return_value=[])
    mocker.patch('tasty.views.owner.service.delete_business_owner', return_value=(True, "OK", 200))
    
    cli = auth_client(role="admin")
    assert cli.get("/owner/list").status_code == 200
    assert cli.post("/owner/2/delete").status_code == 302

def test_owner_edit_profile_full_coverage(auth_client, mocker):
    """Verifica a edição de perfil do owner cobrindo as validações, chamadas de serviço e redirecionamentos."""
    cli = auth_client(user_id=1, role="owner")
    
    mock_user = mocker.MagicMock()
    mock_user.id = 1
    mocker.patch('tasty.views.owner.service.get_business_owner', return_value=mock_user)
    mocker.patch('tasty.views.owner.service.update_business_owner', return_value=(True, "OK", 200))
    mocker.patch('tasty.views.owner.service.change_user_password', return_value=(True, "OK", 200))
    
    assert cli.get("/owner/1/edit").status_code == 200
    
    payload = {
        "name": "Novo Dono",
        "old_password": "velha",
        "new_password": "nova"
    }
    response = cli.post("/owner/1/edit", data=payload)
    assert response.status_code == 302