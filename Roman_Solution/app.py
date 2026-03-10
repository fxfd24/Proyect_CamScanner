from flask import Flask, render_template, request, jsonify
import requests, os, base64, serial
from deepface import DeepFace

app = Flask(__name__)

# --- КОНФИГУРАЦИЯ ---
CAPTURE_URL = "http://192.168.1.29/capture"
DB_PATH = "db"
TEMP_FILE = "temp_capture.jpg"
ARDUINO_PORT = "COM19"  # УБЕДИСЬ, ЧТО ЭТОТ ПОРТ ВЕРНЫЙ
BAUD_RATE = 9600

# Создаем папку БД
os.makedirs(DB_PATH, exist_ok=True)

# Инициализация Arduino
try:
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    print(f"✅ Arduino успешно подключена к {ARDUINO_PORT}")
except Exception as e:
    ser = None
    print(f"⚠️ Ошибка Arduino (проверь порт!): {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture_photo', methods=['POST'])
def capture():
    try:
        resp = requests.get(CAPTURE_URL, timeout=10)
        if resp.status_code == 200:
            with open(TEMP_FILE, 'wb') as f: f.write(resp.content)
            img_b64 = base64.b64encode(resp.content).decode('utf-8')
            return jsonify({"status": "success", "image": img_b64})
        return jsonify({"status": "error", "message": "Камера не ответила"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/save_to_db', methods=['POST'])
def save():
    data = request.json
    name = data.get('name')
    if name and os.path.exists(TEMP_FILE):
        os.replace(TEMP_FILE, os.path.join(DB_PATH, f"{name}.jpg"))
        return jsonify({"status": "success", "message": f"Пользователь {name} сохранен!"})
    return jsonify({"status": "error", "message": "Ошибка сохранения"})

@app.route('/clear', methods=['POST'])
def clear():
    if os.path.exists(TEMP_FILE): os.remove(TEMP_FILE)
    return jsonify({"status": "cleared"})

@app.route('/verify', methods=['POST'])
def verify():
    if not os.path.exists(TEMP_FILE):
        return jsonify({"status": "error", "message": "Нет фото для проверки"})
    
    try:
        # Проверка через DeepFace
        results = DeepFace.find(
            img_path=TEMP_FILE, 
            db_path=DB_PATH, 
            model_name="Facenet512",
            detector_backend="mtcnn",
            silent=True
        )
        
        # Если нашли совпадение с расстоянием < 0.40
        if len(results) > 0 and not results[0].empty and results[0].iloc[0]['distance'] < 0.40:
            person = os.path.basename(results[0].iloc[0]['identity']).split('.')[0]
            distance = results[0].iloc[0]['distance']
            
            # ОТКРЫВАЕМ!
            if ser: ser.write(b'1') 
            return jsonify({"status": "success", "message": f"Доступ разрешен: {person} (Dist: {distance:.3f})"})
        
        # ОТКАЗ!
        if ser: ser.write(b'0')
        return jsonify({"status": "fail", "message": "Доступ запрещен: Лицо не опознано"})
            
    except Exception as e:
        print(f"Error: {e}")
        if ser: ser.write(b'0')
        return jsonify({"status": "error", "message": "Ошибка верификации"})

if __name__ == '__main__':
    # Меняем debug=True на debug=False
    # И добавляем use_reloader=False, чтобы он не перезапускал скрипт лишний раз
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)