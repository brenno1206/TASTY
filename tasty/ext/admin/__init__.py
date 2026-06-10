from flask_admin import Admin
from tasty.ext.db import db
from tasty.models import User, Business, City, BusinessType, Role, Level

# Importação das visões customizadas protegidas
from tasty.ext.admin.views import (
    UserAdminView, BusinessAdminView, CityAdminView, BusinessTypeAdminView, SecureModelView
)

# Instanciação da extensão administrativa isolada do escopo de inicialização
admin = Admin(
    name="Tasty Gerencial",
    url="/admin_panel",          # Rota exclusiva para não colidir com o dashboard antigo do Admin
    endpoint="admin_panel"       # Nome do endpoint base do Flask-Admin
)

def init_app(app):
    """Vincula a infraestrutura do Flask-Admin ao ciclo de vida do aplicativo."""
    admin.init_app(app)
    
    # Registro automatizado das tabelas ORM mapeadas com as regras de visualização
    admin.add_view(UserAdminView(User, db.session, name="Usuários", category="Segurança"))
    admin.add_view(SecureModelView(Role, db.session, name="Papéis (Roles)", category="Segurança"))
    admin.add_view(SecureModelView(Level, db.session, name="Níveis de Acesso", category="Segurança"))
    
    admin.add_view(BusinessAdminView(Business, db.session, name="Restaurantes", category="Operações"))
    admin.add_view(BusinessTypeAdminView(BusinessType, db.session, name="Categorias Gastronômicas", category="Operações"))
    
    admin.add_view(CityAdminView(City, db.session, name="Cidades", category="Localidades"))