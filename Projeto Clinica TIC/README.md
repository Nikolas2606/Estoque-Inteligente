# Sistema de Estoque Inteligente 📦

Sistema modular de gestão de inventário com integração IoT, interface de voz (Alexa) e orquestração Docker.

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────┐
│                    Nginx (80/443)                 │
│                  Proxy Reverso                    │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │  Flask    │  │  MariaDB  │  │  Mosquitto   │  │
│  │  App      │──│  (DB)     │  │  (MQTT)      │  │
│  │  :5000    │  │  :3306    │  │  :1883       │  │
│  └──────────┘  └───────────┘  └──────┬───────┘  │
│                                       │          │
└───────────────────────────────────────┼──────────┘
                                        │
                                   ┌────▼────┐
                                   │  ESP32  │
                                   │  (LEDs) │
                                   └─────────┘
```

## ⚡ Quick Start (Desenvolvimento Local)

### Pré-requisitos
- Python 3.10+
- pip

### 1. Clone e configure

```bash
git clone <repo-url>
cd projeto-estoque
cp .env.example .env
# Edite o .env com suas configurações
```

### 2. Setup Python (sem Docker)

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Popular banco de dados

```bash
python seed.py
```

### 4. Executar

```bash
python run.py
```

Acesse: **http://localhost:5000**

### 🔑 Credenciais de Teste

| Usuário    | Senha      | Função   |
|------------|------------|----------|
| admin      | admin1234  | Gerente  |
| vendedor   | vend1234   | Vendedor |

---

## 🐳 Deploy com Docker

### Pré-requisitos
- Docker
- Docker Compose

### 1. Configure variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com senhas seguras e caminhos corretos
```

### 2. Build e Start

```bash
docker-compose up --build -d
```

### 3. Verificar serviços

```bash
docker-compose ps
docker-compose logs -f app
```

Acesse: **http://localhost**

---

## 📁 Estrutura do Projeto

```
/projeto-estoque
├── docker-compose.yml          # Orquestração Docker
├── .env.example                # Template de variáveis
│
├── /backend                    # Código Flask
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py                  # Entry point
│   ├── config.py               # Configurações
│   ├── seed.py                 # Dados iniciais
│   │
│   └── /app
│       ├── __init__.py         # Application Factory
│       ├── models.py           # SQLAlchemy Models
│       ├── extensions.py       # Flask extensions
│       │
│       ├── /auth               # Blueprint: Autenticação
│       ├── /web                # Blueprint: Interface Web
│       ├── /api                # Blueprint: API Alexa
│       ├── /services           # Lógica de negócio
│       ├── /templates          # HTML Jinja2
│       └── /static             # CSS/JS
│
├── /nginx                      # Proxy Reverso
│   └── default.conf
│
└── /mosquitto                  # Broker MQTT
    └── mosquitto.conf
```

---

## 🔗 Endpoints

### Web (Jinja2)
| Rota | Método | Permissão | Descrição |
|------|--------|-----------|-----------|
| `/login` | GET/POST | Público | Login |
| `/logout` | GET | Autenticado | Logout |
| `/dashboard` | GET | Todos | Listagem de produtos |
| `/gestao/movimentacao` | GET/POST | Gerente | Movimentação |
| `/relatorio/historico` | GET | Gerente | Histórico |
| `/gestao/produtos` | GET | Gerente | CRUD Produtos |
| `/gestao/posicoes` | GET | Gerente | CRUD Posições |
| `/gestao/usuarios` | GET | Gerente | CRUD Usuários |

### API
| Rota | Método | Auth | Descrição |
|------|--------|------|-----------|
| `POST /api/alexa/busca` | POST | API Key | Busca de produtos (Alexa) |

---

## 🌐 Configuração de Rede

### IP Estático (Roteador)
- Servidor: `192.168.1.100`
- ESP32: `192.168.1.150`

### Wi-Fi
- SSID: `SmartStock_Internal`
- Frequência: 2.4 GHz
- Segurança: WPA2

### VPN (Tailscale)
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

---

## 📡 MQTT

- **Tópico**: `estoque/posicao`
- **QoS**: 1 (at least once)
- **Payload**:
```json
{
  "posicoes_ativas": ["A1", "C3"],
  "timestamp": "2026-05-22T10:30:00"
}
```

---

## 📋 Tecnologias

- **Backend**: Python 3.12 + Flask 3.1
- **ORM**: Flask-SQLAlchemy + MariaDB
- **Auth**: Flask-Login
- **Frontend**: Jinja2 + Bootstrap 5.3
- **IoT**: MQTT (Eclipse Mosquitto)
- **Proxy**: Nginx Alpine
- **Container**: Docker + Docker Compose
