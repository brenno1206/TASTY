from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

def role_required(*allowed_roles):
    """
    Decorador para proteger rotas baseado na 'role' do usuário.
    Uso: @role_required('admin', 'client')
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request() 
            
            claims = get_jwt()
            user_role = claims.get('role')

            if user_role not in allowed_roles:
                return jsonify({"error": f"Acesso negado. Requer uma das seguintes permissões: {', '.join(allowed_roles)}"}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper