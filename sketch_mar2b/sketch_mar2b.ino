/**
 * Código para Arduino Uno
 * Responde a comandos de Python:
 * - OPEN   → Servo se mueve a 90° y regresa a 0° (LED no cambia)
 * - DENIED → LED se enciende 1 segundo y se apaga (servo no se mueve)
 */

#include <Servo.h>

const int LED_PIN = 11;
const int SERVO_PIN = 9;

Servo miServo;
String comando = "";

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);  // LED apagado inicialmente
  
  miServo.attach(SERVO_PIN);
  miServo.write(0);  // Servo en posición cerrada (0°)
  
  Serial.println("Arduino listo - Esperando comandos...");
}

void loop() {
  if (Serial.available() > 0) {
    comando = Serial.readStringUntil('\n');
    comando.trim();
    
    if (comando == "OPEN") {
      // ===== ACCESO CONCEDIDO =====
      Serial.println("COMANDO: OPEN - Acceso CONCEDIDO");
      
      // Mover servo a 90° (abrir)
      miServo.write(90);
      delay(1000);  // Esperar 1 segundo
      
      // Regresar servo a 0° (cerrar)
      miServo.write(0);
      
      Serial.println("   ✅ Servo: 90° → 0° (abrió y cerró)");
    } 
    else if (comando == "DENIED") {
      // ===== ACCESO DENEGADO =====
      Serial.println("COMANDO: DENIED - Acceso DENEGADO");
      
      // Encender LED por 1 segundo
      digitalWrite(LED_PIN, HIGH);
      delay(1000);  // LED encendido 1 segundo
      digitalWrite(LED_PIN, LOW);
      
      Serial.println("   ❌ LED: Encendido 1 segundo");
    }
  }
  
  delay(10);
}