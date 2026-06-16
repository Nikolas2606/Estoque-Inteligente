"""
Blueprint de Autenticação.
Gerencia login, logout e controle de sessão via Flask-Login.
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from app.auth import routes  # noqa: E402, F401
