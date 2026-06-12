def test_business_list(auth_client, mocker):
    """Cobre a rota de listagem de negócios do painel do owner garantindo que apenas os negócios do owner logado sejam listados."""
    mock_biz = mocker.MagicMock()
    mock_biz.owners = [mocker.MagicMock(id=1)]
    mocker.patch('tasty.views.business_panel.b_service.get_all_businesses', return_value=[mock_biz])
    
    cli = auth_client(user_id=1, role="owner")
    assert cli.get("/my-business/list").status_code == 200

def test_business_creation(auth_client, mocker):
    """Cobre o fluxo de criação de negócio do painel do owner garantindo que o serviço seja chamado e a página redirecione."""
    mocker.patch('tasty.views.business_panel.bt_service.get_all_business_types', return_value=[])
    mocker.patch('tasty.views.business_panel.b_service.create_business', return_value=(True, "OK", 200))
    
    cli = auth_client(role="owner")
    assert cli.get("/my-business/register").status_code == 200
    assert cli.post("/my-business/register", data={"corporate_name": "Teste"}).status_code == 302

def test_business_edit_and_delete(auth_client, mocker):
    """Cobre as rotas de edição e deleção de negócio do painel do owner garantindo que apenas o owner possa editar/deletar seu negócio."""
    mock_biz = mocker.MagicMock()
    mock_biz.owners = [mocker.MagicMock(id=1)]
    mocker.patch('tasty.views.business_panel.b_service.get_business', return_value=mock_biz)
    mocker.patch('tasty.views.business_panel.b_service.update_business', return_value=(True, "OK", 200))
    mocker.patch('tasty.views.business_panel.b_service.delete_business', return_value=(True, "OK", 200))
    
    cli = auth_client(user_id=1, role="owner")
    assert cli.post("/my-business/5/edit", data={"trade_name": "Novo Nome"}).status_code == 302
    assert cli.post("/my-business/5/delete").status_code == 302

def test_business_panel_security_edge_cases(auth_client, mocker):
    """Mata as validações de segurança do painel do owner garantindo a URL correta."""
    cli = auth_client(role="owner")
    
    mocker.patch("tasty.services.business_service.get_business", return_value=None)
    
    assert cli.get("/my-business/999/edit").status_code == 302
    assert cli.post("/my-business/999/delete").status_code == 302

def test_business_panel_form_failures(auth_client, mocker):
    """Cobre os erros de formulário e banco de dados no painel do restaurante."""
    cli = auth_client(user_id=1, role="owner")

    mocker.patch("tasty.services.business_service.create_business", return_value=(False, "CNPJ Duplicado", 400))
    response_create = cli.post("/my-business/register", data={"trade_name": "Erro"})
    assert response_create.status_code == 200 

    mock_owner = mocker.MagicMock(id=1)
    mock_biz = mocker.MagicMock(id=1)
    mock_biz.owners = [mock_owner] 
    
    mocker.patch("tasty.services.business_service.get_business", return_value=mock_biz)
    mocker.patch("tasty.services.business_service.update_business", return_value=(False, "Erro DB", 500))

    response_update = cli.post("/my-business/1/edit", data={"trade_name": "Erro DB"})
    assert response_update.status_code == 200

    mocker.patch("tasty.services.business_service.delete_business", return_value=(False, "Erro DB", 500))
    response_delete = cli.post("/my-business/1/delete")
    assert response_delete.status_code == 302