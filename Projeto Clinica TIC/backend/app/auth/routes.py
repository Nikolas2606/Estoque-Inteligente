"""
Rotas de autenticação: Login e Logout.
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.auth import auth_bp
from app.auth.forms import LoginForm
from app.models import Usuario


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET: Exibe formulário de login.
    POST: Valida credenciais e inicia sessão.
    """
    # Se já está logado, redireciona para dashboard
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        # Buscar usuário no banco
        usuario = Usuario.query.filter_by(username=username).first()

        # Validar: usuário existe, está ativo e senha correta
        if usuario and usuario.ativo and usuario.check_password(password):
            login_user(usuario)
            flash('Login realizado com sucesso!', 'success')

            # Redirecionar para a página que o usuário tentou acessar
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('web.dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Encerra a sessão do usuário e redireciona para login."""
    logout_user()
    flash('Sessão encerrada com sucesso.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/')
def index():
    """Rota raiz: redireciona para dashboard se logado, login caso contrário."""
    if current_user.is_authenticated:
        return redirect(url_for('web.dashboard'))
    return redirect(url_for('auth.login'))
