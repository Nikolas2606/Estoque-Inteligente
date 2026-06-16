"""
Serviço MQTT — Comunicação com ESP32 via Eclipse Mosquitto.

Publica posições ativas no tópico 'estoque/posicao' para que o
ESP32 possa acender os LEDs correspondentes.
"""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MqttService:
    """Serviço de publicação MQTT desacoplado."""

    TOPICO = 'estoque/posicao'
    QOS = 1  # At least once

    @classmethod
    def publicar_posicoes(cls, codigos_posicao: list):
        """
        Publica lista de posições ativas no tópico MQTT.

        O ESP32 receberá esta mensagem e acenderá os LEDs
        correspondentes, com timeout interno de 20 segundos.

        Args:
            codigos_posicao: Lista de códigos (ex: ["A1", "C3"])

        O método é resiliente: se o broker estiver indisponível,
        loga o erro mas não bloqueia a resposta da Alexa.
        """
        if not codigos_posicao:
            logger.info('MQTT: Nenhuma posição para publicar.')
            return

        payload = {
            'posicoes_ativas': codigos_posicao,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        payload_json = json.dumps(payload)

        try:
            # Importar mqtt dentro do método para evitar erros se
            # MQTT não estiver configurado (dev local sem broker)
            from flask import current_app

            mqtt_enabled = current_app.config.get('MQTT_ENABLED', False)
            if not mqtt_enabled:
                logger.info(
                    f'MQTT desabilitado. Payload simulado: {payload_json}'
                )
                return

            # Tentar publicar via paho-mqtt standalone
            # (mais robusto que Flask-MQTT para publicação pontual)
            import paho.mqtt.publish as publish

            broker_host = current_app.config.get('MQTT_BROKER_URL', 'broker')
            broker_port = current_app.config.get('MQTT_BROKER_PORT', 1883)

            publish.single(
                topic=cls.TOPICO,
                payload=payload_json,
                qos=cls.QOS,
                hostname=broker_host,
                port=broker_port
            )

            logger.info(
                f'MQTT: Publicado em {cls.TOPICO} → {payload_json}'
            )

        except ImportError:
            # paho-mqtt não instalado (dev local)
            logger.warning(
                f'MQTT: paho-mqtt não disponível. '
                f'Payload não enviado: {payload_json}'
            )

        except Exception as e:
            # Broker indisponível ou erro de rede
            # Não bloqueia a resposta da Alexa (edge case 5)
            logger.error(
                f'MQTT: Erro ao publicar em {cls.TOPICO}: {e}. '
                f'Payload: {payload_json}'
            )
