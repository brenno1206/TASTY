from sqlalchemy import select, func
from tasty.ext.db import db
from tasty.models import Business, BusinessSwipe, User, Role

def get_restaurant_metrics(business_id: int) -> dict:
    """Calcula estatísticas agregadas de interações para um restaurante específico."""
    total_views = db.session.execute(
        select(func.count(BusinessSwipe.id)).where(BusinessSwipe.business_id == business_id)
    ).scalar() or 0

    total_matches = db.session.execute(
        select(func.count(BusinessSwipe.id)).where(
            BusinessSwipe.business_id == business_id,
            BusinessSwipe.liked == True
        )
    ).scalar() or 0

    super_likes = db.session.execute(
        select(func.count(BusinessSwipe.id)).where(
            BusinessSwipe.business_id == business_id,
            BusinessSwipe.super_like == True
        )
    ).scalar() or 0

    conversion_rate = round((total_matches / total_views) * 100, 1) if total_views > 0 else 0.0

    return {
        "business_id": business_id,
        "total_views": total_views,
        "total_matches": total_matches,
        "super_likes": super_likes,
        "conversion_rate": conversion_rate
    }


def get_owner_portfolio_metrics(owner_id: int) -> dict:
    """Consolida os dados de telemetria de todas as filiais de uma conta empresarial."""
    stmt_businesses = select(Business.id).join(Business.owners).where(User.id == owner_id, Business.is_active == True)
    business_ids = db.session.execute(stmt_businesses).scalars().all()

    if not business_ids:
        return {"total_views": 0, "total_matches": 0, "avg_conversion_rate": 0.0, "active_stores": 0}

    total_views = db.session.execute(
        select(func.count(BusinessSwipe.id)).where(BusinessSwipe.business_id.in_(business_ids))
    ).scalar() or 0

    total_matches = db.session.execute(
        select(func.count(BusinessSwipe.id)).where(
            BusinessSwipe.business_id.in_(business_ids),
            BusinessSwipe.liked == True
        )
    ).scalar() or 0

    avg_conversion = round((total_matches / total_views) * 100, 1) if total_views > 0 else 0.0

    return {
        "total_views": total_views,
        "total_matches": total_matches,
        "avg_conversion_rate": avg_conversion,
        "active_stores": len(business_ids)
    }

def get_global_metrics() -> dict:
    """Calcula a volumetria total da plataforma para o Dashboard do Administrador."""
    
    total_clients = db.session.execute(
        select(func.count(User.id))
        .join(Role)
        .where(Role.name == "client", User.is_active == True)
    ).scalar() or 0

    total_businesses = db.session.execute(
        select(func.count(Business.id)).where(Business.is_active == True)
    ).scalar() or 0

    total_swipes = db.session.execute(
        select(func.count(BusinessSwipe.id))
    ).scalar() or 0

    return {
        "total_clients": total_clients,
        "total_businesses": total_businesses,
        "total_swipes": total_swipes
    }