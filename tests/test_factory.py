def test_blueprints_registered(app):
    """Garante que a fábrica acoplou todos os submódulos da plataforma."""
    registered = app.blueprints.keys()
    
    assert "auth" in registered
    assert "admin" in registered
    assert "client" in registered
    assert "owner" in registered
    assert "business_panel" in registered
    assert "discovery" in registered
    assert "main" in registered