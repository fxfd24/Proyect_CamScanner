"""
03_Codigo_Python/facial_recognition_system.py

OPTIMIZED CONFIGURATION BASED ON REAL TEST RESULTS:
- Best accuracy: Facenet512 + retinaface (0.0290) ⭐
- Best speed/balance: Facenet512 + mtcnn (0.0457) ✅
- Alternative: ArcFace + mtcnn (0.0970) 🥉

IMPROVEMENTS:
- ✅ Face verification during capture
- ✅ Retry mechanism for failed detections
- ✅ Lighting advice
- ✅ Robust error handling
"""

import cv2
import serial
import numpy as np
import os
import time
import pickle
from datetime import datetime
from deepface import DeepFace
import urllib.request
import socket
from collections import Counter

# ============================================
# CONFIGURATION
# ============================================
CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))

CAMERA_URL = "http://192.168.1.246"
ARDUINO_PORT = "COM6"

DB_PATH = os.path.join(CURRENT_FOLDER, "db")
RECORDS_PATH = os.path.join(CURRENT_FOLDER, "records")
REPRESENTATIONS_PATH = os.path.join(DB_PATH, "representations_facenet.pkl")

# Timeouts
CONNECTION_TIMEOUT = 3
CAPTURE_TIMEOUT = 8

# Number of photos
REGISTRATION_PHOTOS = 3
RECOGNITION_PHOTOS = 2

# Max retries for face detection
MAX_RETRIES = 3

# ============================================
# OPTIMIZED CONFIGURATIONS (BASED ON TEST RESULTS)
# ============================================
CONFIGS = {
    "best_accuracy": {
        "name": "🎯 BEST ACCURACY",
        "model": "Facenet512",
        "detector": "retinaface",
        "threshold": 0.12,        # Based on 0.0290 distance
        "distance": 0.0290,
        "speed": "slow"
    },
    "balanced": {
        "name": "⚖️ BALANCED (RECOMMENDED)",
        "model": "Facenet512",
        "detector": "mtcnn",
        "threshold": 0.18,         # Based on 0.0457 distance
        "distance": 0.0457,
        "speed": "fast"
    },
    "alternative": {
        "name": "🔄 ALTERNATIVE",
        "model": "ArcFace",
        "detector": "mtcnn",
        "threshold": 0.35,         # Based on 0.0970 distance
        "distance": 0.0970,
        "speed": "fast"
    }
}

# Default to balanced configuration
active_config = "balanced"
RECOGNITION_MODEL = CONFIGS[active_config]["model"]
RECOGNITION_DETECTOR = CONFIGS[active_config]["detector"]
RECOGNITION_THRESHOLD = CONFIGS[active_config]["threshold"]

# ============================================
# CREATE FOLDERS
# ============================================
os.makedirs(DB_PATH, exist_ok=True)
os.makedirs(RECORDS_PATH, exist_ok=True)
print(f"📁 DB: {DB_PATH}")
print(f"📁 Records: {RECORDS_PATH}")

# ============================================
# ARDUINO CONNECTION
# ============================================
arduino = None
try:
    arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)
    time.sleep(2)
    print(f"✅ Arduino connected on {ARDUINO_PORT}")
except Exception as e:
    print(f"⚠️ Could not connect to Arduino: {e}")

# ============================================
# FUNCTION: Check camera connection
# ============================================
def check_connection():
    """Verify camera connection"""
    print("\n🔍 CHECKING CAMERA CONNECTION:")
    ip = CAMERA_URL.replace("http://", "")
    
    try:
        socket.gethostbyname(ip)
        print(f"   ✅ IP {ip} is valid")
    except:
        print(f"   ❌ IP {ip} is not valid")
        return False
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((ip, 80))
    if result == 0:
        print(f"   ✅ Port 80 is open")
    else:
        print(f"   ❌ Port 80 is closed")
        return False
    sock.close()
    
    try:
        response = urllib.request.urlopen(f"{CAMERA_URL}/capture", timeout=CONNECTION_TIMEOUT)
        print(f"   ✅ Camera responds")
        return True
    except Exception as e:
        print(f"   ❌ Camera error: {e}")
        return False

# ============================================
# FUNCTION: Capture image
# ============================================
def capture_image(attempts=2):
    """Request photo from ESP32-CAM"""
    for attempt in range(attempts):
        try:
            print(f"📡 Requesting photo (attempt {attempt+1}/{attempts})...")
            
            req = urllib.request.Request(
                f"{CAMERA_URL}/capture",
                headers={'User-Agent': 'Python/Recognition', 'Cache-Control': 'no-cache'}
            )
            
            with urllib.request.urlopen(req, timeout=CAPTURE_TIMEOUT) as response:
                img_array = np.array(bytearray(response.read()), dtype=np.uint8)
                img = cv2.imdecode(img_array, -1)
                
            if img is None:
                print("❌ Could not decode image")
                continue
                
            print(f"✅ Photo received: {img.shape[1]}x{img.shape[0]} pixels")
            return img
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt < attempts - 1:
                print("   Retrying...")
                time.sleep(1)
    
    return None

# ============================================
# FUNCTION: Give lighting advice
# ============================================
def give_lighting_advice(img):
    """Give advice about lighting conditions"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    
    if brightness < 50:
        print("   💡 Advice: Too dark, need more light")
        return False
    elif brightness > 200:
        print("   💡 Advice: Too bright, avoid direct light")
        return False
    else:
        print("   💡 Advice: Good lighting!")
        return True

# ============================================
# FUNCTION: Verify face in image
# ============================================
def verify_face_in_image(img, silent=False):
    """Check if image contains a detectable face"""
    temp_path = os.path.join(CURRENT_FOLDER, "temp_face_check.jpg")
    cv2.imwrite(temp_path, img)
    
    try:
        DeepFace.represent(
            img_path=temp_path,
            model_name=RECOGNITION_MODEL,
            detector_backend=RECOGNITION_DETECTOR,
            enforce_detection=True,
            align=True,
            silent=True
        )
        if not silent:
            print("   ✅ Face detected")
        return True
    except:
        if not silent:
            print("   ❌ No face detected")
        return False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ============================================
# FUNCTION: List registered people
# ============================================
def list_registered():
    """Show all registered people in the database"""
    if not os.path.exists(DB_PATH):
        print("📁 DB folder not found")
        return
    
    # Get all jpg files (excluding angle photos for cleaner list)
    all_files = [f for f in os.listdir(DB_PATH) if f.endswith('.jpg')]
    
    # Filter out angle photos for main list
    main_photos = [f for f in all_files if '_angle' not in f]
    angle_photos = [f for f in all_files if '_angle' in f]
    
    if not main_photos:
        print("📭 No registered people")
        return
    
    print(f"\n👥 REGISTERED PEOPLE ({len(main_photos)}):")
    print("-"*40)
    
    for i, file in enumerate(sorted(main_photos), 1):
        # Get base name without extension and clean it
        name = file.replace('.jpg', '').replace('_', ' ').title()
        
        # Count how many photos this person has (including angles)
        base_name = file.replace('.jpg', '')
        person_photos = [f for f in all_files if f.startswith(base_name) or 
                        f.startswith(base_name.replace(' ', '_'))]
        photo_count = len(person_photos)
        
        print(f"   {i}. {name} ({photo_count} photos)")
    
    # Show statistics
    print("-"*40)
    print(f"📊 Statistics:")
    print(f"   • Total people: {len(main_photos)}")
    print(f"   • Total photos: {len(all_files)}")
    print(f"   • Angle photos: {len(angle_photos)}")
    
    # Show representation file info
    if os.path.exists(REPRESENTATIONS_PATH):
        size_kb = os.path.getsize(REPRESENTATIONS_PATH) / 1024
        size_mb = size_kb / 1024
        if size_mb > 1:
            print(f"   • Face database: {size_mb:.2f} MB")
        else:
            print(f"   • Face database: {size_kb:.1f} KB")
    else:
        print(f"   • Face database: Not generated yet")

# ============================================
# FUNCTION: Register new person (IMPROVED)
# ============================================
def register_person():
    """Register new person with 3 photos and quality checks"""
    print("\n" + "="*60)
    print("📝 REGISTRATION MODE")
    print("="*60)
    
    name = input("👤 Enter person's name: ").strip()
    if not name:
        print("❌ Invalid name")
        return False
    
    clean_name = name.replace(" ", "_").lower()
    full_path = os.path.join(DB_PATH, f"{clean_name}.jpg")
    
    if os.path.exists(full_path):
        print(f"⚠️ {name} already exists")
        list_registered()
        overwrite = input("Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            return False
    
    print(f"\n📸 Capturing {REGISTRATION_PHOTOS} photos...")
    print("   👉 Look straight, left, and right")
    print("   👉 Ensure good lighting on your face")
    
    photos = []
    
    for i in range(REGISTRATION_PHOTOS):
        print(f"\n--- Photo {i+1}/{REGISTRATION_PHOTOS} ---")
        if i == 0:
            print("   👉 Look STRAIGHT at camera")
        elif i == 1:
            print("   👉 Look SLIGHTLY LEFT")
        else:
            print("   👉 Look SLIGHTLY RIGHT")
        
        # Try to get a valid face photo with retries
        face_detected = False
        retries = 0
        
        while not face_detected and retries < MAX_RETRIES:
            img = capture_image(attempts=2)
            if img is None:
                retries += 1
                continue
            
            # Check lighting
            lighting_ok = give_lighting_advice(img)
            
            # Check for face
            if verify_face_in_image(img):
                face_detected = True
                photos.append(img)
                print(f"   ✅ Photo {i+1} captured successfully")
            else:
                retries += 1
                if retries < MAX_RETRIES:
                    print(f"   ⚠️ Retry {retries}/{MAX_RETRIES}...")
        
        if not face_detected:
            print(f"❌ Failed to capture valid face for photo {i+1}")
            return False
        
        time.sleep(1)
    
    print("\n🔍 Verifying all photos...")
    
    # Verify all photos have faces
    all_valid = True
    for i, photo in enumerate(photos):
        if not verify_face_in_image(photo, silent=True):
            print(f"❌ Photo {i+1} failed verification")
            all_valid = False
            break
    
    if not all_valid:
        print("❌ Registration failed: Some photos don't contain clear faces")
        return False
    
    # Save all photos
    cv2.imwrite(full_path, photos[0])
    print(f"💾 Saved: {clean_name}.jpg")
    
    for i, photo in enumerate(photos[1:], 2):
        angle_path = os.path.join(DB_PATH, f"{clean_name}_angle{i}.jpg")
        cv2.imwrite(angle_path, photo)
        print(f"💾 Saved: {clean_name}_angle{i}.jpg")
    
    # Clear cache to force regeneration
    if os.path.exists(REPRESENTATIONS_PATH):
        os.remove(REPRESENTATIONS_PATH)
        print("🔄 Face database cache cleared")
    
    print(f"\n✅ {name} registered successfully!")
    return True

# ============================================
# FUNCTION: Delete person
# ============================================
def delete_person():
    """Delete a person from the database"""
    list_registered()
    
    all_files = [f for f in os.listdir(DB_PATH) if f.endswith('.jpg')]
    main_photos = [f for f in all_files if '_angle' not in f]
    
    if not main_photos:
        return
    
    try:
        idx = int(input("\n🔢 Person number to delete: ")) - 1
        if 0 <= idx < len(main_photos):
            file_to_delete = main_photos[idx]
            base_name = file_to_delete.replace('.jpg', '')
            
            print(f"\n🗑️ Files to delete:")
            print(f"   • {file_to_delete}")
            
            # Find and list all related files
            related_files = [f for f in all_files if f.startswith(base_name)]
            for f in related_files[1:]:
                print(f"   • {f}")
            
            confirm = input(f"\nDelete {len(related_files)} file(s)? (y/n): ").lower()
            
            if confirm == 'y':
                for f in related_files:
                    os.remove(os.path.join(DB_PATH, f))
                    print(f"✅ Deleted: {f}")
                
                # Delete representations to regenerate
                if os.path.exists(REPRESENTATIONS_PATH):
                    os.remove(REPRESENTATIONS_PATH)
                    print("🔄 Face database updated")
                
                print(f"\n✅ Person deleted successfully")
            else:
                print("❌ Deletion cancelled")
        else:
            print("❌ Invalid number")
    except ValueError:
        print("❌ Invalid input")

# ============================================
# FUNCTION: Recognize face
# ============================================
def recognize_face(image_path):
    """
    Face recognition using current optimized configuration
    """
    try:
        db_files = [f for f in os.listdir(DB_PATH) if f.endswith('.jpg')]
        if not db_files:
            return "no_records", False, 0, None
        
        results = DeepFace.find(
            img_path=image_path,
            db_path=DB_PATH,
            model_name=RECOGNITION_MODEL,
            detector_backend=RECOGNITION_DETECTOR,
            distance_metric="cosine",
            enforce_detection=True,
            align=True,
            silent=True
        )
        
        if len(results) > 0 and len(results[0]) > 0:
            best_match = results[0].iloc[0]
            file = best_match['identity']
            person = os.path.basename(file).split('.')[0]
            if '_angle' in person:
                person = person.split('_angle')[0]
            distance = best_match['distance']
            
            # Check for ambiguity
            ambiguous = False
            if len(results[0]) > 1:
                second_distance = results[0].iloc[1]['distance']
                if second_distance - distance < 0.08:
                    ambiguous = True
                    print(f"⚠️ Ambiguous match (diff: {second_distance - distance:.4f})")
            
            accepted = distance < RECOGNITION_THRESHOLD and not ambiguous
            
            print(f"\n📊 Results ({RECOGNITION_MODEL}/{RECOGNITION_DETECTOR}):")
            print(f"   • Person: {person}")
            print(f"   • Distance: {distance:.4f}")
            print(f"   • Threshold: {RECOGNITION_THRESHOLD}")
            print(f"   • Accepted: {'✅' if accepted else '❌'}")
            
            return person, accepted, distance, None
        else:
            return "unknown", False, 1.0, None
            
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return "error", False, 1.0, None

# ============================================
# FUNCTION: Process recognition with voting (IMPROVED)
# ============================================
def process_recognition():
    """Recognize with 2 photos and voting - WITH FACE VERIFICATION"""
    print("\n" + "="*60)
    print("🔍 RECOGNITION MODE")
    print("="*60)
    print(f"   {CONFIGS[active_config]['name']}")
    print(f"   Model: {RECOGNITION_MODEL}")
    print(f"   Detector: {RECOGNITION_DETECTOR}")
    print(f"   Threshold: {RECOGNITION_THRESHOLD}")
    print(f"   Test distance: {CONFIGS[active_config]['distance']:.4f}")
    print("="*60)
    
    db_files = [f for f in os.listdir(DB_PATH) if f.endswith('.jpg')]
    if not db_files:
        print("⚠️ No registered people. Use REGISTRATION mode first.")
        return 0
    
    print(f"\n📸 Capturing {RECOGNITION_PHOTOS} photos...")
    print("   👉 Look directly at camera")
    print("   👉 Ensure good lighting")
    
    photos = []
    
    for i in range(RECOGNITION_PHOTOS):
        print(f"\n--- Photo {i+1} ---")
        
        # Try to get a valid face photo with retries
        face_detected = False
        retries = 0
        
        while not face_detected and retries < MAX_RETRIES:
            img = capture_image()
            if img is None:
                retries += 1
                continue
            
            # Check lighting
            give_lighting_advice(img)
            
            # Quick face check
            if verify_face_in_image(img):
                face_detected = True
                photos.append(img)
                print(f"   ✅ Photo {i+1} captured successfully")
            else:
                retries += 1
                if retries < MAX_RETRIES:
                    print(f"   ⚠️ No face detected, retry {retries}/{MAX_RETRIES}...")
        
        if not face_detected:
            print(f"❌ Failed to capture valid face for photo {i+1}")
            if i == 0:
                return 0
            break
    
    if len(photos) < 1:
        print("❌ No valid photos captured")
        return 0
    
    print(f"\n✅ Captured {len(photos)} valid photos")
    
    # Recognize each photo
    results = []
    for i, photo in enumerate(photos):
        print(f"\n--- Analyzing photo {i+1} ---")
        temp_path = os.path.join(CURRENT_FOLDER, f"temp_{i}.jpg")
        cv2.imwrite(temp_path, photo)
        
        person, accepted, distance, _ = recognize_face(temp_path)
        results.append({'person': person, 'accepted': accepted, 'distance': distance})
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Filter out error results
    valid_results = [r for r in results if r['person'] != 'error' and r['distance'] < 1.0]
    
    if len(valid_results) == 0:
        print("\n❌ No valid recognition results")
        final_accepted = False
        final_person = "error"
        avg_distance = 1.0
    elif len(valid_results) < len(photos):
        print(f"\n⚠️ Only {len(valid_results)}/{len(photos)} photos gave valid results")
        # Use the valid results
        accepted_photos = [r for r in valid_results if r['accepted']]
        
        if len(accepted_photos) == len(valid_results):
            persons = [r['person'] for r in accepted_photos]
            if all(p == persons[0] for p in persons):
                final_accepted = True
                final_person = persons[0]
                avg_distance = sum(r['distance'] for r in accepted_photos) / len(accepted_photos)
            else:
                final_accepted = False
                final_person = "conflict"
                avg_distance = 1.0
        else:
            final_accepted = False
            final_person = "unknown"
            avg_distance = 1.0
    else:
        # All photos valid - normal voting
        accepted_photos = [r for r in results if r['accepted']]
        
        if len(accepted_photos) == len(photos):
            persons = [r['person'] for r in accepted_photos]
            if all(p == persons[0] for p in persons):
                final_accepted = True
                final_person = persons[0]
                avg_distance = sum(r['distance'] for r in accepted_photos) / len(accepted_photos)
            else:
                final_accepted = False
                final_person = "conflict"
                avg_distance = 1.0
                print("⚠️ Conflict: Photos matched different people")
        else:
            final_accepted = False
            final_person = "unknown"
            avg_distance = 1.0
            print(f"⚠️ Only {len(accepted_photos)}/{len(photos)} photos accepted")
    
    # Show results
    print("\n" + "="*50)
    print("📊 VOTING RESULTS:")
    print("-"*50)
    for i, r in enumerate(results):
        status = "✅" if r['accepted'] else "❌"
        valid_tag = "" if r['person'] != 'error' else " (invalid)"
        print(f"   Photo {i+1}: {status} {r['person']} ({r['distance']:.4f}){valid_tag}")
    print("-"*50)
    if final_accepted:
        print(f"✅ FINAL: ACCESS GRANTED - {final_person}")
        print(f"   Avg distance: {avg_distance:.4f}")
    else:
        print(f"❌ FINAL: ACCESS DENIED - {final_person}")
    print("="*50)
    
    # Save records
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, (photo, r) in enumerate(zip(photos, results)):
        status = "APPROVED" if final_accepted else "REJECTED"
        clean_name = final_person if final_accepted else r['person']
        filename = os.path.join(RECORDS_PATH, f"{timestamp}_{status}_{clean_name}_{r['distance']:.3f}_photo{i+1}.jpg")
        cv2.imwrite(filename, photo)
        print(f"💾 Saved: {os.path.basename(filename)}")
    
    # Send to Arduino (only if we got valid results)
    if arduino and len(valid_results) > 0:
        cmd = b"OPEN\n" if final_accepted else b"DENIED\n"
        arduino.write(cmd)
        print(f"\n🔴 Arduino: {'OPEN (LED OFF)' if final_accepted else 'DENIED (LED ON)'}")
    elif arduino:
        print("\n⚠️ No valid results - not sending command to Arduino")
    
    return 1 if final_accepted else 0

# ============================================
# FUNCTION: Switch configuration
# ============================================
def switch_config():
    """Switch between different configurations"""
    global active_config, RECOGNITION_MODEL, RECOGNITION_DETECTOR, RECOGNITION_THRESHOLD
    
    print("\n" + "="*50)
    print("🔄 AVAILABLE CONFIGURATIONS:")
    print("-"*50)
    
    configs_list = list(CONFIGS.keys())
    for i, key in enumerate(configs_list, 1):
        config = CONFIGS[key]
        marker = "▶ " if key == active_config else "  "
        print(f"{marker}{i}. {config['name']}")
        print(f"      Model: {config['model']}")
        print(f"      Detector: {config['detector']}")
        print(f"      Threshold: {config['threshold']}")
        print(f"      Test distance: {config['distance']:.4f}")
        print(f"      Speed: {config['speed']}")
        print()
    
    try:
        choice = input(f"Select configuration (1-{len(configs_list)}) or ENTER to cancel: ").strip()
        if choice:
            idx = int(choice) - 1
            if 0 <= idx < len(configs_list):
                new_config = configs_list[idx]
                if new_config != active_config:
                    active_config = new_config
                    RECOGNITION_MODEL = CONFIGS[active_config]["model"]
                    RECOGNITION_DETECTOR = CONFIGS[active_config]["detector"]
                    RECOGNITION_THRESHOLD = CONFIGS[active_config]["threshold"]
                    print(f"\n✅ Switched to: {CONFIGS[active_config]['name']}")
                else:
                    print("\n✅ Already using this configuration")
    except (ValueError, IndexError):
        print("❌ Invalid selection")

# ============================================
# FUNCTION: Test camera with face detection
# ============================================
def test_camera_with_face():
    """Test camera and face detection"""
    print("\n🔧 TESTING CAMERA WITH FACE DETECTION")
    print("="*50)
    
    img = capture_image()
    if img is None:
        print("❌ Could not capture image")
        return
    
    # Show image
    cv2.imshow("Camera Test", img)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()
    
    # Check lighting
    lighting_ok = give_lighting_advice(img)
    
    # Check face
    if verify_face_in_image(img):
        print("✅ Face detection: SUCCESS")
    else:
        print("❌ Face detection: FAILED")
    
    print("="*50)

# ============================================
# MAIN MENU
# ============================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎥 FACIAL RECOGNITION SYSTEM - OPTIMIZED")
    print("="*70)
    print(f"📁 Base folder: {CURRENT_FOLDER}")
    print(f"\n⚙️ ACTIVE CONFIGURATION:")
    print(f"   {CONFIGS[active_config]['name']}")
    print(f"   Model: {RECOGNITION_MODEL}")
    print(f"   Detector: {RECOGNITION_DETECTOR}")
    print(f"   Threshold: {RECOGNITION_THRESHOLD}")
    print(f"   Test distance: {CONFIGS[active_config]['distance']:.4f}")
    print("\n✨ IMPROVEMENTS:")
    print("   • Face verification during capture")
    print("   • Retry mechanism for failed detections")
    print("   • Lighting advice")
    print("   • Robust error handling")
    print("="*70)
    
    # Check camera
    if not check_connection():
        print("\n⚠️ Camera not responding")
        cont = input("Continue anyway? (y/n): ").lower()
        if cont != 'y':
            exit()
    
    while True:
        print("\n" + "-"*60)
        print("📋 MAIN MENU")
        print("-"*60)
        print("   r → 📝 REGISTER new person (3 photos)")
        print("   l → 👥 LIST registered people")
        print("   e → 🗑️ DELETE person")
        print("   enter → 🔍 RECOGNIZE (2 photos, voting)")
        print("   c → 🔄 SWITCH configuration")
        print(f"   Current: {CONFIGS[active_config]['name']}")
        print("   f → 🔧 TEST face detection")
        print("   t → 🔧 TEST camera connection")
        print("   q → ❌ QUIT")
        print("-"*60)
        
        cmd = input("⌨️ Command: ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'r':
            register_person()
        elif cmd == 'l':
            list_registered()
        elif cmd == 'e':
            delete_person()
        elif cmd == 't':
            check_connection()
        elif cmd == 'f':
            test_camera_with_face()
        elif cmd == 'c':
            switch_config()
        elif cmd == '':
            process_recognition()
        else:
            print("❌ Invalid command")
    
    if arduino:
        arduino.close()
    print("\n👋 System terminated")