# FaceID Door System

Система контроля доступа на базе ESP32-CAM, Arduino Uno и Python (DeepFace).

## Быстрый старт (Windows)

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/fxfd24/Proyect_CamScanner.git
cd Roman_Solution
```
2. **Создайте и активируйте виртуальное окружение:**
```bash
python -m venv .venv
.\.venv\Scripts\Activate
```
3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```
4. **Настройка:**
```bash
Откройте app.py и проверьте ARDUINO_PORT.
Убедитесь, что ESP32-CAM подключена к той же Wi-Fi сети, что и ноут, к которому подключен Arduino Uno (Обязательно укажи свой ssid и password).
```
5. **Запуск:**
Прошей при помощи esp32_cam.ino и arduino_uno.ino обе платы и можно запускать веб-интерфейс:
```bash
python app.py
```
Перейдите в браузере по адресу: http://127.0.0.1:5000
