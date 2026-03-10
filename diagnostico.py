import socket
import urllib.request
import subprocess
import sys

URL_CAMARA = "http://192.168.1.246"
ip = URL_CAMARA.replace("http://", "")

print("="*70)
print("🔍 DIAGNÓSTICO DE CONEXIÓN ESP32-CAM")
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

# 3. Ping
print(f"\n📡 2. PING a {ip}:")
try:
    param = '-n' if sys.platform.lower() == 'win32' else '-c'
    result = subprocess.run(['ping', param, '1', ip], 
                          capture_output=True, text=True, timeout=3)
    if result.returncode == 0:
        print("   ✅ PING EXITOSO")
    else:
        print("   ❌ PING FALLÓ")
except Exception as e:
    print(f"   ⚠️ Error: {e}")

# 4. Puerto 80
print(f"\n🔌 3. PUERTO 80:")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex((ip, 80))
if result == 0:
    print("   ✅ Puerto 80 ABIERTO")
else:
    print(f"   ❌ Puerto 80 CERRADO (código {result})")
sock.close()

# 5. Prueba HTTP
print(f"\n🌐 4. PRUEBA HTTP:")
try:
    response = urllib.request.urlopen(f"{URL_CAMARA}/", timeout=3)
    print(f"   ✅ Servidor web responde: HTTP {response.getcode()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 6. Prueba capture
print(f"\n📸 5. PRUEBA CAPTURE:")
try:
    response = urllib.request.urlopen(f"{URL_CAMARA}/capture", timeout=3)
    print(f"   ✅ /capture responde: {len(response.read())} bytes")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*70)