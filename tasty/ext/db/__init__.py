from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)

def register_models():
    """
    Importa todos os modulos que definem modelos para que sejam registrados
    no metadata do SQLAlchemy antes de operacoes como create_all().
    """
    import tasty.models
    ''' 
    import tasty.models.user
    import tasty.models.role
    import tasty.models.level
    import tasty.models.address
    import tasty.models.city
    import tasty.models.business
    import tasty.models.business_owner
    import tasty.models.business_type
    import tasty.models.photo
    import tasty.models.business_has_type
    import tasty.models.preference
    '''