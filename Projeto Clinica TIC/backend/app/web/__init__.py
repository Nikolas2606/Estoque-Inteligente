"""
Blueprint Web - Rotas de interface Jinja2.
Dashboard, Movimentação, Histórico e CRUD.
"""
from flask import Blueprint

web_bp = Blueprint(
    'web', __name__,
    template_folder='../templates',
    static_folder='../static'
)

from app.web import routes  # noqa: E402, F401
