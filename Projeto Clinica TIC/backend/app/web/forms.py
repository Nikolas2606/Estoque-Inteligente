"""
Formulários WTForms para as telas web.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, TextAreaField,
    SelectField, RadioField, SubmitField,
    BooleanField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, ValidationError
)
from flask_wtf.file import FileField, FileAllowed


class MovimentacaoForm(FlaskForm):
    """Formulário de movimentação de estoque."""

    tipo_movimento = RadioField(
        'Tipo de Movimento',
        choices=[
            ('entrada', 'Entrada'),
            ('saida', 'Saída'),
            ('transferencia', 'Transferência')
        ],
        validators=[DataRequired(message='Selecione o tipo de movimento.')]
    )

    produto_id = SelectField(
        'Produto',
        coerce=int,
        validators=[DataRequired(message='Selecione um produto.')]
    )

    posicao_origem_id = SelectField(
        'Posição Origem',
        coerce=int,
        validators=[DataRequired(message='Selecione a posição de origem.')]
    )

    posicao_destino_id = SelectField(
        'Posição Destino',
        coerce=int,
        validators=[Optional()]
    )

    quantidade = IntegerField(
        'Quantidade',
        validators=[
            DataRequired(message='Informe a quantidade.'),
            NumberRange(
                min=1, max=999,
                message='Quantidade deve ser entre 1 e 999.'
            )
        ],
        render_kw={
            'placeholder': 'Quantidade',
            'class': 'form-control',
            'min': '1',
            'max': '999',
            'type': 'number'
        }
    )

    observacao = TextAreaField(
        'Observação',
        validators=[
            Optional(),
            Length(max=500, message='Observação deve ter no máximo 500 caracteres.')
        ],
        render_kw={
            'placeholder': 'Notas adicionais (opcional)',
            'class': 'form-control',
            'rows': '3',
            'maxlength': '500'
        }
    )

    submit = SubmitField(
        'Registrar Movimento',
        render_kw={'class': 'btn btn-primary btn-lg'}
    )


class ProdutoForm(FlaskForm):
    """Formulário para cadastro e edição de produtos."""

    nome = StringField(
        'Nome do Produto',
        validators=[
            DataRequired(message='Nome é obrigatório.'),
            Length(
                min=3, max=150,
                message='Nome deve ter entre 3 e 150 caracteres.'
            )
        ],
        render_kw={
            'placeholder': 'Nome do produto',
            'class': 'form-control',
            'minlength': '3',
            'maxlength': '150'
        }
    )

    marca = StringField(
        'Marca',
        validators=[
            Optional(),
            Length(max=100, message='Marca deve ter no máximo 100 caracteres.')
        ],
        render_kw={
            'placeholder': 'Marca do produto',
            'class': 'form-control',
            'maxlength': '100'
        }
    )

    tamanho = StringField(
        'Tamanho',
        validators=[
            Optional(),
            Length(max=50, message='Tamanho deve ter no máximo 50 caracteres.')
        ],
        render_kw={
            'placeholder': 'Ex: P, M, G, 500ml',
            'class': 'form-control',
            'maxlength': '50'
        }
    )

    descricao = TextAreaField(
        'Descrição',
        validators=[
            Optional(),
            Length(max=1000, message='Descrição deve ter no máximo 1000 caracteres.')
        ],
        render_kw={
            'placeholder': 'Descrição do produto (opcional)',
            'class': 'form-control',
            'rows': '3',
            'maxlength': '1000'
        }
    )

    imagem = FileField(
        'Imagem do Produto',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens (JPG, PNG, GIF) são permitidas.')
        ],
        render_kw={'class': 'form-control'}
    )

    submit = SubmitField(
        'Salvar Produto',
        render_kw={'class': 'btn btn-primary btn-lg'}
    )


class PosicaoForm(FlaskForm):
    """Formulário para cadastro e edição de posições."""

    codigo = StringField(
        'Código da Posição',
        validators=[
            DataRequired(message='Código é obrigatório.'),
            Length(max=10, message='Código deve ter no máximo 10 caracteres.')
        ],
        render_kw={
            'placeholder': 'Ex: A1, B12, Z99',
            'class': 'form-control',
            'maxlength': '10',
            'style': 'text-transform: uppercase;'
        }
    )

    descricao = StringField(
        'Descrição',
        validators=[
            Optional(),
            Length(max=200, message='Descrição deve ter no máximo 200 caracteres.')
        ],
        render_kw={
            'placeholder': 'Ex: Prateleira superior do Corredor A',
            'class': 'form-control',
            'maxlength': '200'
        }
    )

    submit = SubmitField(
        'Salvar Posição',
        render_kw={'class': 'btn btn-primary btn-lg'}
    )

    def validate_codigo(self, field):
        """Validação customizada do formato do código."""
        import re
        codigo = field.data.strip().upper()
        if not re.match(r'^[A-Z]\d{1,2}$', codigo):
            raise ValidationError(
                'Código deve seguir o formato: Letra + Número (ex: A1, B12).'
            )


class UsuarioForm(FlaskForm):
    """Formulário para cadastro e edição de usuários (gerente only)."""

    username = StringField(
        'Nome de Usuário',
        validators=[
            DataRequired(message='Usuário é obrigatório.'),
            Length(
                min=3, max=50,
                message='Usuário deve ter entre 3 e 50 caracteres.'
            )
        ],
        render_kw={
            'placeholder': 'Nome de usuário',
            'class': 'form-control',
            'minlength': '3',
            'maxlength': '50'
        }
    )

    password = StringField(
        'Senha',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Deixe em branco para manter a senha atual',
            'class': 'form-control',
            'type': 'password',
            'minlength': '4'
        }
    )

    role = SelectField(
        'Função',
        choices=[
            ('vendedor', 'Vendedor'),
            ('gerente', 'Gerente')
        ],
        validators=[DataRequired(message='Selecione a função.')],
        render_kw={'class': 'form-select'}
    )

    ativo = BooleanField(
        'Usuário Ativo',
        default=True,
        render_kw={'class': 'form-check-input'}
    )

    submit = SubmitField(
        'Salvar Usuário',
        render_kw={'class': 'btn btn-primary btn-lg'}
    )
