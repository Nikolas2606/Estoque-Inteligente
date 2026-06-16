"""
Script de Seed - Popular banco com dados iniciais de teste.

Uso:
    cd backend
    python seed.py

Cria: 2 usuários, 5 produtos, 10 posições, ocupações e histórico.
"""
import sys
import os

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models import Usuario, Produto, Posicao, Ocupacao, Historico


def seed():
    """Popula o banco de dados com dados de teste."""
    app = create_app('development')

    with app.app_context():
        # Verificar se já tem dados
        if Usuario.query.first():
            print('⚠️  Banco já possui dados. Seed cancelado.')
            print('   Para resetar: delete o arquivo estoque_dev.db')
            return

        print('🌱 Iniciando seed do banco de dados...\n')

        # ---- USUÁRIOS ----
        print('👤 Criando usuários...')
        gerente = Usuario(username='admin', role='gerente')
        gerente.set_password('admin1234')

        vendedor = Usuario(username='vendedor', role='vendedor')
        vendedor.set_password('vend1234')

        db.session.add_all([gerente, vendedor])
        db.session.flush()  # Gerar IDs
        print(f'   ✓ Gerente: admin / admin1234')
        print(f'   ✓ Vendedor: vendedor / vend1234')

        # ---- POSIÇÕES ----
        print('\n📍 Criando posições...')
        posicoes = []
        descricoes = {
            'A1': 'Prateleira superior - Corredor A',
            'A2': 'Prateleira média - Corredor A',
            'A3': 'Prateleira inferior - Corredor A',
            'A4': 'Gaveta superior - Corredor A',
            'A5': 'Gaveta inferior - Corredor A',
            'B1': 'Prateleira superior - Corredor B',
            'B2': 'Prateleira média - Corredor B',
            'B3': 'Prateleira inferior - Corredor B',
            'B4': 'Gaveta superior - Corredor B',
            'B5': 'Gaveta inferior - Corredor B',
        }
        for codigo, descricao in descricoes.items():
            pos = Posicao(codigo=codigo, descricao=descricao)
            posicoes.append(pos)
            db.session.add(pos)
            print(f'   ✓ {codigo}: {descricao}')

        db.session.flush()

        # ---- PRODUTOS ----
        print('\n📦 Criando produtos...')
        produtos_data = [
            {
                'nome': 'Notebook Dell XPS 15',
                'marca': 'Dell',
                'tamanho': '15 polegadas',
                'descricao': 'Notebook premium com tela OLED e processador Intel i7.',
                'url_imagem': 'produtos/notebook_dell.jpg'
            },
            {
                'nome': 'Mouse Logitech MX Master 3',
                'marca': 'Logitech',
                'tamanho': 'Único',
                'descricao': 'Mouse ergonômico sem fio com sensor de alta precisão.',
                'url_imagem': 'produtos/mouse_logitech.jpg'
            },
            {
                'nome': 'Teclado Mecânico HyperX',
                'marca': 'HyperX',
                'tamanho': 'Full-size',
                'descricao': 'Teclado mecânico com switches Cherry MX Red.',
                'url_imagem': 'produtos/teclado_hyperx.jpg'
            },
            {
                'nome': 'Monitor LG UltraWide 34"',
                'marca': 'LG',
                'tamanho': '34 polegadas',
                'descricao': 'Monitor ultrawide 2K para produtividade.',
                'url_imagem': 'produtos/monitor_lg.jpg'
            },
            {
                'nome': 'Webcam Logitech C920',
                'marca': 'Logitech',
                'tamanho': 'Compacto',
                'descricao': 'Webcam Full HD 1080p com microfone integrado.',
                'url_imagem': 'produtos/webcam_logitech.jpg'
            },
        ]

        produtos = []
        for pd in produtos_data:
            produto = Produto(**pd)
            produtos.append(produto)
            db.session.add(produto)
            print(f'   ✓ {pd["nome"]} ({pd["marca"]})')

        db.session.flush()

        # ---- OCUPAÇÕES (Produtos em Posições) ----
        print('\n📊 Criando ocupações (estoque)...')
        ocupacoes_data = [
            (0, 0, 10),  # Notebook Dell → A1: 10 un
            (0, 5, 5),   # Notebook Dell → B1: 5 un
            (1, 1, 20),  # Mouse → A2: 20 un
            (1, 6, 15),  # Mouse → B2: 15 un
            (2, 2, 8),   # Teclado → A3: 8 un
            (3, 3, 3),   # Monitor → A4: 3 un
            (3, 8, 2),   # Monitor → B4: 2 un
            (4, 4, 30),  # Webcam → A5: 30 un
        ]

        for prod_idx, pos_idx, qtd in ocupacoes_data:
            oc = Ocupacao(
                produto_id=produtos[prod_idx].id,
                posicao_id=posicoes[pos_idx].id,
                quantidade=qtd
            )
            db.session.add(oc)
            print(
                f'   ✓ {produtos[prod_idx].nome} → '
                f'{posicoes[pos_idx].codigo}: {qtd} un'
            )

        db.session.flush()

        # ---- HISTÓRICO (Registros iniciais) ----
        print('\n📝 Criando histórico inicial...')
        for prod_idx, pos_idx, qtd in ocupacoes_data:
            hist = Historico(
                produto_id=produtos[prod_idx].id,
                usuario_id=gerente.id,
                tipo='entrada',
                posicao_id=posicoes[pos_idx].id,
                quantidade_movimentada=qtd,
                observacao='Estoque inicial - Seed'
            )
            db.session.add(hist)

        print(f'   ✓ {len(ocupacoes_data)} registros de entrada inicial')

        # ---- COMMIT ----
        db.session.commit()

        print('\n' + '=' * 50)
        print('✅ Seed concluído com sucesso!')
        print('=' * 50)
        print(f'\n🔑 Credenciais de acesso:')
        print(f'   Gerente:  admin / admin1234')
        print(f'   Vendedor: vendedor / vend1234')
        print(f'\n📦 {len(produtos)} produtos cadastrados')
        print(f'📍 {len(posicoes)} posições criadas')
        print(f'📊 {len(ocupacoes_data)} ocupações definidas')
        print(f'📝 {len(ocupacoes_data)} registros de histórico')


if __name__ == '__main__':
    seed()
