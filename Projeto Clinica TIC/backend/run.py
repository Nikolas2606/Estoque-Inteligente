"""
Ponto de entrada do Sistema de Estoque Inteligente.
Executa o servidor Flask em modo desenvolvimento.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
