/**
 * CÓDIGO ESP32-CAM - VERSIÓN ULTRA SIMPLE
 * Solo hace una cosa: capturar y enviar foto
 */

#include "esp_camera.h"
#include <WiFi.h>

// ===== CONFIGURACIÓN WiFi =====
const char* ssid = "Awebo";
const char* password = "ILovelagopus253";

// ===== PINES PARA AI-THINKER ESP32-CAM =====
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// LED Flash
#define LED_FLASH 4

// Servidor web
WiFiServer server(80);

// Variable para contar fotos
int foto_count = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== INICIANDO ESP32-CAM (VERSIÓN ULTRA SIMPLE) ===");
  
  pinMode(LED_FLASH, OUTPUT);
  digitalWrite(LED_FLASH, LOW);
  
  // Configuración MÍNIMA de cámara
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;    // 320x240
  config.jpeg_quality = 8;                // Calidad media
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error cámara: 0x%x\n", err);
    return;
  }
  Serial.println("✅ Cámara OK");

  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi OK");
  Serial.print("📡 IP: http://");
  Serial.println(WiFi.localIP());
  
  server.begin();
  Serial.println("🚀 Servidor listo");
}

void loop() {
  WiFiClient client = server.available();
  if (!client) {
    delay(10);
    return;
  }
  
  foto_count++;
  Serial.printf("\n📸 Petición #%d recibida\n", foto_count);
  
  // Leer y descartar toda la petición
  while (client.available()) {
    client.read();
  }
  
  // Encender flash
  digitalWrite(LED_FLASH, HIGH);
  delay(100);
  
  // Capturar foto
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Error capturando");
    digitalWrite(LED_FLASH, LOW);
    client.stop();
    return;
  }
  
  digitalWrite(LED_FLASH, LOW);
  
  // ENVÍO DIRECTO - SIN COMPLICACIONES
  client.print("HTTP/1.1 200 OK\r\n");
  client.print("Content-Type: image/jpeg\r\n");
  client.print("Content-Length: ");
  client.print(fb->len);
  client.print("\r\n");
  client.print("Access-Control-Allow-Origin: *\r\n");
  client.print("Connection: close\r\n");
  client.print("\r\n");
  
  // Enviar toda la foto de una vez
  size_t sent = client.write(fb->buf, fb->len);
  
  Serial.printf("✅ Enviados %d de %d bytes\n", sent, fb->len);
  
  esp_camera_fb_return(fb);
  
  // Esperar a que se envíe todo
  client.flush();
  delay(50);
  client.stop();
}