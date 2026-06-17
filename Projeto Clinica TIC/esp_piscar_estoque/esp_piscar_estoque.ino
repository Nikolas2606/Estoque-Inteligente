#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ===== WIFI =====
const char* ssid = "Oi_Velox_WiFi_192D";
const char* password = "meuoiveloxwifi";

// ===== MQTT =====
const char* mqtt_server = "192.168.1.100";
const int mqtt_port = 1883;

// ===== CLIENT =====
WiFiClient espClient;
PubSubClient client(espClient);

// ===== PINOS =====
#define COL_A 33
#define COL_B 32

#define A1 25
#define A2 26

#define B1 27
#define B2 14

// ===== TIMER =====
unsigned long tempoAcendido = 0;
bool ledsAtivos = false;

// ===== APAGA TUDO =====
void apagarTudo() {
  digitalWrite(COL_A, LOW);
  digitalWrite(COL_B, LOW);
  digitalWrite(A1, LOW);
  digitalWrite(A2, LOW);
  digitalWrite(B1, LOW);
  digitalWrite(B2, LOW);
}

// ===== CALLBACK MQTT =====
void callback(char* topic, byte* payload, unsigned int length) {

  String msg = "";

  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  Serial.println("\n===== MQTT RECEBIDO =====");
  Serial.println(msg);

  StaticJsonDocument<256> doc;

  DeserializationError error = deserializeJson(doc, msg);

  if (error) {
    Serial.println("Erro JSON");
    return;
  }

  apagarTudo();

  JsonArray posicoes = doc["posicoes_ativas"];

  bool temA = false;
  bool temB = false;

  for (const char* pos : posicoes) {

    if (strcmp(pos, "A1") == 0) digitalWrite(A1, HIGH);
    if (strcmp(pos, "A2") == 0) digitalWrite(A2, HIGH);

    if (strcmp(pos, "B1") == 0) digitalWrite(B1, HIGH);
    if (strcmp(pos, "B2") == 0) digitalWrite(B2, HIGH);

    if (pos[0] == 'A') temA = true;
    if (pos[0] == 'B') temB = true;
  }

  if (temA) digitalWrite(COL_A, HIGH);
  if (temB) digitalWrite(COL_B, HIGH);

  // ===== INICIA TIMER =====
  tempoAcendido = millis();
  ledsAtivos = true;
}

// ===== WIFI =====
void setup_wifi() {

  Serial.println("Conectando WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi OK");
  Serial.println(WiFi.localIP());
}

// ===== MQTT RECONNECT =====
void reconnect() {

  while (!client.connected()) {

    Serial.print("Conectando MQTT... ");

    if (client.connect("ESP32_estoque")) {

      Serial.println("OK");

      client.subscribe("estoque/posicao");

    } else {

      Serial.print("falhou rc=");
      Serial.println(client.state());

      delay(3000);
    }
  }
}

void setup() {

  Serial.begin(115200);

  pinMode(COL_A, OUTPUT);
  pinMode(COL_B, OUTPUT);

  pinMode(A1, OUTPUT);
  pinMode(A2, OUTPUT);
  pinMode(B1, OUTPUT);
  pinMode(B2, OUTPUT);

  apagarTudo();

  setup_wifi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  reconnect();
}

void loop() {

  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  // ===== AUTO DESLIGA EM 10s =====
  if (ledsAtivos && millis() - tempoAcendido >= 10000) {

    Serial.println("Desligando LEDs após 10 segundos");

    apagarTudo();

    ledsAtivos = false;
  }
}