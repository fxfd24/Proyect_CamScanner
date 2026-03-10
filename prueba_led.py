import serial
import time

PUERTO_ARDUINO = "COM6"  # Cambia si es necesario
print("🔌 Probando Arduino...")

try:
    arduino = serial.Serial(PUERTO_ARDUINO, 9600, timeout=1)
    time.sleep(2)
    print("✅ Conectado!")
    
    # Enviar OPEN (LED debe apagarse)
    arduino.write(b"OPEN\n")
    print("✅ Enviado: OPEN - LED APAGADO")
    time.sleep(2)
    
    # Enviar DENIED (LED debe encenderse)
    arduino.write(b"DENIED\n")
    print("✅ Enviado: DENIED - LED ENCENDIDO")
    time.sleep(2)
    
    arduino.close()
    
except Exception as e:
    print(f"❌ Error: {e}")