from flask_admin import Admin
from tasty.ext.db import db
from tasty.models import User, Business, City, BusinessType, Role, Level

from tasty.ext.admin.views import (
    UserAdminView, BusinessAdminView, CityAdminView, BusinessTypeAdminView, SecureModelView
)

admin = Admin(
    name="Tasty Gerencial",
    url="/admin_panel",
    endpoint="admin_panel"
)

def init_app(app):
    """Vincula a infraestrutura do Flask-Admin ao ciclo de vida do aplicativo."""
    admin.init_app(app)
    app.logger.info("Flask-Admin inicializado com sucesso.")
    
    admin.add_view(UserAdminView(User, db, name="Usuários", category="Segurança"))
    admin.add_view(SecureModelView(Role, db, name="Papéis (Roles)", category="Segurança"))
    admin.add_view(SecureModelView(Level, db, name="Níveis de Acesso", category="Segurança"))
    admin.add_view(BusinessAdminView(Business, db, name="Restaurantes", category="Operações"))
    admin.add_view(BusinessTypeAdminView(BusinessType, db, name="Categorias Gastronômicas", category="Operações"))
    admin.add_view(CityAdminView(City, db, name="Cidades", category="Localidades"))

    app.logger.info("Views do Flask-Admin registradas com sucesso.")