from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from tasty.models import City
from tasty.ext.db import db

def create_city(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Cadastra uma nova cidade garantindo que não haja duplicatas geográficas."""
    if not data or not isinstance(data, dict):
        return False, "Dados inválidos.", 400
        
    name = data.get("name")
    state = data.get("state")
    country = data.get("country", "Brasil") # Default para Brasil
    
    if not name:
        return False, "O nome da cidade é obrigatório.", 400
        
    try:
        # Busca exata usando a mesma tupla do Index criado no banco de dados
        stmt = select(City).where(
            City.name.ilike(name),
            City.state.ilike(state) if state else City.state.is_(None),
            City.country.ilike(country) if country else City.country.is_(None)
        )
        
        if db.session.execute(stmt).scalar_one_or_none():
            return False, f"A cidade {name} - {state} já está cadastrada.", 400
            
        new_city = City(
            name=name,
            state=state,
            country=country,
            region=data.get("region")
        )
        
        db.session.add(new_city)
        db.session.commit()
        return True, "Cidade cadastrada com sucesso.", 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro interno do banco de dados: {str(e)}", 500


def get_city(city_id: int) -> Optional[City]:
    """Retorna os dados de uma cidade específica."""
    return db.session.execute(select(City).where(City.id == city_id)).scalar_one_or_none()


def update_city(city_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Atualiza metadados da cidade."""
    city = get_city(city_id)
    if not city:
        return False, "Cidade não encontrada.", 404
        
    try:
        if "name" in data:
            city.name = data["name"]
        if "state" in data:
            city.state = data["state"]
        if "country" in data:
            city.country = data["country"]
        if "region" in data:
            city.region = data["region"]
            
        db.session.commit()
        return True, "Cidade atualizada com sucesso.", 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar cidade: {str(e)}", 500


def get_all_cities() -> List[City]:
    """Lista todas as cidades (útil para dropdowns de filtros)."""
    stmt = select(City).order_by(City.state, City.name)
    return list(db.session.execute(stmt).scalars().all())

# Nota: Normalmente não implementamos `delete_city` em um sistema em produção 
# caso ela já possua milhares de endereços atrelados, pois causaria orfandade de dados. 
# Caso o admin precise consertar um erro, o update_city resolve.