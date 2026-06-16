"""
Decorators customizados para controle de acesso.
"""
from functools import wraps
from flask import abort
from flask_login import current_user


def gerente_required(f):
    """
    Decorator que restringe acesso a usuários com role='gerente'.
    Deve ser usado APÓS @login_required.

    Uso:
        @route('/gestao')
        @login_required
        @gerente_required
        def gestao():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'gerente':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
