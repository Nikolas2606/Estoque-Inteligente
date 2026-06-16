"""
Modelos SQLAlchemy do Sistema de Estoque Inteligente.

Define todas as tabelas do banco de dados:
- Usuario: Autenticação e controle de acesso
- Produto: Cadastro de produtos do estoque
- Posicao: Localizações físicas no estoque
- Ocupacao: Relacionamento Produto <-> Posição (M:N com quantidade)
- Historico: Auditoria de todas as movimentações
"""
import re
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# ============================================================
# MODELO: USUARIO
# ============================================================
class Usuario(UserMixin, db.Model):
    """Usuário do sistema com autenticação e role-based access."""

    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='vendedor')
    data_criacao = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    # Relacionamentos
    historicos = db.relationship(
        'Historico', backref='usuario', lazy='dynamic'
    )

    def set_password(self, password):
        """Gera hash seguro da senha usando werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_role(role):
        """Valida que o role é um dos valores permitidos."""
        return role in ('gerente', 'vendedor')

    def is_gerente(self):
        """Verifica se o usuário tem role de gerente."""
        return self.role == 'gerente'

    def __repr__(self):
        return f'<Usuario {self.username} ({self.role})>'


# ============================================================
# MODELO: PRODUTO
# ============================================================
class Produto(db.Model):
    """Produto cadastrado no estoque."""

    __tablename__ = 'produto'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(
        db.String(150), nullable=False, index=True
    )
    marca = db.Column(db.String(100), default='')
    tamanho = db.Column(db.String(50), default='')
    descricao = db.Column(db.Text, default='')
    url_imagem = db.Column(db.String(500), default='')
    data_criacao = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    # Relacionamentos (cascade delete)
    ocupacoes = db.relationship(
        'Ocupacao', backref='produto', lazy='joined',
        cascade='all, delete-orphan'
    )
    historicos = db.relationship(
        'Historico', backref='produto', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def total_estoque(self):
        """Calcula o total de unidades em todas as posições."""
        return sum(o.quantidade for o in self.ocupacoes)

    @staticmethod
    def validate_nome(nome):
        """Valida nome do produto: 3-150 caracteres, obrigatório."""
        if not nome or len(nome.strip()) < 3:
            return False, "Nome deve ter entre 3 e 150 caracteres."
        if len(nome.strip()) > 150:
            return False, "Nome deve ter no máximo 150 caracteres."
        return True, ""

    @staticmethod
    def validate_url_imagem(url):
        """Valida path da imagem: evita path traversal."""
        if not url:
            return True, ""
        if '..' in url or url.startswith('/') or url.startswith('\\'):
            return False, "Caminho de imagem inválido."
        return True, ""

    def to_dict(self):
        """Serializa o produto para resposta JSON (API Alexa)."""
        localizacoes = []
        total_quantidade = 0

        for ocupacao in self.ocupacoes:
            if ocupacao.quantidade > 0:
                localizacoes.append({
                    'posicao': ocupacao.posicao.codigo,
                    'quantidade': ocupacao.quantidade,
                    'descricao': ocupacao.posicao.descricao or ''
                })
                total_quantidade += ocupacao.quantidade

        return {
            'id': self.id,
            'nome': self.nome,
            'marca': self.marca,
            'tamanho': self.tamanho,
            'url_imagem': self.url_imagem,
            'total_quantidade': total_quantidade,
            'localizacoes': localizacoes
        }

    def __repr__(self):
        return f'<Produto {self.nome}>'


# ============================================================
# MODELO: POSICAO
# ============================================================
class Posicao(db.Model):
    """Posição física no estoque (corredor + número)."""

    __tablename__ = 'posicao'

    # Regex para validação do código: Letra + 1 ou 2 dígitos
    CODIGO_REGEX = re.compile(r'^[A-Z]\d{1,2}$')

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(
        db.String(10), unique=True, nullable=False, index=True
    )
    descricao = db.Column(db.String(200), default='')
    ativa = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relacionamentos
    ocupacoes = db.relationship(
        'Ocupacao', backref='posicao', lazy='joined',
        cascade='all, delete-orphan'
    )
    historicos = db.relationship(
        'Historico', backref='posicao', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @classmethod
    def validate_codigo(cls, codigo):
        """Valida formato do código: ^[A-Z]\\d{1,2}$ (ex: A1, B12, Z99)."""
        if not codigo:
            return False, "Código da posição é obrigatório."
        if not cls.CODIGO_REGEX.match(codigo.upper()):
            return False, "Código deve seguir o formato: Letra + Número (ex: A1, B12)."
        return True, ""

    def __repr__(self):
        return f'<Posicao {self.codigo}>'


# ============================================================
# MODELO: OCUPACAO (Relacionamento M:N com quantidade)
# ============================================================
class Ocupacao(db.Model):
    """Relaciona um produto a uma posição com quantidade."""

    __tablename__ = 'ocupacao'

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(
        db.Integer, db.ForeignKey('produto.id'), nullable=False
    )
    posicao_id = db.Column(
        db.Integer, db.ForeignKey('posicao.id'), nullable=False
    )
    quantidade = db.Column(db.Integer, default=0, nullable=False)
    data_atualizacao = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Constraint: Combinação (produto_id, posicao_id) deve ser única
    __table_args__ = (
        db.UniqueConstraint(
            'produto_id', 'posicao_id', name='uq_produto_posicao'
        ),
    )

    @staticmethod
    def validate_quantidade(quantidade):
        """Valida quantidade: 0-999, nunca negativa."""
        if quantidade is None:
            return False, "Quantidade é obrigatória."
        if not isinstance(quantidade, int):
            return False, "Quantidade deve ser um número inteiro."
        if quantidade < 0:
            return False, "Quantidade não pode ser negativa."
        if quantidade > 999:
            return False, "Quantidade máxima é 999 unidades."
        return True, ""

    def __repr__(self):
        return (
            f'<Ocupacao Produto={self.produto_id} '
            f'Posicao={self.posicao_id} Qtd={self.quantidade}>'
        )


# ============================================================
# MODELO: HISTORICO (Auditoria de Movimentações)
# ============================================================
class Historico(db.Model):
    """Registro de auditoria para todas as movimentações de estoque."""

    __tablename__ = 'historico'

    TIPOS_VALIDOS = ('entrada', 'saida', 'transferencia')

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(
        db.Integer, db.ForeignKey('produto.id'), nullable=False
    )
    usuario_id = db.Column(
        db.Integer, db.ForeignKey('usuario.id'), nullable=False
    )
    tipo = db.Column(db.String(20), nullable=False)
    posicao_id = db.Column(
        db.Integer, db.ForeignKey('posicao.id'), nullable=False
    )
    quantidade_movimentada = db.Column(db.Integer, nullable=False)
    data_hora = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        index=True
    )
    observacao = db.Column(db.Text, default='')

    @classmethod
    def validate_tipo(cls, tipo):
        """Valida que o tipo é entrada, saida ou transferencia."""
        if tipo not in cls.TIPOS_VALIDOS:
            return False, f"Tipo deve ser: {', '.join(cls.TIPOS_VALIDOS)}."
        return True, ""

    @staticmethod
    def validate_quantidade_movimentada(quantidade):
        """Valida quantidade movimentada: 1-999."""
        if quantidade is None or quantidade < 1:
            return False, "Quantidade movimentada deve ser no mínimo 1."
        if quantidade > 999:
            return False, "Quantidade movimentada máxima é 999."
        return True, ""

    def __repr__(self):
        return (
            f'<Historico {self.tipo} Produto={self.produto_id} '
            f'Qtd={self.quantidade_movimentada}>'
        )
