from typing import Tuple, List
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from tasty.ext.db import db
from tasty.models import BusinessSwipe, Business, User


def swipe_business(
    user_id: int,
    business_id: int,
    liked: bool,
    super_like: bool = False
) -> Tuple[bool, str, int]:
    """Registra ou atualiza uma interação de swipe do usuário com um estabelecimento."""
    try:
        # 1. Validação de pré-condição: Verifica se o estabelecimento existe e está ativo
        # Isso evita estourar erros brutos de Foreign Key Violation do PostgreSQL
        business_stmt = select(Business.id).where(Business.id == business_id, Business.is_active == True)
        if not db.session.execute(business_stmt).scalar_one_or_none():
            return False, "Estabelecimento não encontrado ou inativo.", 404

        # Validação de usuário
        user_stmt = select(User.id).where(User.id == user_id, User.is_active == True)
        if not db.session.execute(user_stmt).scalar_one_or_none():
            return False, "Usuário não encontrado ou inativo.", 404

        # 2. Busca ou atualiza o Swipe
        stmt = select(BusinessSwipe).where(
            BusinessSwipe.user_id == user_id,
            BusinessSwipe.business_id == business_id
        )
        swipe = db.session.execute(stmt).scalar_one_or_none()

        if swipe:
            swipe.liked = liked
            swipe.super_like = super_like
        else:
            swipe = BusinessSwipe(
                user_id=user_id,
                business_id=business_id,
                liked=liked,
                super_like=super_like
            )
            db.session.add(swipe)

        db.session.commit()
        return True, "Swipe registrado com sucesso.", 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro interno de banco de dados: {str(e)}", 500


def get_next_businesses_for_user(user_id: int, limit: int = 20) -> List[Business]:
    """
    Retorna restaurantes que o usuário ainda NÃO avaliou (swipe).
    Otimizado para usar LEFT JOIN ao invés de NOT IN (subquery),
    garantindo performance escalar no PostgreSQL.
    """
    try:
        stmt = (
            select(Business)
            .outerjoin(
                BusinessSwipe, 
                (Business.id == BusinessSwipe.business_id) & (BusinessSwipe.user_id == user_id)
            )
            .where(
                Business.is_active == True,
                BusinessSwipe.id.is_(None)  # Onde não houver match no JOIN, significa que não houve swipe
            )
            .limit(limit)
        )

        return list(db.session.execute(stmt).scalars().all())

    except SQLAlchemyError:
        return []


def get_liked_businesses(user_id: int) -> List[Business]:
    """Retorna os estabelecimentos que o usuário avaliou positivamente."""
    try:
        stmt = (
            select(Business)
            .join(BusinessSwipe, BusinessSwipe.business_id == Business.id)
            .where(
                BusinessSwipe.user_id == user_id,
                BusinessSwipe.liked == True,
                Business.is_active == True
            )
        )

        return list(db.session.execute(stmt).scalars().all())

    except SQLAlchemyError:
        return []


def get_disliked_businesses(user_id: int) -> List[Business]:
    """Retorna os estabelecimentos que o usuário avaliou negativamente."""
    try:
        stmt = (
            select(Business)
            .join(BusinessSwipe, BusinessSwipe.business_id == Business.id)
            .where(
                BusinessSwipe.user_id == user_id,
                BusinessSwipe.liked == False,
                Business.is_active == True
            )
        )

        return list(db.session.execute(stmt).scalars().all())

    except SQLAlchemyError:
        return []


def reset_user_swipes(user_id: int) -> Tuple[bool, str, int]:
    """
    Remove todo o histórico de interações do usuário.
    Otimizado para execução em lote nativa (Bulk Delete).
    """
    try:
        # Exclui diretamente no banco sem carregar objetos para a memória do Python
        stmt = delete(BusinessSwipe).where(BusinessSwipe.user_id == user_id)
        db.session.execute(stmt)
        db.session.commit()

        return True, "Histórico de swipes zerado com sucesso.", 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao resetar histórico: {str(e)}", 500