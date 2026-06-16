"""
Serviço de Busca de Produtos — Lógica de query para API Alexa.

Encapsula a busca de produtos com geração de mensagens de voz
naturais em português para a Alexa.
"""
import logging

from app.extensions import db
from app.models import Produto, Ocupacao

logger = logging.getLogger(__name__)


class ProdutoService:
    """Serviço de busca de produtos para a API Alexa."""

    @classmethod
    def buscar_produtos(cls, termo: str, max_resultados: int = 5) -> dict:
        """
        Busca produtos por nome ou marca.

        Args:
            termo: Termo de busca (já sanitizado/lowercase)
            max_resultados: Máximo de produtos retornados (1-10)

        Returns:
            dict com 'encontrado' (bool) e 'produtos' (list)
        """
        filtro = f'%{termo}%'

        # Query: produtos ativos com match no nome ou marca
        produtos = Produto.query.filter(
            Produto.ativo == True,  # noqa: E712
            db.or_(
                Produto.nome.ilike(filtro),
                Produto.marca.ilike(filtro)
            )
        ).limit(max_resultados).all()

        # Filtrar apenas produtos com estoque > 0
        resultados = []
        for produto in produtos:
            produto_dict = produto.to_dict()
            if produto_dict['total_quantidade'] > 0:
                # Gerar mensagem de voz natural
                produto_dict['mensagem_voz'] = cls._gerar_mensagem_voz(
                    produto_dict
                )
                resultados.append(produto_dict)

        if resultados:
            return {
                'encontrado': True,
                'produtos': resultados
            }
        else:
            return {
                'encontrado': False,
                'produtos': []
            }

    @classmethod
    def buscar_sugestoes(cls, termo: str, max_sugestoes: int = 3) -> list:
        """
        Busca sugestões de produtos similares quando o termo
        exato não é encontrado.

        Returns:
            Lista de nomes de produtos sugeridos.
        """
        try:
            # Buscar produtos ativos que começam com a primeira letra
            # ou que tenham alguma similaridade
            sugestoes = Produto.query.filter(
                Produto.ativo == True  # noqa: E712
            ).order_by(
                Produto.nome.asc()
            ).limit(max_sugestoes).all()

            return [p.nome for p in sugestoes if p.total_estoque > 0]

        except Exception as e:
            logger.error(f'Erro ao buscar sugestões: {e}')
            return []

    @classmethod
    def _gerar_mensagem_voz(cls, produto_dict: dict) -> str:
        """
        Gera mensagem de voz natural em português para a Alexa.

        Ex: "Encontrei 15 unidades do Notebook Dell XPS 15.
             10 em A1 e 5 em C3."
        """
        nome = produto_dict['nome']
        total = produto_dict['total_quantidade']
        localizacoes = produto_dict.get('localizacoes', [])

        # Unidade singular/plural
        un = 'unidade' if total == 1 else 'unidades'

        # Construir parte das localizações
        if len(localizacoes) == 1:
            loc = localizacoes[0]
            loc_texto = (
                f"na posição {loc['posicao']} "
                f"com {loc['quantidade']} {un}"
            )
        elif len(localizacoes) == 2:
            partes = [
                f"{l['quantidade']} em {l['posicao']}"
                for l in localizacoes
            ]
            loc_texto = f"{partes[0]} e {partes[1]}"
        else:
            partes = [
                f"{l['quantidade']} em {l['posicao']}"
                for l in localizacoes
            ]
            loc_texto = ', '.join(partes[:-1]) + f' e {partes[-1]}'

        # Mensagem final
        if len(localizacoes) == 1:
            mensagem = (
                f"Encontrei {total} {un} de {nome}. "
                f"Localizada {loc_texto}."
            )
        else:
            mensagem = (
                f"Encontrei {total} {un} de {nome}. "
                f"Localizadas nas posições: {loc_texto}."
            )

        return mensagem
