from typing import Tuple, Optional, List
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from tasty.ext.db import db
from tasty.models import BusinessSwipe, Business, User


def swipe_business(
    user_id: int,
    business_id: int,
    liked: bool,
    super_like: bool = False
) -> Tuple[bool, str, int]:

    try:
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
        return False, str(e), 500

def get_next_businesses_for_user(user_id: int, limit: int = 20) -> List[Business]:
    """
    Retorna restaurantes que o usuário ainda NÃO deu swipe.
    """

    try:
        subquery = select(BusinessSwipe.business_id).where(
            BusinessSwipe.user_id == user_id
        )

        stmt = (
            select(Business)
            .where(
                Business.is_active == True,
                ~Business.id.in_(subquery)
            )
            .limit(limit)
        )

        return list(db.session.execute(stmt).scalars().all())

    except SQLAlchemyError:
        return []

def get_liked_businesses(user_id: int) -> List[Business]:
    try:
        stmt = (
            select(Business)
            .join(BusinessSwipe, BusinessSwipe.business_id == Business.id)
            .where(
                BusinessSwipe.user_id == user_id,
                BusinessSwipe.liked == True
            )
        )

        return list(db.session.execute(stmt).scalars().all())

    except SQLAlchemyError:
        return []

def get_disliked_businesses(user_id: int) -> List[Business]:
    try:
        stmt = (
            select(Business)
            .join(BusinessSwipe, BusinessSwipe.business_id == Business.id)
            .where(
                BusinessSwipe.user_id == user_id,
                BusinessSwipe.liked == False
            )
        )

        return list(db.session.execute(stmt).scalars().all())

    except SQLAlchemyError:
        return []

def reset_user_swipes(user_id: int) -> Tuple[bool, str, int]:
    try:
        stmt = select(BusinessSwipe).where(BusinessSwipe.user_id == user_id)
        swipes = db.session.execute(stmt).scalars().all()

        for s in swipes:
            db.session.delete(s)

        db.session.commit()

        return True, "Swipes resetados.", 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao resetar swipes: {str(e)}", 500