def test_admin_dashboard_access(auth_client, mocker):
    """Verifica se um Admin consegue entrar no painel e se clientes são barrados."""
    # Isola o banco de dados das estatísticas
    mocker.patch('tasty.services.analytics_service.get_global_metrics', return_value={})
    
    # 1. Teste de Sucesso (Admin Logado)
    # Criamos um cliente já com o cookie de "admin"
    admin_cli = auth_client(role="admin")
    response_admin = admin_cli.get("/admin/dashboard")
    assert response_admin.status_code == 200  # Entrou com sucesso!
    
    # 2. Teste de Bloqueio (Cliente tentando entrar no Admin)
    # Criamos um cliente com cookie de "client"
    client_cli = auth_client(role="client")
    response_blocked = client_cli.get("/admin/dashboard")
    # Deve dar 302 Redirect (Redirecionando para fora dali por falta de permissão)
    assert response_blocked.status_code == 302 

def test_client_dashboard_access(auth_client):
    """Verifica se o Cliente consegue entrar no seu próprio dashboard."""
    cli = auth_client(role="client")
    response = cli.get("/client/dashboard")
    assert response.status_code == 200

def test_owner_dashboard_access(auth_client, mocker):
    """Verifica se o Proprietário consegue entrar no dashboard de métricas."""
    mocker.patch('tasty.services.analytics_service.get_owner_portfolio_metrics', return_value={})
    
    cli = auth_client(role="owner")
    response = cli.get("/owner/dashboard")
    assert response.status_code == 200