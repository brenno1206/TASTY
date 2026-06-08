from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, delete
from tasty.models import BusinessType
from tasty.ext.db import db

def create_business_type(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Cria uma nova categoria gastronômica/tipo de estabelecimento."""
    if not data or not isinstance(data, dict):
        return False, "Dados inválidos.", 400
        
    try:
        # Validação de unicidade simples baseada no nome
        name = data.get("name")
        if not name:
            return False, "O nome da categoria é obrigatório.", 400
            
        stmt = select(BusinessType).where(BusinessType.name.ilike(name))
        if db.session.execute(stmt).scalar_one_or_none():
            return False, f"A categoria '{name}' já existe.", 400
            
        new_type = BusinessType(
            name=name,
            emoji=data.get("emoji"),
            description=data.get("description")
        )
        
        db.session.add(new_type)
        db.session.commit()
        return True, "Categoria criada com sucesso.", 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro interno do banco de dados: {str(e)}", 500


def get_business_type(type_id: int) -> Optional[BusinessType]:
    """Retorna uma categoria específica pelo ID."""
    return db.session.execute(select(BusinessType).where(BusinessType.id == type_id)).scalar_one_or_none()


def update_business_type(type_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Atualiza os dados de uma categoria existente."""
    if not data or not isinstance(data, dict):
        return False, "Dados inválidos.", 400
        
    b_type = get_business_type(type_id)
    if not b_type:
        return False, "Categoria não encontrada.", 404
        
    try:
        if "name" in data:
            # Verifica se o novo nome não colide com outra categoria existente
            new_name = data["name"]
            stmt = select(BusinessType).where(BusinessType.name.ilike(new_name), BusinessType.id != type_id)
            if db.session.execute(stmt).scalar_one_or_none():
                return False, "Já existe outra categoria com este nome.", 400
            b_type.name = new_name
            
        if "emoji" in data:
            b_type.emoji = data["emoji"]
            
        if "description" in data:
            b_type.description = data["description"]
            
        db.session.commit()
        return True, "Categoria atualizada com sucesso.", 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar categoria: {str(e)}", 500


def delete_business_type(type_id: int) -> Tuple[bool, str, int]:
    """Exclui fisicamente uma categoria. Requer cuidado pois afeta preferências de usuários e restaurantes."""
    b_type = get_business_type(type_id)
    if not b_type:
        return False, "Categoria não encontrada.", 404
        
    try:
        # A exclusão no banco resolverá as tabelas associativas N:N (business_has_type, preferences)
        # graças ao 'ondelete="CASCADE"' configurado nessas tabelas intermediárias.
        db.session.delete(b_type)
        db.session.commit()
        return True, "Categoria excluída com sucesso.", 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao excluir categoria: {str(e)}", 500


def get_all_business_types() -> List[BusinessType]:
    """Retorna todas as categorias disponíveis para listagem no app."""
    # Ordenado alfabeticamente para melhor UX no front-end
    stmt = select(BusinessType).order_by(BusinessType.name)
    return list(db.session.execute(stmt).scalars().all())