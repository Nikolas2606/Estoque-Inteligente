# 👟 Sistema Inteligente de Localização de Calçados com Alexa, MQTT e ESP32

Sistema IoT desenvolvido para auxiliar funcionários e clientes de uma loja de calçados na consulta e localização rápida de produtos.

A solução integra uma Skill personalizada da Alexa, um backend em Python, banco de dados MariaDB, broker MQTT e um ESP32 responsável por indicar visualmente a localização do produto por meio de LEDs.

---

# 🚀 Quick Start

Clone o repositório:

```bash
git clone https://github.com/Nikolas2606/Estoque-Inteligente.git

cd estoqueInteligente
```

Crie o arquivo de variáveis de ambiente:

```bash
cp .env.example .env
```

Construa as imagens Docker:

```bash
docker compose build
```

Inicie todos os serviços:

```bash
docker compose up -d
```

Verifique se os containers estão rodando:

```bash
docker ps
```

Visualize os logs:

```bash
docker compose logs -f
```

---

# 📖 Visão Geral

O sistema foi desenvolvido para reduzir o tempo gasto na procura de produtos dentro de uma loja de calçados.

Fluxo de funcionamento:

1. O funcionário solicita à Alexa a localização de um produto.
2. A Skill Alexa envia a requisição ao backend.
3. O backend consulta o banco de dados.
4. O backend publica a localização em um tópico MQTT.
5. O ESP32 recebe a mensagem.
6. O LED correspondente à posição do produto é acionado.

---

# 🏗️ Arquitetura

```text
Funcionário
     │
     ▼
 Alexa Skill
     │
     ▼
Cloudflare Tunnel
     │
     ▼
Backend Flask
     │
 ┌───┴────┐
 ▼        ▼
MariaDB  MQTT Broker
             │
             ▼
           ESP32
             │
             ▼
            LEDs
```

---

# 🛠️ Tecnologias Utilizadas

- Python
- Flask
- MariaDB
- Mosquitto MQTT
- Docker
- Docker Compose
- ESP32
- Arduino IDE
- Alexa Custom Skill
- Cloudflare Tunnel
- Servidor NAS

---

# 📂 Estrutura do Projeto

```bash
.
├── app/
│   ├── api/
│   ├── services/
│   ├── models/
│   └── config/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

---

# 🔧 Configuração

Crie um arquivo `.env`:

```env
DB_ROOT_PASSWORD=root

DB_NAME=estoque

DB_USER=usuario

DB_PASSWORD=senha

MQTT_HOST=mosquitto

MQTT_PORT=1883

API_KEY=sua_api_key
```

---

# 🐳 Docker

## Construir as imagens

```bash
docker compose build
```

## Iniciar os containers

```bash
docker compose up -d
```

## Reiniciar após alterações

```bash
docker compose up -d --build
```

## Ver containers ativos

```bash
docker ps
```

## Visualizar logs

Todos os serviços:

```bash
docker compose logs -f
```

Backend:

```bash
docker compose logs -f backend
```

Banco de dados:

```bash
docker compose logs -f db
```

Mosquitto:

```bash
docker compose logs -f mosquitto
```

## Parar os containers

```bash
docker compose down
```

## Parar e remover volumes

```bash
docker compose down -v
```

---

# 📡 MQTT

Exemplo de publicação:

```bash
mosquitto_pub \
-t estoque/localizacao \
-m '{"produto":"Nike Air Max","prateleira":"A3"}'
```

Exemplo de assinatura:

```bash
mosquitto_sub \
-t estoque/localizacao
```

---

# 🎙️ Alexa Skill

Exemplo de comando:

> "Alexa, peça ao Buscador Estoque para localizar Nike Air Max."

Fluxo:

1. Alexa interpreta o comando.
2. Envia uma requisição HTTP ao backend.
3. O backend consulta o banco de dados.
4. O backend publica a localização via MQTT.
5. O ESP32 recebe a mensagem e aciona o LED correspondente.

---

# ☁️ Cloudflare Tunnel

A Skill Alexa é executada nos servidores da Amazon e precisa acessar o backend pela internet.

Criar um túnel:

```bash
cloudflared tunnel create estoque-tunnel
```

Listar túneis:

```bash
cloudflared tunnel list
```

Executar o túnel:

```bash
cloudflared tunnel run estoque-tunnel
```

---

# 🔌 ESP32

O ESP32:

- Conecta-se ao Wi-Fi da loja.
- Conecta-se ao broker MQTT.
- Escuta os tópicos de localização.
- Processa as mensagens recebidas.
- Acende o LED correspondente à localização do produto.

Exemplo de mensagem:

```json
{
  "produto": "Nike Air Max",
  "prateleira": "A3"
}
```

---

# 🧪 Executando sem Docker

Crie um ambiente virtual:

```bash
python -m venv venv
```

Ative o ambiente:

### Windows

```bash
venv\Scripts\activate
```

### Linux

```bash
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute a aplicação:

```bash
python run.py
```

ou

```bash
flask run
```

---

# 📋 Exemplo de Endpoint

### Buscar produto

```http
POST /alexa/busca
```

Headers:

```http
X-API-Key: SUA_API_KEY
```

Body:

```json
{
  "produto": "Nike Air Max"
}
```

Resposta:

```json
{
  "produto": "Nike Air Max",
  "prateleira": "A3",
  "setor": "Esportivo"
}
```

---

# 👨‍💻 Autores

Projeto desenvolvido como trabalho acadêmico de Engenharia de Software.

- Nikolas Malinowski
- Integrantes do grupo

---

# 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos.
