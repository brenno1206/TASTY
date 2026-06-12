def test_admin_dashboard(auth_client, mocker):
    """Cobre a rota de dashboard do admin, garantindo que as métricas sejam buscadas e a página renderizada."""
    mocker.patch('tasty.views.admin.analytics_service.get_global_metrics', return_value={})
    cli = auth_client(role="admin")
    assert cli.get("/admin/dashboard").status_code == 200

def test_admin_list_team(auth_client, mocker):
    """Cobre a rota de listagem de equipe do admin."""
    mock_admin = mocker.MagicMock()
    mock_admin.id = 1
    mock_admin.role.level.name = "max"
    
    mocker.patch('tasty.views.admin.service.get_admin', return_value=mock_admin)
    mocker.patch('tasty.views.admin.service.get_all_admins', return_value=[mock_admin])
    
    cli = auth_client(role="admin")
    assert cli.get("/admin/list").status_code == 200

def test_admin_businesses_and_types(auth_client, mocker):
    """Cobre as rotas de listagem de negócios e tipos de negócios do admin."""
    mocker.patch('tasty.views.admin.b_service.get_all_businesses', return_value=[])
    mocker.patch('tasty.views.admin.bt_service.get_all_business_types', return_value=[])
    
    cli = auth_client(role="admin")
    assert cli.get("/admin/businesses").status_code == 200
    assert cli.get("/admin/business_types").status_code == 200

def test_admin_edit_and_delete_teammate(auth_client, mocker):
    """Cobre as rotas de edição e deleção de membros da equipe do admin."""
    mocker.patch('tasty.views.admin.service.get_admin', return_value=mocker.MagicMock())
    mocker.patch('tasty.views.admin.service.update_admin', return_value=(True, "OK", 200))
    mocker.patch('tasty.views.admin.service.delete_admin', return_value=(True, "OK", 200))
    
    cli = auth_client(role="admin")
    assert cli.post("/admin/2/edit", data={"name": "Novo"}).status_code == 302
    assert cli.post("/admin/2/delete").status_code == 302

def test_admin_business_types_creation_flow(auth_client, mocker):
    """Cobre o fluxo completo de criação de categoria na rota admin."""
    cli = auth_client(role="admin")

    mocker.patch("tasty.views.admin.db.session.add")
    mocker.patch("tasty.views.admin.db.session.commit")
    
    response_success = cli.post("/admin/business_types", data={
        "name": "Nova Categoria",
        "description": "Uma categoria de teste",
        "emoji": "&#128640;"
    })
    assert response_success.status_code == 302
    
    response_empty = cli.post("/admin/business_types", data={
        "name": "",
        "description": "Sem nome"
    })
    assert response_empty.status_code == 200
    
    mocker.patch("tasty.views.admin.db.session.commit", side_effect=Exception("DB Offline"))
    response_db_error = cli.post("/admin/business_types", data={"name": "Quebra DB"})
    assert response_db_error.status_code == 200

def test_admin_edit_and_delete_failures(auth_client, mocker):
    """Cobre as falhas de acesso e banco na edição/deleção de admins via View."""
    cli = auth_client(role="admin")
    
    response = cli.get("/admin/9999/edit")
    assert response.status_code == 302 
    
    mocker.patch("tasty.views.admin.service.update_admin", return_value=(False, "Erro DB", 500))
    mocker.patch("tasty.views.admin.service.get_admin", return_value=mocker.MagicMock(id=1))
    
    response_post = cli.post("/admin/1/edit", data={"name": "Tentativa"})
    assert response_post.status_code == 200