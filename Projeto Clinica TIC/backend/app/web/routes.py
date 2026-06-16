"""
Rotas Web do Sistema de Estoque Inteligente.

Inclui Dashboard, Movimentação, Histórico e CRUD completo
de Produtos, Posições e Usuários.
"""
import csv
import io
from datetime import datetime, timezone

from flask import (
    render_template, redirect, url_for, flash,
    request, Response, current_app
)
import os
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

from app.web import web_bp
from app.web.decorators import gerente_required
from app.web.forms import (
    MovimentacaoForm, ProdutoForm, PosicaoForm, UsuarioForm
)
from app.extensions import db
from app.models import Produto, Posicao, Ocupacao, Historico, Usuario


# ============================================================
# DASHBOARD
# ============================================================
@web_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard de estoque com busca e paginação."""
    page = request.args.get('page', 1, type=int)
    busca = request.args.get('q', '', type=str).strip()
    per_page = current_app.config.get('PRODUTOS_POR_PAGINA', 20)

    # Query base: produtos ativos
    query = Produto.query.filter_by(ativo=True)

    # Filtro de busca por nome ou marca
    if busca and len(busca) >= 2:
        filtro = f'%{busca}%'
        query = query.filter(
            db.or_(
                Produto.nome.ilike(filtro),
                Produto.marca.ilike(filtro)
            )
        )

    # Ordenar por nome e paginar
    query = query.order_by(Produto.nome.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    produtos = pagination.items

    return render_template(
        'dashboard.html',
        produtos=produtos,
        pagination=pagination,
        busca=busca
    )


# ============================================================
# MOVIMENTAÇÃO DE ESTOQUE
# ============================================================
@web_bp.route('/gestao/movimentacao', methods=['GET', 'POST'])
@login_required
@gerente_required
def movimentacao():
    """Formulário de movimentação de estoque (Gerente only)."""
    form = MovimentacaoForm()

    # Carregar opções dinâmicas dos selects
    produtos_ativos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    posicoes_ativas = Posicao.query.filter_by(ativa=True).order_by(Posicao.codigo).all()

    form.produto_id.choices = [
        (p.id, f'{p.nome} ({p.marca})' if p.marca else p.nome)
        for p in produtos_ativos
    ]
    form.posicao_origem_id.choices = [
        (p.id, f'{p.codigo} - {p.descricao}' if p.descricao else p.codigo)
        for p in posicoes_ativas
    ]
    form.posicao_destino_id.choices = [
        (0, '-- Selecione --')
    ] + [
        (p.id, f'{p.codigo} - {p.descricao}' if p.descricao else p.codigo)
        for p in posicoes_ativas
    ]

    if form.validate_on_submit():
        tipo = form.tipo_movimento.data
        produto_id = form.produto_id.data
        posicao_origem_id = form.posicao_origem_id.data
        quantidade = form.quantidade.data
        observacao = (form.observacao.data or '').strip()[:500]

        # Validar produto
        produto = db.session.get(Produto, produto_id)
        if not produto or not produto.ativo:
            flash('Produto inativo ou não encontrado.', 'danger')
            return render_template('movimentacao.html', form=form)

        # Validar posição origem
        posicao_origem = db.session.get(Posicao, posicao_origem_id)
        if not posicao_origem or not posicao_origem.ativa:
            flash('Posição não encontrada ou inativa.', 'danger')
            return render_template('movimentacao.html', form=form)

        try:
            if tipo == 'entrada':
                _processar_entrada(
                    produto_id, posicao_origem_id, quantidade, observacao
                )
                flash('Entrada registrada com sucesso!', 'success')

            elif tipo == 'saida':
                sucesso, msg = _processar_saida(
                    produto_id, posicao_origem_id, quantidade, observacao
                )
                if not sucesso:
                    flash(msg, 'danger')
                    return render_template('movimentacao.html', form=form)
                flash('Saída registrada com sucesso!', 'success')

            elif tipo == 'transferencia':
                posicao_destino_id = form.posicao_destino_id.data

                # Validar posição destino
                if not posicao_destino_id or posicao_destino_id == 0:
                    flash('Selecione a posição de destino.', 'danger')
                    return render_template('movimentacao.html', form=form)

                posicao_destino = db.session.get(Posicao, posicao_destino_id)
                if not posicao_destino or not posicao_destino.ativa:
                    flash('Posição destino não encontrada ou inativa.', 'danger')
                    return render_template('movimentacao.html', form=form)

                if posicao_origem_id == posicao_destino_id:
                    flash(
                        'Posição origem e destino não podem ser iguais.',
                        'danger'
                    )
                    return render_template('movimentacao.html', form=form)

                sucesso, msg = _processar_transferencia(
                    produto_id, posicao_origem_id, posicao_destino_id,
                    quantidade, observacao
                )
                if not sucesso:
                    flash(msg, 'danger')
                    return render_template('movimentacao.html', form=form)
                flash('Transferência registrada com sucesso!', 'success')

            else:
                flash('Tipo de movimento inválido.', 'danger')
                return render_template('movimentacao.html', form=form)

            return redirect(url_for('web.dashboard'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Erro na movimentação: {e}')
            flash('Erro interno ao processar movimentação.', 'danger')

    return render_template('movimentacao.html', form=form)


def _processar_entrada(produto_id, posicao_id, quantidade, observacao):
    """Processa entrada de estoque: cria ou incrementa ocupação."""
    ocupacao = Ocupacao.query.filter_by(
        produto_id=produto_id, posicao_id=posicao_id
    ).first()

    if ocupacao:
        ocupacao.quantidade += quantidade
    else:
        ocupacao = Ocupacao(
            produto_id=produto_id,
            posicao_id=posicao_id,
            quantidade=quantidade
        )
        db.session.add(ocupacao)

    # Registrar histórico
    historico = Historico(
        produto_id=produto_id,
        usuario_id=current_user.id,
        tipo='entrada',
        posicao_id=posicao_id,
        quantidade_movimentada=quantidade,
        observacao=observacao
    )
    db.session.add(historico)
    db.session.commit()


def _processar_saida(produto_id, posicao_id, quantidade, observacao):
    """Processa saída de estoque: valida e decrementa ocupação."""
    ocupacao = Ocupacao.query.filter_by(
        produto_id=produto_id, posicao_id=posicao_id
    ).first()

    if not ocupacao or ocupacao.quantidade < quantidade:
        disponivel = ocupacao.quantidade if ocupacao else 0
        posicao = db.session.get(Posicao, posicao_id)
        codigo = posicao.codigo if posicao else '??'
        return False, (
            f'Quantidade insuficiente em {codigo}. '
            f'Disponível: {disponivel} un'
        )

    ocupacao.quantidade -= quantidade
    
    if ocupacao.quantidade == 0:
        db.session.delete(ocupacao)

    # Registrar histórico
    historico = Historico(
        produto_id=produto_id,
        usuario_id=current_user.id,
        tipo='saida',
        posicao_id=posicao_id,
        quantidade_movimentada=quantidade,
        observacao=observacao
    )
    db.session.add(historico)
    db.session.commit()
    return True, ''


def _processar_transferencia(
    produto_id, posicao_origem_id, posicao_destino_id,
    quantidade, observacao
):
    """Processa transferência entre posições."""
    # Validar estoque na origem
    ocupacao_origem = Ocupacao.query.filter_by(
        produto_id=produto_id, posicao_id=posicao_origem_id
    ).first()

    if not ocupacao_origem or ocupacao_origem.quantidade < quantidade:
        disponivel = ocupacao_origem.quantidade if ocupacao_origem else 0
        posicao = db.session.get(Posicao, posicao_origem_id)
        codigo = posicao.codigo if posicao else '??'
        return False, (
            f'Quantidade insuficiente em {codigo}. '
            f'Disponível: {disponivel} un'
        )

    # Decrementar origem
    ocupacao_origem.quantidade -= quantidade
    
    if ocupacao_origem.quantidade == 0:
        db.session.delete(ocupacao_origem)

    # Incrementar ou criar destino
    ocupacao_destino = Ocupacao.query.filter_by(
        produto_id=produto_id, posicao_id=posicao_destino_id
    ).first()

    if ocupacao_destino:
        ocupacao_destino.quantidade += quantidade
    else:
        ocupacao_destino = Ocupacao(
            produto_id=produto_id,
            posicao_id=posicao_destino_id,
            quantidade=quantidade
        )
        db.session.add(ocupacao_destino)

    # Registrar histórico (origem)
    historico = Historico(
        produto_id=produto_id,
        usuario_id=current_user.id,
        tipo='transferencia',
        posicao_id=posicao_origem_id,
        quantidade_movimentada=quantidade,
        observacao=observacao
    )
    db.session.add(historico)
    db.session.commit()
    return True, ''


# ============================================================
# RELATÓRIO DE HISTÓRICO
# ============================================================
@web_bp.route('/relatorio/historico')
@login_required
@gerente_required
def historico():
    """Relatório de histórico de movimentações com filtros."""
    page = request.args.get('page', 1, type=int)
    tipo_filtro = request.args.get('tipo', '', type=str)
    data_inicio = request.args.get('data_inicio', '', type=str)
    data_fim = request.args.get('data_fim', '', type=str)
    per_page = current_app.config.get('HISTORICO_POR_PAGINA', 20)

    # Query base com joins
    query = Historico.query.join(
        Produto, Historico.produto_id == Produto.id
    ).join(
        Usuario, Historico.usuario_id == Usuario.id
    ).join(
        Posicao, Historico.posicao_id == Posicao.id
    )

    # Filtro por tipo
    if tipo_filtro and tipo_filtro in Historico.TIPOS_VALIDOS:
        query = query.filter(Historico.tipo == tipo_filtro)

    # Filtro por período
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Historico.data_hora >= dt_inicio)
        except ValueError:
            pass

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            # Incluir todo o dia final
            dt_fim = dt_fim.replace(hour=23, minute=59, second=59)
            query = query.filter(Historico.data_hora <= dt_fim)
        except ValueError:
            pass

    # Ordenar: mais recente primeiro
    query = query.order_by(Historico.data_hora.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    registros = pagination.items

    return render_template(
        'historico.html',
        registros=registros,
        pagination=pagination,
        tipo_filtro=tipo_filtro,
        data_inicio=data_inicio,
        data_fim=data_fim
    )


@web_bp.route('/relatorio/historico/csv')
@login_required
@gerente_required
def historico_csv():
    """Exporta histórico filtrado para CSV."""
    tipo_filtro = request.args.get('tipo', '', type=str)
    data_inicio = request.args.get('data_inicio', '', type=str)
    data_fim = request.args.get('data_fim', '', type=str)

    query = Historico.query.join(
        Produto, Historico.produto_id == Produto.id
    ).join(
        Usuario, Historico.usuario_id == Usuario.id
    ).join(
        Posicao, Historico.posicao_id == Posicao.id
    )

    if tipo_filtro and tipo_filtro in Historico.TIPOS_VALIDOS:
        query = query.filter(Historico.tipo == tipo_filtro)
    if data_inicio:
        try:
            dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Historico.data_hora >= dt)
        except ValueError:
            pass
    if data_fim:
        try:
            dt = datetime.strptime(data_fim, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59
            )
            query = query.filter(Historico.data_hora <= dt)
        except ValueError:
            pass

    registros = query.order_by(Historico.data_hora.desc()).all()

    # Gerar CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Data/Hora', 'Produto', 'Tipo', 'Posição',
        'Quantidade', 'Usuário', 'Observação'
    ])
    for r in registros:
        writer.writerow([
            r.data_hora.strftime('%d/%m/%Y %H:%M') if r.data_hora else '',
            r.produto.nome if r.produto else '',
            r.tipo,
            r.posicao.codigo if r.posicao else '',
            r.quantidade_movimentada,
            r.usuario.username if r.usuario else '',
            r.observacao or ''
        ])

    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=historico_estoque.csv'
        }
    )
    return response


# ============================================================
# CRUD - PRODUTOS
# ============================================================
@web_bp.route('/gestao/produtos')
@login_required
@gerente_required
def listar_produtos():
    """Lista todos os produtos para gestão (ativos e inativos)."""
    page = request.args.get('page', 1, type=int)
    produtos = Produto.query.order_by(
        Produto.ativo.desc(), Produto.nome.asc()
    ).paginate(page=page, per_page=20, error_out=False)

    return render_template('gestao_produtos.html', pagination=produtos)


@web_bp.route('/gestao/produto/novo', methods=['GET', 'POST'])
@login_required
@gerente_required
def criar_produto():
    """Formulário de cadastro de novo produto."""
    form = ProdutoForm()

    if form.validate_on_submit():
        url_imagem_path = ''
        if form.imagem.data:
            imagem_file = form.imagem.data
            filename = secure_filename(imagem_file.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'fotos')
            os.makedirs(upload_folder, exist_ok=True)
            imagem_file.save(os.path.join(upload_folder, filename))
            url_imagem_path = f'fotos/{filename}'

        produto = Produto(
            nome=form.nome.data.strip(),
            marca=(form.marca.data or '').strip(),
            tamanho=(form.tamanho.data or '').strip(),
            descricao=(form.descricao.data or '').strip(),
            url_imagem=url_imagem_path
        )
        db.session.add(produto)
        db.session.commit()
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('web.listar_produtos'))

    return render_template(
        'form_produto.html', form=form, titulo='Novo Produto'
    )


@web_bp.route('/gestao/produto/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@gerente_required
def editar_produto(id):
    """Formulário de edição de produto existente."""
    produto = db.session.get(Produto, id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('web.listar_produtos'))

    form = ProdutoForm(obj=produto)

    if form.validate_on_submit():
        if form.imagem.data:
            imagem_file = form.imagem.data
            filename = secure_filename(imagem_file.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'fotos')
            os.makedirs(upload_folder, exist_ok=True)
            imagem_file.save(os.path.join(upload_folder, filename))
            produto.url_imagem = f'fotos/{filename}'

        produto.nome = form.nome.data.strip()
        produto.marca = (form.marca.data or '').strip()
        produto.tamanho = (form.tamanho.data or '').strip()
        produto.descricao = (form.descricao.data or '').strip()
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('web.listar_produtos'))

    return render_template(
        'form_produto.html', form=form, titulo='Editar Produto', produto=produto
    )


@web_bp.route('/gestao/produto/<int:id>/toggle', methods=['POST'])
@login_required
@gerente_required
def toggle_produto(id):
    """Ativa ou desativa um produto."""
    produto = db.session.get(Produto, id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('web.listar_produtos'))

    produto.ativo = not produto.ativo
    db.session.commit()
    estado = 'ativado' if produto.ativo else 'desativado'
    flash(f'Produto {estado} com sucesso!', 'success')
    return redirect(url_for('web.listar_produtos'))


@web_bp.route('/gestao/produto/<int:id>/excluir', methods=['POST'])
@login_required
@gerente_required
def excluir_produto(id):
    """Exclui um produto (cascade nas ocupações e histórico)."""
    produto = db.session.get(Produto, id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('web.listar_produtos'))

    db.session.delete(produto)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('web.listar_produtos'))


# ============================================================
# CRUD - POSIÇÕES
# ============================================================
@web_bp.route('/gestao/posicoes')
@login_required
@gerente_required
def listar_posicoes():
    """Lista todas as posições para gestão."""
    page = request.args.get('page', 1, type=int)
    posicoes = Posicao.query.order_by(
        Posicao.ativa.desc(), Posicao.codigo.asc()
    ).paginate(page=page, per_page=20, error_out=False)

    return render_template('gestao_posicoes.html', pagination=posicoes)


@web_bp.route('/gestao/posicao/nova', methods=['GET', 'POST'])
@login_required
@gerente_required
def criar_posicao():
    """Formulário de cadastro de nova posição."""
    form = PosicaoForm()

    if form.validate_on_submit():
        codigo = form.codigo.data.strip().upper()

        # Verificar unicidade
        existente = Posicao.query.filter_by(codigo=codigo).first()
        if existente:
            flash(f'Já existe uma posição com o código {codigo}.', 'danger')
            return render_template(
                'form_posicao.html', form=form, titulo='Nova Posição'
            )

        posicao = Posicao(
            codigo=codigo,
            descricao=(form.descricao.data or '').strip()
        )
        db.session.add(posicao)
        db.session.commit()
        flash('Posição cadastrada com sucesso!', 'success')
        return redirect(url_for('web.listar_posicoes'))

    return render_template(
        'form_posicao.html', form=form, titulo='Nova Posição'
    )


@web_bp.route('/gestao/posicao/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@gerente_required
def editar_posicao(id):
    """Formulário de edição de posição existente."""
    posicao = db.session.get(Posicao, id)
    if not posicao:
        flash('Posição não encontrada.', 'danger')
        return redirect(url_for('web.listar_posicoes'))

    form = PosicaoForm(obj=posicao)

    if form.validate_on_submit():
        codigo = form.codigo.data.strip().upper()

        # Verificar unicidade (excluindo a própria posição)
        existente = Posicao.query.filter(
            Posicao.codigo == codigo, Posicao.id != id
        ).first()
        if existente:
            flash(f'Já existe outra posição com o código {codigo}.', 'danger')
            return render_template(
                'form_posicao.html', form=form,
                titulo='Editar Posição', posicao=posicao
            )

        posicao.codigo = codigo
        posicao.descricao = (form.descricao.data or '').strip()
        db.session.commit()
        flash('Posição atualizada com sucesso!', 'success')
        return redirect(url_for('web.listar_posicoes'))

    return render_template(
        'form_posicao.html', form=form,
        titulo='Editar Posição', posicao=posicao
    )


@web_bp.route('/gestao/posicao/<int:id>/toggle', methods=['POST'])
@login_required
@gerente_required
def toggle_posicao(id):
    """Ativa ou desativa uma posição."""
    posicao = db.session.get(Posicao, id)
    if not posicao:
        flash('Posição não encontrada.', 'danger')
        return redirect(url_for('web.listar_posicoes'))

    posicao.ativa = not posicao.ativa
    db.session.commit()
    estado = 'ativada' if posicao.ativa else 'desativada'
    flash(f'Posição {estado} com sucesso!', 'success')
    return redirect(url_for('web.listar_posicoes'))


# ============================================================
# CRUD - USUÁRIOS
# ============================================================
@web_bp.route('/gestao/usuarios')
@login_required
@gerente_required
def listar_usuarios():
    """Lista todos os usuários para gestão."""
    page = request.args.get('page', 1, type=int)
    usuarios = Usuario.query.order_by(
        Usuario.ativo.desc(), Usuario.username.asc()
    ).paginate(page=page, per_page=20, error_out=False)

    return render_template('gestao_usuarios.html', pagination=usuarios)


@web_bp.route('/gestao/usuario/novo', methods=['GET', 'POST'])
@login_required
@gerente_required
def criar_usuario():
    """Formulário de cadastro de novo usuário."""
    form = UsuarioForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        if not password or len(password) < 4:
            flash('Senha é obrigatória e deve ter no mínimo 4 caracteres.', 'danger')
            return render_template(
                'form_usuario.html', form=form, titulo='Novo Usuário'
            )

        # Verificar unicidade
        existente = Usuario.query.filter_by(username=username).first()
        if existente:
            flash(f'Já existe um usuário com o nome "{username}".', 'danger')
            return render_template(
                'form_usuario.html', form=form, titulo='Novo Usuário'
            )

        usuario = Usuario(
            username=username,
            role=form.role.data,
            ativo=form.ativo.data
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('web.listar_usuarios'))

    return render_template(
        'form_usuario.html', form=form, titulo='Novo Usuário'
    )


@web_bp.route('/gestao/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@gerente_required
def editar_usuario(id):
    """Formulário de edição de usuário existente."""
    usuario = db.session.get(Usuario, id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('web.listar_usuarios'))

    form = UsuarioForm(obj=usuario)

    if form.validate_on_submit():
        username = form.username.data.strip()

        # Verificar unicidade (excluindo o próprio)
        existente = Usuario.query.filter(
            Usuario.username == username, Usuario.id != id
        ).first()
        if existente:
            flash(f'Já existe outro usuário com o nome "{username}".', 'danger')
            return render_template(
                'form_usuario.html', form=form,
                titulo='Editar Usuário', usuario=usuario
            )

        usuario.username = username
        usuario.role = form.role.data
        usuario.ativo = form.ativo.data

        # Atualizar senha apenas se informada
        if form.password.data and len(form.password.data) >= 4:
            usuario.set_password(form.password.data)

        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('web.listar_usuarios'))

    return render_template(
        'form_usuario.html', form=form,
        titulo='Editar Usuário', usuario=usuario
    )


@web_bp.route('/gestao/usuario/<int:id>/toggle', methods=['POST'])
@login_required
@gerente_required
def toggle_usuario(id):
    """Ativa ou desativa um usuário."""
    usuario = db.session.get(Usuario, id)
    if not usuario:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('web.listar_usuarios'))

    # Não permitir que o gerente desative a si mesmo
    if usuario.id == current_user.id:
        flash('Você não pode desativar seu próprio usuário.', 'danger')
        return redirect(url_for('web.listar_usuarios'))

    usuario.ativo = not usuario.ativo
    db.session.commit()
    estado = 'ativado' if usuario.ativo else 'desativado'
    flash(f'Usuário {estado} com sucesso!', 'success')
    return redirect(url_for('web.listar_usuarios'))
