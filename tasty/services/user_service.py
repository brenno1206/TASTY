from typing import Dict, Any, Tuple, Optional, List
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from tasty.models import User, Role, Level, Address, BusinessType
from tasty.ext.db import db

# ==========================================================
# GERENCIAMENTO DE NÍVEIS E PAPÉIS (ROLES)
# ==========================================================

def get_or_create_level(name: str, description: str = "") -> Level:
    """Busca um nível de acesso pelo nome ou o cria caso não exista, garantindo integridade e evitando duplicatas."""
    stmt = select(Level).where(Level.name == name)
    level = db.session.execute(stmt).scalar_one_or_none()
    
    if not level:
        level = Level(name=name, description=description)
        db.session.add(level)
        db.session.commit()
    return level

def get_or_create_role(name: str, level_name: str = None) -> Role:
    """Busca um papel de acesso pelo nome ou o cria caso não exista, associando-o a um nível se fornecido."""
    stmt = select(Role).where(Role.name == name)
    role = db.session.execute(stmt).scalar_one_or_none()
    
    if not role:
        role = Role(name=name)
        if level_name:
            level_stmt = select(Level).where(Level.name == level_name)
            level = db.session.execute(level_stmt).scalar_one_or_none()
            if level:
                role.level = level
                
        db.session.add(role)
        db.session.commit()
    return role


# ==========================================================
# FUNÇÕES AUXILIARES GERAIS DE USUÁRIO
# ==========================================================

def _create_user_with_role(data: Dict[str, Any], role_name: str) -> Tuple[bool, str, int]:
    """Função auxiliar para criação de usuários com um papel específico, garantindo validações e integridade."""
    if not data or not isinstance(data, dict):
        return False, "Erro: Dados inválidos.", 400
    
    payload = data.copy()
    
    try:
        if db.session.execute(select(User).where(User.email == payload.get("email"))).scalar_one_or_none():
            return False, "Erro: Email já registrado.", 400
            
        if payload.get("cpf") and db.session.execute(select(User).where(User.cpf == payload.get("cpf"))).scalar_one_or_none():
            return False, "Erro: CPF já registrado.", 400
        
        role = get_or_create_role(role_name)
        
        addresses_data = payload.pop("addresses", [])
        preferences_ids = payload.pop("preferences", [])
        
        if "password" in payload:
            payload["password"] = generate_password_hash(payload["password"])
            
        new_user = User(
            name=payload.get("name"),
            email=payload.get("email"),
            phone=payload.get("phone"),
            photo=payload.get("photo"),
            password=payload.get("password"),
            cpf=payload.get("cpf"),
            role_id=role.id
        )
        
        for addr in addresses_data:
            new_user.addresses.append(
                Address(
                    road=addr.get("road"),
                    number=addr.get("number"),
                    district=addr.get("district"),
                    zipcode=addr.get("zipcode"),
                    latitude=addr.get("latitude"),
                    longitude=addr.get("longitude"),
                    city_id=addr.get("city_id")
                )
            )
            
        if preferences_ids:
            b_types = db.session.execute(
                select(BusinessType).where(BusinessType.id.in_(preferences_ids))
            ).scalars().all()
            new_user.preferences.extend(b_types)
            
        db.session.add(new_user)
        db.session.commit()
        return True, f"{role_name.capitalize()} criado com sucesso.", 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro no banco de dados: {str(e)}", 500

def _update_user_dynamically(user: User, data: Dict[str, Any]) -> None:
    """Atualiza de forma segura atributos diretos e relacionamentos permitidos."""
    allowed_fields = {"name", "phone", "photo", "cpf"}
    
    for key in allowed_fields:
        if key in data:
            setattr(user, key, data[key])
            
    if "addresses" in data:
        user.addresses.clear()
        for addr in data["addresses"]:
            user.addresses.append(
                Address(
                    road=addr.get("road"),
                    number=addr.get("number"),
                    district=addr.get("district"),
                    zipcode=addr.get("zipcode"),
                    latitude=addr.get("latitude"),
                    longitude=addr.get("longitude"),
                    city_id=addr.get("city_id")
                )
            )
            
    if "preferences" in data:
        user.preferences.clear()
        if data["preferences"]:
            b_types = db.session.execute(
                select(BusinessType).where(BusinessType.id.in_(data["preferences"]))
            ).scalars().all()
            user.preferences.extend(b_types)

def _soft_delete_user(user: User) -> None:
    """Realiza um soft delete marcando o usuário como inativo, preservando dados históricos e relações."""
    user.is_active = False
    
def _get_active_users_by_role(role_name: str) -> List[User]:
    """Retorna uma lista de usuários ativos filtrados por papel específico."""
    stmt = select(User).join(Role).where(Role.name == role_name, User.is_active == True)
    return list(db.session.execute(stmt).scalars().all())


# ==========================================================
# GERENCIAMENTO DE ADMINISTRADOR
# ==========================================================

def create_admin(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Cria um administrador com validações específicas e atribuição automática de papel."""
    return _create_user_with_role(data, "admin")

def get_admin(admin_id: int) -> Optional[User]:
    """Retorna um administrador específico pelo ID apenas se estiver ativo, garantindo que o papel seja de admin."""
    stmt = select(User).join(Role).where(User.id == admin_id, Role.name == "admin", User.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()

def get_admins_by_level(level_name: str) -> List[User]:
    """Retorna uma lista de administradores filtrados por nível de acesso, garantindo que sejam ativos."""
    stmt = (
        select(User)
        .join(Role)
        .join(Level)
        .where(
            Role.name == "admin", 
            Level.name == level_name,
            User.is_active == True
        )
    )
    return list(db.session.execute(stmt).scalars().all())

def update_admin(admin_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Atualiza os dados de um administrador específico, garantindo validações e integridade dos dados."""
    admin = get_admin(admin_id)
    if not admin:
        return False, "Administrador não encontrado ou inativo.", 404
        
    try:
        _update_user_dynamically(admin, data)
        db.session.commit()
        return True, "Administrador atualizado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar: {str(e)}", 500

def delete_admin(admin_id: int) -> Tuple[bool, str, int]:
    """Realiza um soft delete em um administrador específico, marcando-o como inativo para preservar dados históricos e relações, garantindo que o papel seja de admin."""
    admin = get_admin(admin_id)
    if not admin:
        return False, "Administrador não encontrado.", 404
    try:
        _soft_delete_user(admin)
        db.session.commit()
        return True, "Administrador desativado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao desativar: {str(e)}", 500

def get_all_admins() -> List[User]:
    """Retorna uma lista de todos os administradores ativos, garantindo que o papel seja de admin."""
    return _get_active_users_by_role("admin")


# ==========================================================
# GERENCIAMENTO DE CLIENTE
# ==========================================================

def create_client(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Cria um cliente com validações específicas e atribuição automática de papel."""
    return _create_user_with_role(data, "client")

def get_client(client_id: int) -> Optional[User]:
    """Retorna um cliente específico pelo ID apenas se estiver ativo, garantindo que o papel seja de client."""
    stmt = select(User).join(Role).where(User.id == client_id, Role.name == "client", User.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()

def update_client(client_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Atualiza os dados de um cliente específico, garantindo validações e integridade dos dados."""
    client = get_client(client_id)
    if not client:
        return False, "Cliente não encontrado ou inativo.", 404
    try:
        _update_user_dynamically(client, data)
        db.session.commit()
        return True, "Cliente atualizado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar: {str(e)}", 500

def delete_client(client_id: int) -> Tuple[bool, str, int]:
    """Realiza um soft delete em um cliente específico, marcando-o como inativo para preservar dados históricos e relações, garantindo que o papel seja de client."""
    client = get_client(client_id)
    if not client:
        return False, "Cliente não encontrado.", 404
    try:
        _soft_delete_user(client)
        db.session.commit()
        return True, "Cliente desativado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao desativar: {str(e)}", 500

def get_all_clients() -> List[User]:
    """Retorna uma lista de todos os clientes ativos, garantindo que o papel seja de client."""
    return _get_active_users_by_role("client")


# ==========================================================
# GERENCIAMENTO DE DONO DE NEGÓCIO (OWNER)
# ==========================================================

def create_business_owner(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Cria um dono de negócio com validações específicas e atribuição automática de papel."""
    return _create_user_with_role(data, "owner")

def get_business_owner(owner_id: int) -> Optional[User]:
    """Retorna um dono de negócio específico pelo ID apenas se estiver ativo, garantindo que o papel seja de owner."""
    stmt = select(User).join(Role).where(User.id == owner_id, Role.name == "owner", User.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()

def update_business_owner(owner_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Atualiza os dados de um dono de negócio específico, garantindo validações e integridade dos dados."""
    owner = get_business_owner(owner_id)
    if not owner:
        return False, "Dono de negócio não encontrado ou inativo.", 404
    try:
        _update_user_dynamically(owner, data)
        db.session.commit()
        return True, "Dono de negócio atualizado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar: {str(e)}", 500

def delete_business_owner(owner_id: int) -> Tuple[bool, str, int]:
    """Realiza um soft delete em um dono de negócio específico, marcando-o como inativo para preservar dados históricos e relações, garantindo que o papel seja de owner."""
    owner = get_business_owner(owner_id)
    if not owner:
        return False, "Dono de negócio não encontrado.", 404
    try:
        _soft_delete_user(owner)
        db.session.commit()
        return True, "Dono de negócio desativado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao desativar: {str(e)}", 500

def get_all_business_owners() -> List[User]:
    """Retorna uma lista de todos os donos de negócio ativos, garantindo que o papel seja de owner."""
    return _get_active_users_by_role("owner")


# ==========================================================
# GERENCIAMENTO DE AUTENTICAÇÃO E CREDENCIAIS SEGURAS
# ==========================================================

def login(email: str, password: str) -> Tuple[bool, str, int, Optional[User]]:
    """
    Autentica um usuário de forma global baseando-se estritamente em e-mail e senha.
    Retorna erros explícitos e consistentes para cada falha no processo.
    """
    try:
        stmt = select(User).where(User.email == email)
        user = db.session.execute(stmt).scalar_one_or_none()
        
        if not user:
            return False, "Usuário não encontrado. Verifique o e-mail digitado ou cadastre-se.", 404, None
            
        if not user.is_active:
            return False, "Esta conta foi desativada pelo administrador do sistema.", 403, None
            
        if not check_password_hash(user.password, password):
            return False, "Senha incorreta. Tente novamente.", 401, None
            
        if not user.role:
            return False, "Sua conta está sem perfil de acesso definido. Contate o suporte.", 404, None
            
        return True, "Login bem-sucedido.", 200, user
        
    except SQLAlchemyError as e:
        return False, f"Erro interno de comunicação com o banco de dados: {str(e)}", 500, None

def change_user_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str, int]:
    """Serviço dedicado e seguro para alteração interna de senhas via validação cruzada."""
    try:
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        user = db.session.execute(stmt).scalar_one_or_none()
        
        if not user:
            return False, "Usuário inválido ou inativo.", 404
            
        if not check_password_hash(user.password, old_password):
            return False, "Senha atual incorreta.", 401
            
        user.password = generate_password_hash(new_password)
        db.session.commit()
        return True, "Senha modificada com sucesso.", 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao alterar credenciais: {str(e)}", 500