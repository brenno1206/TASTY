from flask import session, redirect, url_for, flash
from flask_admin.contrib.sqla import ModelView

class SecureModelView(ModelView):
    """
    Classe base de segurança. Sobrescreve o comportamento padrão do Flask-Admin
    para garantir proteção estrita de dados baseada na sessão da plataforma Tasty.
    """
    # Ativa recursos corporativos globais do Flask-Admin
    can_export = True
    page_size = 20

    def is_accessible(self):
        # O painel só é acessível se o usuário estiver logado e possuir papel de admin
        return session.get("user_id") is not None and session.get("user_role", "").startswith("admin")

    def inaccessible_callback(self, name, **kwargs):
        # Redireciona usuários não autorizados ou deslogados diretamente para a tela de login
        flash("Acesso restrito! Por favor, faça login como administrador.", "danger")
        return redirect(url_for("auth.login"))


class UserAdminView(SecureModelView):
    """Configuração gerencial da base de Usuários (Clientes, Owners e Admins)."""
    column_list = ["id", "name", "email", "phone", "role", "is_active", "created_at"]
    
    column_searchable_list = ["name", "email", "cpf"]
    
    column_filters = ["is_active", "role.name"]
    
    column_labels = {
        "id": "ID",
        "name": "Nome Completo",
        "email": "E-mail",
        "phone": "Telefone/Celular",
        "role": "Papel (Role)",
        "is_active": "Conta Ativa?",
        "created_at": "Data de Cadastro",
        "password": "Senha (Hash)"
    }
    
    # Proteção de segurança: impede a exibição ou edição acidental do hash da senha
    form_excluded_columns = ["password"]


class BusinessAdminView(SecureModelView):
    """Configuração gerencial dos Estabelecimentos Parceiros."""
    column_list = ["id", "trade_name", "cnpj", "opening_time", "closing_time", "is_active"]
    column_searchable_list = ["trade_name", "cnpj", "corporate_name"]
    column_filters = ["is_active"]
    column_labels = {
        "id": "ID",
        "trade_name": "Nome Fantasia",
        "corporate_name": "Razão Social",
        "cnpj": "CNPJ",
        "description": "Descrição do App",
        "opening_time": "Abertura",
        "closing_time": "Fechamento",
        "is_active": "Ativo no App?",
        "owners": "Proprietários Vinculados",
        "business_types": "Categorias Gastronômicas"
    }


class CityAdminView(SecureModelView):
    """Configuração das Cidades atendidas pelo radar de geolocalização."""
    column_list = ["id", "name", "state", "country", "region"]
    column_searchable_list = ["name", "state"]
    column_filters = ["state", "region"]
    column_labels = {
        "id": "ID",
        "name": "Cidade",
        "state": "Estado (UF)",
        "country": "País",
        "region": "Região Geográfica"
    }


class BusinessTypeAdminView(SecureModelView):
    """Configuração do catálogo de categorias gastronômicas (Onboarding/Tags)."""
    column_list = ["id", "name", "emoji", "description"]
    column_searchable_list = ["name"]
    column_labels = {
        "id": "ID",
        "name": "Categoria",
        "emoji": "Código Emoji HTML",
        "description": "Descrição Breve"
    }