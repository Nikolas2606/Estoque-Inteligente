"""
Application Factory do Sistema de Estoque Inteligente.

Padrão Flask recomendado para modularidade e testabilidade.
Inicializa extensões, registra blueprints e configura o app.
"""
import os
import logging

from flask import Flask

from config import config_map
from app.extensions import db, login_manager


def create_app(config_name=None):
    """
    Cria e configura a instância Flask.

    Args:
        config_name: 'development', 'production' ou 'testing'.
                     Se None, usa FLASK_ENV do ambiente.
    """
    app = Flask(__name__)

    # Determinar configuração
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config_map.get(config_name, config_map['development']))

    # Logging
    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    app.logger.info(f'Iniciando aplicação em modo: {config_name}')

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    from app.extensions import csrf
    csrf.init_app(app)

    # User loader para Flask-Login
    from app.models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # Registrar Blueprints
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.web import web_bp
    app.register_blueprint(web_bp)

    from app.api import api_bp
    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)

    # Criar tabelas (desenvolvimento/primeira execução)
    with app.app_context():
        db.create_all()
        app.logger.info('Tabelas do banco de dados verificadas/criadas.')

    # Context processor global: disponibilizar dados em todos os templates
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'Estoque Inteligente'
        }

    # Handler de erro 403 (Acesso Negado)
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    # Handler de erro 404 (Página Não Encontrada)
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    # Handler de erro 500 (Erro Interno)
    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
