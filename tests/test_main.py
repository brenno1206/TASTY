def test_index_route(client, mocker):
    """Verifica se a Landing Page carrega as categorias perfeitamente."""
    mocker.patch('tasty.views.main.bt_service.get_all_business_types', return_value=[])
    
    response = client.get("/")
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data
    
    response_index = client.get("/index")
    assert response_index.status_code == 200