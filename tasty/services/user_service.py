from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from tasty.models import User, Role, Level, Address, BusinessType
from tasty.ext.db import db

# ==========================================================
# GERENCIAMENTO DE NÍVEIS E PAPÉIS (ROLES)
# ==========================================================

def get_or_create_level(name: str, description: str = "") -> Level:
    stmt = select(Level).where(Level.name == name)
    level = db.session.execute(stmt).scalar_one_or_none()
    
    if not level:
        level = Level(name=name, description=description)
        db.session.add(level)
        db.session.commit()
    return level

def get_or_create_role(name: str, level_name: str = None) -> Role:
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
    if not data or not isinstance(data, dict):
        return False, "Erro: Dados inválidos.", 400
    
    # Copia o dicionário para evitar mutações colaterais no escopo de quem chamou a função
    payload = data.copy()
    
    try:
        # Validação estrita de unicidade antes da tentativa de inserção
        if db.session.execute(select(User).where(User.email == payload.get("email"))).scalar_one_or_none():
            return False, "Erro: Email já registrado.", 400
            
        if payload.get("cpf") and db.session.execute(select(User).where(User.cpf == payload.get("cpf"))).scalar_one_or_none():
            return False, "Erro: CPF já registrado.", 400
        
        role = get_or_create_role(role_name)
        
        # Isolamento de estruturas de relacionamentos
        addresses_data = payload.pop("addresses", [])
        preferences_ids = payload.pop("preferences", [])
        
        # Tratamento seguro da credencial secreta
        if "password" in payload:
            payload["password"] = generate_password_hash(payload["password"])
            
        # Instanciação mapeada do Usuário
        new_user = User(
            name=payload.get("name"),
            email=payload.get("email"),
            phone=payload.get("phone"),
            photo=payload.get("photo"),
            password=payload.get("password"),
            google_id=payload.get("google_id"),
            facebook_id=payload.get("facebook_id"),
            cpf=payload.get("cpf"),
            role_id=role.id
        )
        
        # Vinculo seguro de endereços
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
            
        # Vinculo N:N de preferências gastronômicas
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
    # Lista restrita de campos primitivos que podem sofrer mutação genérica por API cadastral
    allowed_fields = {"name", "phone", "photo", "google_id", "facebook_id", "cpf"}
    
    for key in allowed_fields:
        if key in data:
            setattr(user, key, data[key])
            
    # Atualização estrutural de endereços associados (Substituição por cascade completo)
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
            
    # Atualização N:N das preferências
    if "preferences" in data:
        user.preferences.clear()
        if data["preferences"]:
            b_types = db.session.execute(
                select(BusinessType).where(BusinessType.id.in_(data["preferences"]))
            ).scalars().all()
            user.preferences.extend(b_types)

def _soft_delete_user(user: User) -> None:
    user.is_active = False
    
def _get_active_users_by_role(role_name: str) -> List[User]:
    stmt = select(User).join(Role).where(Role.name == role_name, User.is_active == True)
    return list(db.session.execute(stmt).scalars().all())


# ==========================================================
# GERENCIAMENTO DE ADMINISTRADOR
# ==========================================================

def create_admin(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    return _create_user_with_role(data, "admin")

def get_admin(admin_id: int) -> Optional[User]:
    stmt = select(User).join(Role).where(User.id == admin_id, Role.name == "admin", User.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()

def get_admins_by_level(level_name: str) -> List[User]:
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
    return _get_active_users_by_role("admin")


# ==========================================================
# GERENCIAMENTO DE CLIENTE
# ==========================================================

def create_client(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    return _create_user_with_role(data, "client")

def get_client(client_id: int) -> Optional[User]:
    stmt = select(User).join(Role).where(User.id == client_id, Role.name == "client", User.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()

def update_client(client_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    client = get_client(client_id)
    if not client:
        return False, "Cliente não encontrado ou inativo.", 404
    try:
        _update_user_dynamically(client, data)
        db.session.commit()
        return True, "Cliente updated com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar: {str(e)}", 500

def delete_client(client_id: int) -> Tuple[bool, str, int]:
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
    return _get_active_users_by_role("client")


# ==========================================================
# GERENCIAMENTO DE DONO DE NEGÓCIO (OWNER)
# ==========================================================

def create_business_owner(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    return _create_user_with_role(data, "owner")

def get_business_owner(owner_id: int) -> Optional[User]:
    stmt = select(User).join(Role).where(User.id == owner_id, Role.name == "owner", User.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()

def update_business_owner(owner_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
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
        # Busca o usuário apenas pelo e-mail, trazendo junto o relacionamento da Role
        stmt = select(User).where(User.email == email)
        user = db.session.execute(stmt).scalar_one_or_none()
        
        # Caso 1: Usuário não existe no banco de dados
        if not user:
            return False, "Usuário não encontrado. Verifique o e-mail digitado ou cadastre-se.", 404, None
            
        # Caso 2: O usuário existe, mas foi desativado (soft delete)
        if not user.is_active:
            return False, "Esta conta foi desativada pelo administrador do sistema.", 403, None
            
        # Caso 3: Senha incorreta
        if not check_password_hash(user.password, password):
            return False, "Senha incorreta. Tente novamente.", 401, None
            
        # Caso 4: Usuário não possui uma role atrelada (erro de integridade do banco)
        if not user.role:
            return False, "Sua conta está sem perfil de acesso definido. Contate o suporte.", border_t-4, None
            
        # Sucesso absoluto: retorna o objeto de usuário completo
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