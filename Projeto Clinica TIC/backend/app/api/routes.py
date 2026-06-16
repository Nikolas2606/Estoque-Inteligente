"""
Rotas da API — Endpoint de busca para Alexa.
"""
from flask import request, jsonify, current_app

from app.api import api_bp
from app.services.produto_service import ProdutoService
from app.services.mqtt_service import MqttService


@api_bp.route('/alexa/busca', methods=['POST'])
def alexa_busca():
    """
    Endpoint de busca de produtos para a Skill Alexa.

    Autenticação: API Key no header X-API-Key.

    Request Body (JSON):
        {
            "busca": "nome do produto" (obrigatório, 2-100 chars),
            "quantidade_maxima": 5 (opcional, 1-10, default 5)
        }

    Responses:
        200: Produto encontrado ou não encontrado
        400: Parâmetro inválido
        401: API Key inválida
        500: Erro interno
    """
    # --- Validação do corpo da requisição ---
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            'status': 'erro',
            'mensagem': 'Corpo da requisição deve ser JSON.',
            'codigo_erro': 'CORPO_INVALIDO'
        }), 400

    busca = (data.get('busca') or '').strip().lower()
    quantidade_maxima = data.get('quantidade_maxima', 5)

    # Validar campo 'busca'
    if not busca or len(busca) < 2:
        return jsonify({
            'status': 'erro',
            'mensagem': "Parâmetro 'busca' deve ter no mínimo 2 caracteres.",
            'codigo_erro': 'PARAM_INVALIDO'
        }), 400

    if len(busca) > 100:
        return jsonify({
            'status': 'erro',
            'mensagem': "Parâmetro 'busca' deve ter no máximo 100 caracteres.",
            'codigo_erro': 'PARAM_INVALIDO'
        }), 400

    # Validar quantidade_maxima
    try:
        quantidade_maxima = int(quantidade_maxima)
        quantidade_maxima = max(1, min(10, quantidade_maxima))
    except (ValueError, TypeError):
        quantidade_maxima = 5

    # --- Busca de produtos ---
    try:
        resultado = ProdutoService.buscar_produtos(busca, quantidade_maxima)

        if resultado['encontrado']:
            # Publicar posições ativas no MQTT
            posicoes_ativas = []
            for produto in resultado['produtos']:
                for loc in produto.get('localizacoes', []):
                    codigo = loc.get('posicao', '')
                    if codigo and codigo not in posicoes_ativas:
                        posicoes_ativas.append(codigo)

            if posicoes_ativas:
                MqttService.publicar_posicoes(posicoes_ativas)

            return jsonify({
                'status': 'sucesso',
                'encontrado': True,
                'produtos': resultado['produtos']
            }), 200
        else:
            # Produto não encontrado — buscar sugestões
            sugestoes = ProdutoService.buscar_sugestoes(busca)

            return jsonify({
                'status': 'sucesso',
                'encontrado': False,
                'mensagem_voz': 'Desculpe, não encontrei esse produto no estoque atual.',
                'sugestoes': sugestoes
            }), 200

    except Exception as e:
        current_app.logger.error(f'Erro na busca Alexa: {e}')
        return jsonify({
            'status': 'erro',
            'mensagem': 'Erro interno ao processar busca.',
            'codigo_erro': 'ERRO_INTERNO'
        }), 500
