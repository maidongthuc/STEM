// KHAI BÁO THƯ VIỆN
#include <Arduino.h>
#include <WiFi.h>  
#include <PubSubClient.h>

// KHAI BÁO PASS VÀ TÊN WIFI
const char* ssid = "TrieuMen";
const char* password = "1111aaaa";

// KHAI BÁO CÁC CHÂN ĐIỀU KHIỂN ĐỘNG CƠ VÀ PWM
#define in1 12
#define in2 13
#define in3 14
#define in4 15
// #define ENA 2

// KHAI BÁO MQTT
#define MQTT_SERVER "broker.mqttdashboard.com"
#define MQTT_PORT 1883
#define MQTT_USER "chechanh2003"
#define MQTT_PASSWORD "0576289825"
#define TOPIC_1 "Livingroom/device_1"
#define TOPIC_2 "Livingroom/device_2"
#define TOPIC_3 "Livingroom/device_3"
#define TOPIC_4 "Livingroom/device_4"

WiFiClient wifiClient;
PubSubClient client(wifiClient);

// HÀM KẾT NỐI WIFI
void setup_wifi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// HÀM KẾT NỐI MQTT BROKER
void connect_to_broker() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "IoTLab4";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("connected");
      client.subscribe(TOPIC_1);
      client.subscribe(TOPIC_2);
      client.subscribe(TOPIC_3);
      client.subscribe(TOPIC_4);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 2 seconds");
      delay(2000);
    }
  }
}

// HÀM CALLBACK XỬ LÝ DỮ LIỆU TỪ MQTT
void callback(char* topic, byte *payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.println(topic);
  Serial.println("DEVICE 1: " + message);
  
  if (message[0] == 'u') {
    up(message.substring(1).toInt());
  }
  else if (message[0] == 'd') {
    down(message.substring(1).toInt());
  }
  else   if (message[0] == 'l') {
    left(message.substring(1).toInt());
  }
  else   if (message[0] == 'r') {
    right(message.substring(1).toInt());
  }
  else {
    off();
  }
}


// HÀM ĐIỀU KHIỂN ĐỘNG CƠ
void up(int n){
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  delay(n*20);
  Serial.println(n);
  off();
  delay(500);
}

void down(int n){
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW);
  digitalWrite(in4, HIGH);
  delay(n*20);
  Serial.println(n);
  off();
  delay(500);
}

void left(int n){
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
  delay(n);
  Serial.println(n);
  off();
  delay(500);
}

void right(int n){
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  delay(n);
  Serial.println(n);
  off();
  delay(500);
}

void off(){
  digitalWrite(in1, LOW);
  digitalWrite(in2, LOW);
  digitalWrite(in3, LOW);
  digitalWrite(in4, LOW);
}

// HÀM SETUP
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(500);
  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
  connect_to_broker();
  // analogWrite(ENA, 50);

  // Thiết lập các chân điều khiển là OUTPUT
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(in3, OUTPUT);
  pinMode(in4, OUTPUT);
}

// HÀM LOOP
void loop() {
  client.loop();
  if (!client.connected()) {
    connect_to_broker();
  }
}
