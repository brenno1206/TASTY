from typing import Dict, Any, Tuple, Optional, List
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from tasty.models import (
    User, Role, Level, Business, Address, City, 
    BusinessType, Photo
)
from tasty.ext.db import db

# ==========================================================
# GERENCIAMENTO DE NÍVEIS E PAPÉIS (ROLES)
# ==========================================================

def get_or_create_level(name: str, description: str = "") -> 'Level':
    stmt = select(Level).where(Level.name == name)
    level = db.session.execute(stmt).scalar_one_or_none()
    
    if not level:
        level = Level(name=name, description=description)
        db.session.add(level)
        db.session.commit()
    return level

def get_or_create_role(name: str, level_name: str = None) -> 'Role':
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
# FUNÇÕES AUXILIARES GERAIS
# ==========================================================

def _create_user_with_role(data: Dict[str, Any], role_name: str) -> Tuple[bool, str, int]:
    if not data or not isinstance(data, dict):
        return False, "Erro: Dados inválidos.", 400
    
    try:
        # Verifica se email e CPF já existem
        if db.session.execute(select(User).where(User.email == data.get("email"))).scalar_one_or_none():
            return False, "Erro: Email já registrado.", 400
        if data.get("cpf") and db.session.execute(select(User).where(User.cpf == data.get("cpf"))).scalar_one_or_none():
            return False, "Erro: CPF já registrado.", 400
        
        role = get_or_create_role(role_name)
        
        # Extrai relacionamentos para não quebrar a criação dinâmica
        addresses_data = data.pop("addresses", [])
        preferences_ids = data.pop("preferences", [])
        
        # Faz o hash da senha
        if "password" in data:
            data["password"] = generate_password_hash(data["password"])
            
        # Cria usuário com todos os atributos restantes (name, phone, photo, etc)
        new_user = User(**data, role_id=role.id)
        
        # Associa Endereços (1:N)
        for addr in addresses_data:
            new_user.addresses.append(Address(**addr))
            
        # Associa Preferências de BusinessTypes (N:N)
        if preferences_ids:
            b_types = db.session.execute(select(BusinessType).where(BusinessType.id.in_(preferences_ids))).scalars().all()
            new_user.preferences.extend(b_types)
            
        db.session.add(new_user)
        db.session.commit()
        return True, f"{role_name.capitalize()} criado com sucesso.", 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro no banco de dados: {str(e)}", 500

def _update_user_dynamically(user: User, data: Dict[str, Any]) -> None:
    """Atualiza atributos e relacionamentos de um usuário dinamicamente."""
    # Atualiza atributos diretos
    for key, value in data.items():
        if hasattr(user, key) and key not in ["id", "role_id", "addresses", "preferences", "owned_businesses"]:
            if key == "password":
                value = generate_password_hash(value)
            setattr(user, key, value)
            
    # Atualiza Endereços (Substitui os antigos pelos novos)
    if "addresses" in data:
        user.addresses.clear() # Deleta os órfãos graças ao cascade="all, delete-orphan"
        for addr in data["addresses"]:
            user.addresses.append(Address(**addr))
            
    # Atualiza Preferências
    if "preferences" in data:
        user.preferences.clear()
        b_types = db.session.execute(select(BusinessType).where(BusinessType.id.in_(data["preferences"]))).scalars().all()
        user.preferences.extend(b_types)

def _soft_delete_user(user: User) -> None:
    """Aplica o soft delete."""
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
    """Obtém administradores filtrados por um nível específico (ex: 'max', 'premium', 'basic')."""
    stmt = (
        select(User)
        .join(Role)
        .join(Level)
        .where(
            Role.name == "admin", 
            Level.name == level_name,
            User.is_active == True # Apenas admins ativos
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
        return True, "Cliente atualizado com sucesso.", 200
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
# GERENCIAMENTO DE DONO DE NEGÓCIO
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
# GERENCIAMENTO DE NEGÓCIO
# ==========================================================

def create_business(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    if not data or not isinstance(data, dict):
        return False, "Erro: Dados inválidos.", 400
        
    try:
        if db.session.execute(select(Business).where(Business.cnpj == data.get("cnpj"))).scalar_one_or_none():
            return False, "Erro: CNPJ já registrado.", 400

        # Extrai relacionamentos
        addresses_data = data.pop("addresses", [])
        photos_urls = data.pop("photos", []) # Espera lista de strings (URLs) ou dicts
        owners_ids = data.pop("owners", []) # Espera lista de IDs
        types_ids = data.pop("business_types", []) # Espera lista de IDs
        
        new_business = Business(**data)
        
        # Associação de Relacionamentos
        for addr in addresses_data:
            new_business.addresses.append(Address(**addr))
            
        for photo in photos_urls:
            if isinstance(photo, dict):
                new_business.photos.append(Photo(**photo))
            else:
                new_business.photos.append(Photo(url=photo))
                
        if owners_ids:
            owners = db.session.execute(select(User).where(User.id.in_(owners_ids))).scalars().all()
            new_business.owners.extend(owners)
            
        if types_ids:
            b_types = db.session.execute(select(BusinessType).where(BusinessType.id.in_(types_ids))).scalars().all()
            new_business.business_types.extend(b_types)

        db.session.add(new_business)
        db.session.commit()
        return True, "Negócio criado com sucesso.", 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao criar negócio: {str(e)}", 500

def get_business(business_id: int) -> Optional[Business]:
    stmt = select(Business).where(Business.id == business_id, Business.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()

def update_business(business_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    business = get_business(business_id)
    if not business:
        return False, "Negócio não encontrado ou inativo.", 404
        
    try:
        # Atualiza dados primitivos
        for key, value in data.items():
            if hasattr(business, key) and key not in ["id", "addresses", "photos", "owners", "business_types"]:
                setattr(business, key, value)
                
        # Atualização dinâmica de relacionamentos (substituição completa)
        if "addresses" in data:
            business.addresses.clear()
            for addr in data["addresses"]:
                business.addresses.append(Address(**addr))
                
        if "photos" in data:
            business.photos.clear()
            for photo in data["photos"]:
                p_data = photo if isinstance(photo, dict) else {"url": photo}
                business.photos.append(Photo(**p_data))
                
        if "owners" in data:
            business.owners.clear()
            owners = db.session.execute(select(User).where(User.id.in_(data["owners"]))).scalars().all()
            business.owners.extend(owners)
            
        if "business_types" in data:
            business.business_types.clear()
            b_types = db.session.execute(select(BusinessType).where(BusinessType.id.in_(data["business_types"]))).scalars().all()
            business.business_types.extend(b_types)
                
        db.session.commit()
        return True, "Negócio atualizado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar negócio: {str(e)}", 500

def delete_business(business_id: int) -> Tuple[bool, str, int]:
    business = get_business(business_id)
    if not business:
        return False, "Negócio não encontrado.", 404
        
    try:
        # Soft delete para negócio (Note que is_active é um booleano real aqui)
        business.is_active = False 
        db.session.commit()
        return True, "Negócio desativado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao desativar negócio: {str(e)}", 500

def get_all_businesses() -> List[Business]:
    stmt = select(Business).where(Business.is_active == True)
    return list(db.session.execute(stmt).scalars().all())

# ==========================================================
# GERENCIAMENTO DE AUTENTICAÇÃO
# ==========================================================

def login(email: str, password: str, expected_role: str) -> Tuple[bool, str, int, Optional[User]]:
    """Autentica validando senha, role, e se a conta está ativa."""
    try:
        stmt = select(User).join(Role).where(
            User.email == email, 
            Role.name == expected_role,
            User.is_active == True
        )
        user = db.session.execute(stmt).scalar_one_or_none()
        
        if not user:
            return False, "Usuário inativo, não encontrado ou papel incorreto.", 404, None
            
        if not check_password_hash(user.password, password):
            return False, "Credenciais inválidas.", 401, None
            
        return True, "Login bem-sucedido.", 200, user
        
    except SQLAlchemyError as e:
        return False, f"Erro no servidor: {str(e)}", 500, None