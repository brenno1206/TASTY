from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from tasty.models import Business, Address, Photo, User, BusinessType
from tasty.ext.db import db

# ==========================================================
# GERENCIAMENTO DE NEGÓCIO (BUSINESS)
# ==========================================================

def create_business(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Cria um novo estabelecimento com seus relacionamentos de forma segura."""
    if not data or not isinstance(data, dict):
        return False, "Erro: Dados inválidos fornecidos no payload.", 400
        
    payload = data.copy()
        
    try:
        # Validação de unicidade do CNPJ (Regra de Negócio Crítica)
        cnpj = payload.get("cnpj")
        if not cnpj:
            return False, "Erro: CNPJ é obrigatório.", 400
            
        if db.session.execute(select(Business).where(Business.cnpj == cnpj)).scalar_one_or_none():
            return False, "Erro: CNPJ já registrado no sistema.", 400

        # Extração de relacionamentos aninhados para não quebrar a instanciação
        addresses_data = payload.pop("addresses", [])
        photos_urls = payload.pop("photos", []) 
        owners_ids = payload.pop("owners", []) 
        types_ids = payload.pop("business_types", []) 
        
        # Instanciação estrita da entidade principal
        new_business = Business(
            corporate_name=payload.get("corporate_name"),
            trade_name=payload.get("trade_name"),
            cnpj=cnpj,
            description=payload.get("description"),
            opening_time=payload.get("opening_time"),
            closing_time=payload.get("closing_time")
        )
        
        # Associação de Endereços com suporte à geolocalização
        for addr in addresses_data:
            new_business.addresses.append(
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
            
        # Associação de Fotos (Aceita lista de strings/urls ou dicionários mapeados)
        for photo in photos_urls:
            if isinstance(photo, dict):
                new_business.photos.append(
                    Photo(
                        url=photo.get("url"), 
                        description=photo.get("description")
                    )
                )
            else:
                new_business.photos.append(Photo(url=photo))
                
        # Resolução e Associação de N:N (Donos/Owners)
        if owners_ids:
            owners = db.session.execute(
                select(User).where(User.id.in_(owners_ids), User.is_active == True)
            ).scalars().all()
            new_business.owners.extend(owners)
            
        # Resolução e Associação de N:N (Tipos de Estabelecimento)
        if types_ids:
            b_types = db.session.execute(
                select(BusinessType).where(BusinessType.id.in_(types_ids))
            ).scalars().all()
            new_business.business_types.extend(b_types)

        db.session.add(new_business)
        db.session.commit()
        return True, "Estabelecimento criado com sucesso.", 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro interno do banco de dados: {str(e)}", 500


def get_business(business_id: int) -> Optional[Business]:
    """Retorna um estabelecimento pelo ID apenas se estiver ativo."""
    stmt = select(Business).where(Business.id == business_id, Business.is_active == True)
    return db.session.execute(stmt).scalar_one_or_none()


def update_business(business_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Atualiza atributos primitivos e substitui relacionamentos aninhados em cascata."""
    if not data or not isinstance(data, dict):
        return False, "Erro: Dados inválidos.", 400

    business = get_business(business_id)
    if not business:
        return False, "Estabelecimento não encontrado ou inativo.", 404
        
    try:
        # Lista branca de campos permitidos para atualização genérica
        # CNPJ não deve ser alterável livremente, mas caso seja requisito no futuro, 
        # será necessária uma validação de unicidade extra aqui.
        allowed_fields = {
            "corporate_name", "trade_name", "description", 
            "opening_time", "closing_time"
        }
        
        for key in allowed_fields:
            if key in data:
                setattr(business, key, data[key])
                
        # Atualização de Endereços (limpa os antigos e injeta os novos, acionando delete-orphan)
        if "addresses" in data:
            business.addresses.clear()
            for addr in data["addresses"]:
                business.addresses.append(
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
                
        # Atualização de Fotos
        if "photos" in data:
            business.photos.clear()
            for photo in data["photos"]:
                if isinstance(photo, dict):
                    business.photos.append(
                        Photo(
                            url=photo.get("url"), 
                            description=photo.get("description")
                        )
                    )
                else:
                    business.photos.append(Photo(url=photo))
                
        # Atualização de Donos (Owners)
        if "owners" in data:
            business.owners.clear()
            if data["owners"]:
                owners = db.session.execute(
                    select(User).where(User.id.in_(data["owners"]), User.is_active == True)
                ).scalars().all()
                business.owners.extend(owners)
            
        # Atualização de Categorias (Business Types)
        if "business_types" in data:
            business.business_types.clear()
            if data["business_types"]:
                b_types = db.session.execute(
                    select(BusinessType).where(BusinessType.id.in_(data["business_types"]))
                ).scalars().all()
                business.business_types.extend(b_types)
                
        db.session.commit()
        return True, "Estabelecimento atualizado com sucesso.", 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar estabelecimento: {str(e)}", 500


def delete_business(business_id: int) -> Tuple[bool, str, int]:
    """Aplica o soft-delete no estabelecimento."""
    business = get_business(business_id)
    if not business:
        return False, "Estabelecimento não encontrado.", 404
        
    try:
        business.is_active = False 
        db.session.commit()
        return True, "Estabelecimento desativado com sucesso.", 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao desativar estabelecimento: {str(e)}", 500


def get_all_businesses() -> List[Business]:
    """Retorna todos os estabelecimentos ativos na plataforma."""
    stmt = select(Business).where(Business.is_active == True)
    return list(db.session.execute(stmt).scalars().all())