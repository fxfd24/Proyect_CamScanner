import socket
import urllib.request
import subprocess
import sys
import time

URL_CAMARA = "http://192.168.1.246"
ip = URL_CAMARA.replace("http://", "")

print("="*70)
print("🔍 DIAGNÓSTICO COMPLETO DE CONEXIÓN")
print("="*70)

# 1. IP de tu PC
print("\n📊 1. INFORMACIÓN DE TU PC:")
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"   PC Hostname: {hostname}")
print(f"   PC IP: {local_ip}")
print(f"   Red de PC: {'.'.join(local_ip.split('.')[:3])}.x")

# 2. Verificar misma red
red_pc = '.'.join(local_ip.split('.')[:3])
red_cam = '.'.join(ip.split('.')[:3])
if red_pc == red_cam:
    print(f"\n✅ MISMA RED: {red_pc}.x")
else:
    print(f"\n❌ DIFERENTE RED: PC={red_pc}.x vs Cámara={red_cam}.x")
    print("   IMPORTANTE: Deben estar en la misma red WiFi")

# 3. Ping a la cámara
print(f"\n📡 2. PING a {ip}:")
try:
    param = '-n' if sys.platform.lower() == 'win32' else '-c'
    result = subprocess.run(['ping', param, '1', ip], 
                          capture_output=True, text=True, timeout=3)
    if result.returncode == 0:
        print("   ✅ PING EXITOSO - La cámara responde")
        # Mostrar tiempo
        for line in result.stdout.split('\n'):
            if 'tiempo' in line.lower() or 'time' in line.lower():
                print(f"   {line.strip()}")
                break
    else:
        print("   ❌ PING FALLÓ - La cámara no responde")
        print("   Causa posible: Firewall bloqueando ICMP")
except Exception as e:
    print(f"   ⚠️ Error: {e}")

# 4. Escaneo de puertos
print(f"\n🔌 3. ESCANEO DE PUERTOS:")
puertos = [80, 81, 8080, 8000]
for puerto in puertos:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((ip, puerto))
    if result == 0:
        print(f"   ✅ Puerto {puerto}: ABIERTO")
    else:
        print(f"   ❌ Puerto {puerto}: CERRADO (código {result})")
    sock.close()

# 5. Prueba HTTP básica
print(f"\n🌐 4. PRUEBA HTTP BÁSICA:")
try:
    # Probar con socket primero
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    sock.connect((ip, 80))
    
    # Enviar petición manual
    request = f"GET / HTTP/1.1\r\nHost: {ip}\r\nConnection: close\r\n\r\n"
    sock.send(request.encode())
    
    # Recibir respuesta
    response = sock.recv(1024).decode()
    print(f"   ✅ Socket responde: {response[:50]}...")
    sock.close()
except Exception as e:
    print(f"   ❌ Socket error: {e}")

# 6. Prueba con urllib (la que usa tu código)
print(f"\n🐍 5. PRUEBA CON URLLIB:")
try:
    # Probar página principal
    response = urllib.request.urlopen(f"{URL_CAMARA}/", timeout=3)
    print(f"   ✅ / responde: HTTP {response.getcode()}")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    response.close()
except Exception as e:
    print(f"   ❌ Error en /: {type(e).__name__}: {e}")

try:
    # Probar /capture
    print(f"\n📸 6. PRUEBA DE CAPTURA:")
    response = urllib.request.urlopen(f"{URL_CAMARA}/capture", timeout=5)
    print(f"   ✅ /capture responde: HTTP {response.getcode()}")
    print(f"   Tamaño: {len(response.read())} bytes")
    response.close()
except Exception as e:
    print(f"   ❌ Error en capture: {type(e).__name__}: {e}")

# 7. Solución específica
print("\n" + "="*70)
print("🔧 DIAGNÓSTICO Y SOLUCIÓN:")
if red_pc != red_cam:
    print("❌ PROBLEMA: PC y cámara en diferentes redes")
    print("   SOLUCIÓN: Conecta ambos a la MISMA red WiFi")
elif not result or result.returncode != 0:
    print("❌ PROBLEMA: Ping falla pero IP parece correcta")
    print("   SOLUCIÓN: Firewall bloqueando. Desactívalo temporalmente")
else:
    print("✅ La cámara responde a ping pero Python falla")
    print("   SOLUCIÓN PROBABLE: Firewall de Python/Windows")
    print("   Intenta:")
    print("   1. Ejecutar Python como administrador")
    print("   2. Desactivar firewall temporalmente")
    print("   3. Agregar Python a excepciones del firewall")
print("="*70)