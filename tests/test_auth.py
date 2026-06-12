import pytest

def test_login_success(client, mocker):
    """Testa se o envio de um login válido aciona o serviço e redireciona corretamente."""
    mock_user = mocker.MagicMock()
    mock_user.id = 1
    mock_user.role.name = "client"
    mock_user.name = "Teste"
    
    mocker.patch("tasty.views.auth.service.login", return_value=(True, "OK", 200, mock_user))
    
    response = client.post("/auth/login", data={
        "email": "teste@tasty.com", 
        "password": "senha_segura"
    })
    
    assert response.status_code == 302
    assert "/client/dashboard" in response.location


@pytest.mark.parametrize(
    "email, password, service_success, service_msg, expected_status",
    [
        ("nao_existe@tasty.com", "123456", False, "Usuário não encontrado.", 200),
        ("brenno@admin.com", "senha_errada", False, "Credenciais inválidas.", 200),
        
        ("", "senha123", False, "", 200),
        ("brenno@admin.com", "", False, "", 200),
        ("email_invalido_sem_arroba", "123", False, "", 200),
    ]
)

def test_login_failures(client, mocker, email, password, service_success, service_msg, expected_status):
    """Garante que dados incorretos ou em branco não efetuem login e mantenham o usuário na página (200 OK)."""
    
    mocker.patch(
        "tasty.views.auth.service.login", 
        return_value=(service_success, service_msg, 401, None)
    )
    
    response = client.post("/auth/login", data={
        "email": email,
        "password": password
    })
    
    assert response.status_code == expected_status
    
    if service_msg:
        assert service_msg.encode("utf-8") in response.data


def test_register_client_success(client, mocker):
    """Testa a criação de conta para clientes garantindo validação fluida do WTForms."""
    mocker.patch("tasty.views.auth.service.create_client", return_value=(True, "OK", 200))
    
    payload = {
        "name": "Novo Usuário",
        "email": "novo@tasty.com",
        "password": "senha123",
        "confirm_password": "senha123",
        "cpf": "111.111.111-11",
        "phone": "27999999999",
        "role": "client"
    }
    
    response = client.post("/auth/register", data=payload)
    assert response.status_code == 302
    assert "/auth/login" in response.location


@pytest.mark.parametrize(
    "missing_field, invalid_email, bad_cpf",
    [
        ("name", "valido@tasty.com", "111.111.111-11"),  # Nome em branco
        ("email", "", "111.111.111-11"),                 # Email em branco
        (None, "email_sem_formato.com", "111.111.111-11"),# Email inválido
        ("password", "valido@tasty.com", "111.111.111-11"),# Senha em branco
        ("cpf", "valido@tasty.com", ""),                  # CPF em branco
    ]
)
def test_register_validation_failures(client, mocker, missing_field, invalid_email, bad_cpf):
    """Injeta múltiplos cenários destrutivos e garante que o formulário de registro barra todos."""
    mocker.patch("tasty.views.auth.service.create_client", return_value=(True, "OK", 200))
    
    payload = {
        "name": "Usuário Teste",
        "email": invalid_email,
        "password": "senha123",
        "confirm_password": "senha123",
        "cpf": bad_cpf,
        "phone": "27999999999",
        "role": "client"
    }
    
    if missing_field:
        payload[missing_field] = ""
        
    response = client.post("/auth/register", data=payload)
    
    assert response.status_code == 200


def test_register_service_failure(client, mocker):
    """Testa quando os dados passam no formulário mas o Service rejeita (ex: CPF/Email já cadastrado)."""
    msg_erro_banco = "Este e-mail já está sendo utilizado por outra conta."
    
    mocker.patch("tasty.views.auth.service.create_client", return_value=(False, msg_erro_banco, 400))
    
    mock_flash = mocker.patch("tasty.views.auth.flash")
    
    payload = {
        "name": "Brenno Gomes Breda",
        "email": "brenno_duplicado@tasty.com",
        "password": "senha123",         
        "confirm_password": "senha123", 
        "cpf": "222.222.222-22",
        "phone": "27999999999",
        "role": "client"
    }
    
    response = client.post("/auth/register", data=payload)
    
    assert response.status_code == 200
    
    mock_flash.assert_called_with(msg_erro_banco, "danger")


def test_logout(auth_client):
    """Garante que a sessão seja encerrada corretamente e o usuário seja expulso para a Home."""
    cli = auth_client(role="client")
    response = cli.get("/auth/logout")
    
    assert response.status_code == 302
    assert "/" in response.location or "/index" in response.location

def test_auth_already_logged_in_and_decorators(auth_client, client):
    """Mata as linhas de Auth e Decorators forçando acessos indevidos."""
    assert client.get("/client/dashboard").status_code == 302
    
    cli = auth_client(role="client")
    
    assert cli.get("/admin/dashboard").status_code == 302
    
    assert cli.get("/auth/login").status_code == 302
    assert cli.get("/auth/register").status_code == 302