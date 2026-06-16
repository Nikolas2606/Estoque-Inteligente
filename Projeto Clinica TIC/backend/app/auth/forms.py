"""
Formulários de autenticação (WTForms).
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    """Formulário de login com validação de campos."""

    username = StringField(
        'Usuário',
        validators=[
            DataRequired(message='Usuário é obrigatório.'),
            Length(
                min=3, max=50,
                message='Usuário deve ter entre 3 e 50 caracteres.'
            )
        ],
        render_kw={
            'placeholder': 'Digite seu usuário',
            'autocomplete': 'username',
            'class': 'form-control',
            'minlength': '3',
            'maxlength': '50'
        }
    )

    password = PasswordField(
        'Senha',
        validators=[
            DataRequired(message='Senha é obrigatória.'),
            Length(
                min=4,
                message='Senha deve ter no mínimo 4 caracteres.'
            )
        ],
        render_kw={
            'placeholder': 'Digite sua senha',
            'autocomplete': 'current-password',
            'class': 'form-control',
            'minlength': '4'
        }
    )

    submit = SubmitField(
        'Entrar',
        render_kw={'class': 'btn btn-primary w-100 btn-lg'}
    )
