"""
Script Auxiliar para Testar e Visualizar Mensagens MQTT.
Escuta o tópico 'estoque/posicao' no broker.
"""
import sys
import os

# Usar o venv do backend para garantir que as dependências paho-mqtt estejam disponíveis
try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Erro: paho-mqtt não está instalado no ambiente python atual.")
    print("Dica: execute usando o venv: backend/venv/Scripts/python.exe mqtt_subscriber.py")
    sys.exit(1)

# Configuração
BROKER_HOST = "localhost"  # Se o broker estiver em outra máquina ou container, altere aqui
BROKER_PORT = 1883
TOPICO = "estoque/posicao"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Conectado com sucesso ao broker {BROKER_HOST}:{BROKER_PORT}!")
        client.subscribe(TOPICO)
        print(f"📥 Inscrito no tópico '{TOPICO}'. Aguardando mensagens...")
    else:
        print(f"❌ Falha ao conectar. Código de retorno: {rc}")

def on_message(client, userdata, msg):
    print(f"\n🔔 Nova mensagem recebida em [{msg.topic}]:")
    print(msg.payload.decode('utf-8'))

# Compatibilidade com paho-mqtt v2.x e v1.x
try:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
except AttributeError:
    client = mqtt.Client()  # Versão antiga do paho-mqtt

client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"Tentando conectar ao broker em {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\nEncerrando subscriber MQTT.")
except Exception as e:
    print(f"\n❌ Erro de conexão: {e}")
    print("Verifique se o broker (Mosquitto/Docker) está ativo e rodando na porta especificada.")
