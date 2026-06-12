from typing import Tuple, List
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from tasty.ext.db import db
from tasty.models import BusinessSwipe, Business, User
from tasty.services.location_service import get_distance_between_user_and_business

def swipe_business(
    user_id: int,
    business_id: int,
    liked: bool,
    super_like: bool = False
) -> Tuple[bool, str, int]:
    """Registra ou atualiza uma interação de swipe do usuário com um estabelecimento."""
    try:
        business_stmt = select(Business.id).where(Business.id == business_id, Business.is_active == True)
        if not db.session.execute(business_stmt).scalar_one_or_none():
            return False, "Estabelecimento não encontrado ou inativo.", 404

        user_stmt = select(User.id).where(User.id == user_id, User.is_active == True)
        if not db.session.execute(user_stmt).scalar_one_or_none():
            return False, "Usuário não encontrado ou inativo.", 404

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
    Retorna estabelecimentos não avaliados ordenados por um score misto:
    80% Afinidade Gastronômica (Quantidade de tags em comum)
    20% Proximidade Geográfica (Mais perto do endereço principal do cliente)
    """
    try:
        user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user or not user.addresses or not user.preferences:
            stmt = select(Business).outerjoin(BusinessSwipe, (Business.id == BusinessSwipe.business_id) & (BusinessSwipe.user_id == user_id)).where(Business.is_active == True, BusinessSwipe.id.is_(None)).limit(limit)
            return list(db.session.execute(stmt).scalars().all())

        user_addr = user.addresses[0]
        user_lat, user_lon = user_addr.latitude, user_addr.longitude
        user_pref_ids = [p.id for p in user.preferences]

        stmt_candidates = (
            select(Business)
            .outerjoin(BusinessSwipe, (Business.id == BusinessSwipe.business_id) & (BusinessSwipe.user_id == user_id))
            .where(Business.is_active == True, BusinessSwipe.id.is_(None))
        )
        candidates = db.session.execute(stmt_candidates).scalars().all()

        scored_candidates = []
        for b in candidates:
            b_type_ids = [t.id for t in b.business_types]
            matches = set(user_pref_ids).intersection(set(b_type_ids))
            
            tag_score = len(matches) / len(user_pref_ids) if user_pref_ids else 0

            dist = get_distance_between_user_and_business(user_id, b.id)
            if dist is None:
                dist = 50.0
            
            distance_score = max(0, (30.0 - dist) / 30.0)

            final_score = (0.8 * tag_score) + (0.2 * distance_score)
            
            b.distance_km = round(dist, 1) if dist is not None else "--"
            scored_candidates.append((final_score, b))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_candidates[:limit]]

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
        stmt = delete(BusinessSwipe).where(BusinessSwipe.user_id == user_id)
        db.session.execute(stmt)
        db.session.commit()

        return True, "Histórico de swipes zerado com sucesso.", 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao resetar histórico: {str(e)}", 500