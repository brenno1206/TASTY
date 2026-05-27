from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)

def register_models():
    """
    Importa todos os modulos que definem modelos para que sejam registrados
    no metadata do SQLAlchemy antes de operacoes como create_all().
    """
    import tasty.models.user
    import tasty.models.role
    import tasty.models.level
    import tasty.models.address
    import tasty.models.city
    import tasty.models.business
    import tasty.models.businessowner
    import tasty.models.businesstype
    import tasty.models.photo
    import tasty.models.businesshastype
    import tasty.models.preference