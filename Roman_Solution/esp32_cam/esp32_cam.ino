/**
 * CÓDIGO ESP32-CAM - VERSIÓN ESTABLE PARA EL PROYECTO WEB
 * 
 * ENDPOINTS:
 * - /stream  (Para el video en vivo)
 * - /capture (Para reconocer y guardar rostros con flash)
 */

#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// ===== CONFIGURACIÓN WiFi =====
const char* ssid = "MTSRouter_2.4G_006254";
const char* password = "4bxGK2Nr";

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

// Servidores
httpd_handle_t stream_httpd = NULL;
httpd_handle_t camera_httpd = NULL;

// Contador de fotos
int foto_count = 0;

// ============================================
// PARTE 1: STREAMING MJPEG (/stream)
// ============================================
static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t *_jpg_buf = NULL;
  char part_buf[64];
  
  res = httpd_resp_set_type(req, "multipart/x-mixed-replace;boundary=123456789000000000000987654321");
  if (res != ESP_OK) return res;
  
  Serial.println("🎥 Streaming iniciado");
  
  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      res = ESP_FAIL;
      break;
    }
    
    if (fb->format != PIXFORMAT_JPEG) {
      bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
      esp_camera_fb_return(fb);
      fb = NULL;
      if (!jpeg_converted) continue;
    } else {
      _jpg_buf_len = fb->len;
      _jpg_buf = fb->buf;
    }
    
    size_t hlen = snprintf(part_buf, 64, "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", _jpg_buf_len);
    res = httpd_resp_send_chunk(req, part_buf, hlen);
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, (const char*)_jpg_buf, _jpg_buf_len);
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, "\r\n--123456789000000000000987654321\r\n", 37);
    
    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if (_jpg_buf) {
      free(_jpg_buf);
      _jpg_buf = NULL;
    }
    
    if (res != ESP_OK) break;
  }
  return res;
}

// ============================================
// PARTE 2: CAPTURA DE FOTO (/capture)
// ============================================
static esp_err_t capture_handler(httpd_req_t *req) {
  foto_count++;
  Serial.printf("\n📸 Capturando foto #%d...\n", foto_count);
  
  // Flash (para iluminar la cara durante el reconocimiento)
  digitalWrite(LED_FLASH, HIGH);
  delay(150);
  
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    digitalWrite(LED_FLASH, LOW);
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }
  
  digitalWrite(LED_FLASH, LOW);
  
  // Headers
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=captura.jpg");
  
  esp_err_t res = httpd_resp_send(req, (const char*)fb->buf, fb->len);
  
  Serial.printf("✅ Foto enviada: %d bytes\n", fb->len);
  esp_camera_fb_return(fb);
  return res;
}

// ============================================
// PARTE 3: SETUP
// ============================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== INICIANDO ESP32-CAM ===");
  
  pinMode(LED_FLASH, OUTPUT);
  digitalWrite(LED_FLASH, LOW);
  
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
  
  config.xclk_freq_hz = 10000000;      // 10MHz (seguro)
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;    // 640x480 (buen balance para reconocimiento y streaming)
  config.jpeg_quality = 12;              
  config.fb_count = 1;                   
  
  esp_err_t err = esp_camera_init(&config);
  
  if (err != ESP_OK) {
    Serial.printf("❌ Error: 0x%x\n", err);
    return;
  }
  
  // Conectar WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi conectado!");
  Serial.print("📡 IP: http://");
  Serial.println(WiFi.localIP());
  
  // Configurar servidores
  httpd_config_t httpd_config = HTTPD_DEFAULT_CONFIG();
  
  httpd_uri_t stream_uri = {.uri = "/stream", .method = HTTP_GET, .handler = stream_handler};
  httpd_uri_t capture_uri = {.uri = "/capture", .method = HTTP_GET, .handler = capture_handler};
  
  if (httpd_start(&camera_httpd, &httpd_config) == ESP_OK) {
    httpd_register_uri_handler(camera_httpd, &stream_uri);
    httpd_register_uri_handler(camera_httpd, &capture_uri);
    
    Serial.println("\n🚀 SERVICIOS DISPONIBLES:");
    Serial.println("   🎥 /stream  - Streaming MJPEG");
    Serial.println("   📸 /capture - Capturar foto con flash");
  }
}

void loop() {
  delay(10000);
}