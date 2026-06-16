"""
Instâncias das extensões Flask.
Separadas do Application Factory para evitar imports circulares.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# ORM
db = SQLAlchemy()

# Autenticação
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'

# CSRF Global
csrf = CSRFProtect()
