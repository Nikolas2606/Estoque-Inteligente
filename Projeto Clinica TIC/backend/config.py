"""
Configurações centralizadas do Sistema de Estoque Inteligente.
Carrega valores do arquivo .env para portabilidade entre ambientes.
"""
import os
from dotenv import load_dotenv

# Carrega variáveis do .env na raiz do projeto
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))


class Config:
    """Configuração base compartilhada por todos os ambientes."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-padrao-insegura-trocar')

    # SQLAlchemy / MariaDB
    DB_USER = os.environ.get('DB_USER', 'estoque_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'estoque_password_123')
    DB_HOST = os.environ.get('DB_HOST', 'db')  # Nome do serviço Docker
    DB_NAME = os.environ.get('DB_NAME', 'estoque_db')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MQTT (Eclipse Mosquitto)
    MQTT_BROKER_URL = os.environ.get('MQTT_BROKER_HOST', 'broker')
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT', 1883))
    MQTT_KEEPALIVE = 60
    MQTT_TLS_ENABLED = False

    # API Alexa
    ALEXA_API_KEY = os.environ.get('ALEXA_API_KEY', 'alexa_api_key_trocar')

    # Upload de Imagens
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'fotos'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max

    # Paginação
    PRODUTOS_POR_PAGINA = 20
    HISTORICO_POR_PAGINA = 20


class DevelopmentConfig(Config):
    """Configuração para desenvolvimento local."""

    DEBUG = True
    # Usar SQLite local para desenvolvimento sem Docker
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'estoque_dev.db')
    )
    # MQTT desabilitado em dev local (pode não ter broker)
    MQTT_ENABLED = os.environ.get('MQTT_ENABLED', 'false').lower() == 'true'


class ProductionConfig(Config):
    """Configuração para produção (Docker)."""

    DEBUG = False
    MQTT_ENABLED = True


class TestingConfig(Config):
    """Configuração para testes automatizados."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MQTT_ENABLED = False


# Mapa de configurações por ambiente
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
