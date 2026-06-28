import face_recognition
import cv2
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import shutil
import webbrowser
import sqlite3
import json
import time

# ---------------------------------------------------------
# ЦВЕТОВАЯ ПАЛИТРА (Стиль "Мягкая пастель / Soft Dashboard")
# ---------------------------------------------------------
BG_COLOR = "#F4F1DE"       
FG_COLOR = "#3D405B"       
BTN_SCAN = "#81B29A"       
BTN_UPLOAD = "#F2CC8F"     
BTN_TAKE = "#B7B2E3"       
BTN_REC = "#E07A5F"        
BTN_CAM = "#A8DADC"        
BTN_MASK = "#B5838D"       
LOG_BG = "#F8F9FA"         
TEXT_MUTED = "#8D99AE"     

# ---------------------------------------------------------
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ И СТАНДАРТЫ
# ---------------------------------------------------------
known_faces = []
known_names = []
dataset_folder = "dataset"
MAX_IMAGE_WIDTH = 800  # Единый стандарт ширины для всех изображений

if not os.path.exists(dataset_folder):
    os.makedirs(dataset_folder)

# ---------------------------------------------------------
# ФУНКЦИЯ: ЕДИНЫЙ СТАНДАРТ РАЗМЕРА ИЗОБРАЖЕНИЙ
# ---------------------------------------------------------
def resize_to_standard(image):
    """Приводит изображение к единому стандарту по ширине с сохранением пропорций"""
    if image is None:
        return None
    
    h, w = image.shape[:2]
    if w > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / w
        new_h = int(h * ratio)
        # Используем INTER_AREA для качественного уменьшения без лесенок
        return cv2.resize(image, (MAX_IMAGE_WIDTH, new_h), interpolation=cv2.INTER_AREA)
    return image

# ---------------------------------------------------------
# БАЗА ДАННЫХ (SQLite)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("faces_database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS encodings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            encoding_data TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def add_user_to_db(name, face_encoding):
    conn = sqlite3.connect("faces_database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        cursor.execute("INSERT OR IGNORE INTO users (name) VALUES (?)", (name,))
        cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
        user_id = cursor.fetchone()[0]
        
        encoding_json = json.dumps(face_encoding.tolist())
        cursor.execute("INSERT INTO encodings (user_id, encoding_data) VALUES (?, ?)", (user_id, encoding_json))
        conn.commit()
        return True
    except Exception as e:
        log(f"[X] Ошибка работы с БД: {e}")
        return False
    finally:
        conn.close()

def load_all_faces_from_db():
    conn = sqlite3.connect("faces_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.name, encodings.encoding_data 
        FROM encodings 
        JOIN users ON encodings.user_id = users.id
    ''')
    
    db_faces = []
    db_names = []
    
    for name, encoding_json in cursor.fetchall():
        encoding_list = json.loads(encoding_json)
        face_array = np.array(encoding_list, dtype=np.float64)
        db_names.append(name)
        db_faces.append(face_array)
        
    conn.close()
    return db_faces, db_names

init_db()

# ---------------------------------------------------------
# ФУНКЦИИ АНИМАЦИИ ИНТЕРФЕЙСА
# ---------------------------------------------------------
def add_hover_effect(button, normal_color, hover_color):
    button.bind("<Enter>", lambda e: button.config(bg=hover_color))
    button.bind("<Leave>", lambda e: button.config(bg=normal_color))

def lighten_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, int(r * 1.15))
    g = min(255, int(g * 1.15))
    b = min(255, int(b * 1.15))
    return f"#{r:02x}{g:02x}{b:02x}"

def log(message):
    log_text.config(state='normal')
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)
    log_text.config(state='disabled')

# ---------------------------------------------------------
# ФУНКЦИИ ЛОГИКИ ПРОГРАММЫ
# ---------------------------------------------------------
def scan_database_thread():
    btn_scan.config(state=tk.DISABLED)
    global known_faces, known_names
    
    log("=== ЗАГРУЗКА ИЗ БАЗЫ ДАННЫХ ===")
    
    faces, names = load_all_faces_from_db()
    known_faces = faces
    known_names = names
                    
    log(f"=== ГОТОВО! Загружено {len(known_faces)} лиц. ===\n")
    btn_scan.config(state=tk.NORMAL)

def start_scanning():
    threading.Thread(target=scan_database_thread, daemon=True).start()

def upload_to_database():
    folder_path = filedialog.askdirectory(title="Выберите папку с фотографиями одного человека")
    if not folder_path: return 
        
    valid_extensions = (".jpg", ".jpeg", ".png")
    file_paths = [
        os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)
    ]
    
    if not file_paths:
        messagebox.showwarning("Внимание", "В выбранной папке не найдено изображений (.jpg, .png)!")
        return

    existing_names = [d for d in os.listdir(dataset_folder) if os.path.isdir(os.path.join(dataset_folder, d))]

    dialog = tk.Toplevel(root)
    dialog.title("Добавление папки")
    dialog.geometry("380x180")
    dialog.configure(bg=BG_COLOR)
    dialog.transient(root) 
    dialog.grab_set()      

    tk.Label(dialog, text=f"Найдено изображений: {len(file_paths)}\nКому принадлежат эти лица?", bg=BG_COLOR, fg=FG_COLOR, font=("Helvetica", 11)).pack(pady=10)
    
    combo = ttk.Combobox(dialog, values=existing_names, width=35, font=("Helvetica", 10))
    combo.pack(pady=5)
    
    result_name = tk.StringVar()

    def on_ok():
        name = combo.get().strip()
        if name:
            result_name.set(name)
            dialog.destroy()
        else:
            messagebox.showwarning("Ошибка", "Имя не может быть пустым!", parent=dialog)

    btn_frame = tk.Frame(dialog, bg=BG_COLOR)
    btn_frame.pack(pady=15)
    
    tk.Button(btn_frame, text="Загрузить папку", command=on_ok, bg=BTN_SCAN, fg="white", font=("Helvetica", 10, "bold"), relief="flat").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Отмена", command=dialog.destroy, bg="#E5E5E5", fg=FG_COLOR, font=("Helvetica", 10, "bold"), relief="flat").pack(side=tk.LEFT, padx=10)

    root.wait_window(dialog)
    person_name = result_name.get()
    if not person_name: return 

    def process_folder():
        log(f"Начата обработка ({len(file_paths)} фото) для '{person_name}'...")
        success_count = 0
        
        for path in file_paths:
            filename = os.path.basename(path)
            try:
                # Читаем фото (уже в RGB формате)
                image_rgb = face_recognition.load_image_file(path)
                
                # Применяем ЕДИНЫЙ СТАНДАРТ РАЗМЕРА
                image_rgb = resize_to_standard(image_rgb)
                
                encodings = face_recognition.face_encodings(image_rgb)
                
                if len(encodings) == 0:
                    log(f"    [-] Пропуск {filename}: лицо не найдено.")
                    continue
                    
                face_encoding = encodings[0]
                
                if add_user_to_db(person_name, face_encoding):
                    person_folder = os.path.join(dataset_folder, person_name)
                    os.makedirs(person_folder, exist_ok=True)
                    destination = os.path.join(person_folder, filename)
                    
                    # Сохраняем стандартизированное фото в базу, обходя проблемы с кириллицей
                    bgr_save = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                    ext = os.path.splitext(destination)[1]
                    if not ext: ext = ".jpg"
                    
                    result, nparr = cv2.imencode(ext, bgr_save)
                    if result:
                        with open(destination, 'wb') as f:
                            f.write(nparr.tobytes())
                            
                    success_count += 1
                    
            except Exception as e:
                log(f"    [X] Ошибка обработки {filename}: {e}")
                
        log(f"[+] Из папки успешно сохранено {success_count} из {len(file_paths)} лиц!")
        log("Не забудьте нажать 'Обновить базу'.\n")

    threading.Thread(target=process_folder, daemon=True).start()

def take_photo_from_camera():
    def run_capture():
        log("Запуск камеры для создания снимка... (Нажмите Пробел для фото, Q для выхода)")
        video_capture = cv2.VideoCapture(0)
        
        captured_frame = None
        while True:
            ret, frame = video_capture.read()
            if not ret: break

            preview = frame.copy()
            cv2.rectangle(preview, (10, 10), (410, 45), (45, 42, 40), -1)
            cv2.putText(preview, "Пробел - Сделать снимок | Q - Выход", (20, 33), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            
            cv2.imshow('Создание снимка', preview)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '): 
                captured_frame = frame
                break
            elif key in [ord('q'), ord('Q')]:
                break
            
            try:
                if cv2.getWindowProperty('Создание снимка', cv2.WND_PROP_VISIBLE) < 1:
                    break
            except:
                break
                
        video_capture.release()
        cv2.destroyAllWindows()
        
        if captured_frame is not None:
            root.after(0, lambda: save_captured_photo(captured_frame))
        else:
            log("Создание снимка отменено пользователем.\n")

    threading.Thread(target=run_capture, daemon=True).start()

def save_captured_photo(frame):
    existing_names = [d for d in os.listdir(dataset_folder) if os.path.isdir(os.path.join(dataset_folder, d))]

    dialog = tk.Toplevel(root)
    dialog.title("Сохранение снимка")
    dialog.geometry("380x180")
    dialog.configure(bg=BG_COLOR)
    dialog.transient(root) 
    dialog.grab_set()      

    tk.Label(dialog, text="Кому принадлежит лицо на снимке?", bg=BG_COLOR, fg=FG_COLOR, font=("Helvetica", 11)).pack(pady=10)
    
    combo = ttk.Combobox(dialog, values=existing_names, width=35, font=("Helvetica", 10))
    combo.pack(pady=5)
    
    result_name = tk.StringVar()

    def on_ok():
        name = combo.get().strip()
        if name:
            result_name.set(name)
            dialog.destroy()
        else:
            messagebox.showwarning("Ошибка", "Имя не может быть пустым!", parent=dialog)

    btn_frame = tk.Frame(dialog, bg=BG_COLOR)
    btn_frame.pack(pady=15)
    
    tk.Button(btn_frame, text="Сохранить снимок", command=on_ok, bg=BTN_SCAN, fg="white", font=("Helvetica", 10, "bold"), relief="flat").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Отмена", command=dialog.destroy, bg="#E5E5E5", fg=FG_COLOR, font=("Helvetica", 10, "bold"), relief="flat").pack(side=tk.LEFT, padx=10)

    root.wait_window(dialog)
    person_name = result_name.get()
    if not person_name: 
        log("Сохранение снимка отменено.\n")
        return 

    def process_captured():
        log(f"Обработка сделанного снимка для '{person_name}'...")
        try:
            # Применяем ЕДИНЫЙ СТАНДАРТ РАЗМЕРА
            std_frame = resize_to_standard(frame)
            
            # ИСПРАВЛЕНИЕ ОШИБКИ ПАМЯТИ: Строго используем cv2.cvtColor вместо срезов [::-1]
            image_rgb = cv2.cvtColor(std_frame, cv2.COLOR_BGR2RGB)
            
            encodings = face_recognition.face_encodings(image_rgb)
            
            if len(encodings) == 0:
                log("    [-] Ошибка: На фото лицо не обнаружено. Повторите попытку при хорошем освещении.")
                messagebox.showerror("Ошибка распознавания", "Лицо не найдено! Сделайте новый снимок, смотря прямо в камеру.", parent=root)
                return
                
            face_encoding = encodings[0]
            
            if add_user_to_db(person_name, face_encoding):
                person_folder = os.path.join(dataset_folder, person_name)
                os.makedirs(person_folder, exist_ok=True)
                
                filename = f"camera_{int(time.time())}.jpg"
                destination = os.path.join(person_folder, filename)
                
                # Безопасное сохранение
                ext = os.path.splitext(destination)[1]
                result, nparr = cv2.imencode(ext, std_frame)
                if result:
                    with open(destination, 'wb') as f:
                        f.write(nparr.tobytes())
                
                log(f"[+] Снимок успешно сохранен в базу для '{person_name}'!")
                log("Не забудьте нажать 'Обновить базу'.\n")
                messagebox.showinfo("Успех", f"Фотография успешно добавлена для {person_name}!", parent=root)
        except Exception as e:
            log(f"    [X] Ошибка обработки снимка: {e}")

    threading.Thread(target=process_captured, daemon=True).start()

def recognize_photo():
    if not known_faces:
        messagebox.showwarning("Внимание", "База пуста! Нажмите 'Обновить базу данных'.")
        return

    file_path = filedialog.askopenfilename(title="Выберите фото", filetypes=[("Изображения", "*.jpg *.jpeg *.png")])
    if not file_path: return

    log("Анализ фотографии...")
    
    try:
        image_rgb = face_recognition.load_image_file(file_path)
        
        # Применяем ЕДИНЫЙ СТАНДАРТ РАЗМЕРА перед показом
        image_rgb = resize_to_standard(image_rgb)
        
        bgr_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        process_and_show_image(image_rgb, bgr_image, "Результат распознавания")
    except Exception as e:
        log(f"    [X] Ошибка: Не удалось загрузить или обработать изображение. {e}")

def process_and_show_image(rgb_image, bgr_image, window_title):
    face_locations = face_recognition.face_locations(rgb_image)
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.55)
        name = "Неизвестный"
        color = (130, 130, 255) 

        if True in matches:
            best_match_index = np.argmin(face_recognition.face_distance(known_faces, face_encoding))
            if matches[best_match_index]:
                name = known_names[best_match_index]
                color = (180, 220, 150) 

        cv2.rectangle(bgr_image, (left, top), (right, bottom), color, 2)
        cv2.putText(bgr_image, name, (left, top - 10), cv2.FONT_HERSHEY_DUPLEX, 0.6, color, 1)

    log("Анализ завершен!\n")
    cv2.imshow(window_title, bgr_image)
    cv2.waitKey(0)
    cv2.destroyWindow(window_title)

def recognize_webcam():
    if not known_faces:
        messagebox.showwarning("Внимание", "База пуста! Отсканируйте базу перед запуском камеры.")
        return

    def run_webcam():
        log("Запуск веб-камеры... (Нажмите 'Q' в окне камеры для выхода)")
        video_capture = cv2.VideoCapture(0)
        
        while True:
            ret, frame = video_capture.read()
            if not ret: break

            # Применяем ЕДИНЫЙ СТАНДАРТ РАЗМЕРА к окну камеры
            frame = resize_to_standard(frame)

            # Уменьшаем копию исключительно для быстрого анализа лиц
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            
            # ИСПРАВЛЕНИЕ ОШИБКИ ПАМЯТИ: Строгая конвертация cv2.cvtColor
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.55)
                name = "Неизвестный"
                color = (130, 130, 255)

                if True in matches:
                    best_match_index = np.argmin(face_recognition.face_distance(known_faces, face_encoding))
                    name = known_names[best_match_index]
                    color = (180, 220, 150)

                top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, name, (left, bottom + 25), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1)

            cv2.imshow('Live Face Recognition (Press Q to exit)', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
        log("Веб-камера отключена.\n")

    threading.Thread(target=run_webcam, daemon=True).start()

def analyze_landmarks():
    file_path = filedialog.askopenfilename(title="Выберите фото для топографии", filetypes=[("Изображения", "*.jpg *.jpeg *.png")])
    if not file_path: return

    log("Построение маски черт лица...")
    
    try:
        image_rgb = face_recognition.load_image_file(file_path)
        
        # Применяем ЕДИНЫЙ СТАНДАРТ РАЗМЕРА
        image_rgb = resize_to_standard(image_rgb)
        bgr_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        
        face_landmarks_list = face_recognition.face_landmarks(image_rgb)
        
        for face_landmarks in face_landmarks_list:
            for facial_feature in face_landmarks.keys():
                points = np.array(face_landmarks[facial_feature], np.int32)
                cv2.polylines(bgr_image, [points], isClosed=False, color=(255, 230, 200), thickness=2)

        cv2.imshow("Facial Landmarks", bgr_image)
        cv2.waitKey(0)
        cv2.destroyWindow("Facial Landmarks")
    except Exception as e:
        log(f"    [X] Ошибка анализа: {e}")

def open_github(event):
    webbrowser.open("https://github.com/KiviPups")

# ---------------------------------------------------------
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС (GUI) - DASHBOARD
# ---------------------------------------------------------
root = tk.Tk()
root.title("Умное распознавание лиц")
root.geometry("850x550")
root.configure(bg="#FFFFFF")
root.minsize(700, 450)

sidebar = tk.Frame(root, bg=BG_COLOR, width=280)
sidebar.pack(side=tk.LEFT, fill=tk.Y)
sidebar.pack_propagate(False)

title_label = tk.Label(sidebar, text="FACE\nRECOGNITION", font=("Helvetica", 16, "bold"), bg=BG_COLOR, fg=FG_COLOR)
title_label.pack(pady=(30, 30))

btn_scan = tk.Button(sidebar, text="🔄 Обновить базу", width=22, height=2, bg=BTN_SCAN, fg="white", font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=start_scanning, anchor="w", padx=20)
btn_scan.pack(pady=6, padx=20, fill=tk.X)
add_hover_effect(btn_scan, BTN_SCAN, lighten_color(BTN_SCAN))

btn_upload = tk.Button(sidebar, text="📁 Загрузить папку лиц", width=22, height=2, bg=BTN_UPLOAD, fg=FG_COLOR, font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=upload_to_database, anchor="w", padx=20)
btn_upload.pack(pady=6, padx=20, fill=tk.X)
add_hover_effect(btn_upload, BTN_UPLOAD, lighten_color(BTN_UPLOAD))

btn_take = tk.Button(sidebar, text="📸 Сделать снимок", width=22, height=2, bg=BTN_TAKE, fg=FG_COLOR, font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=take_photo_from_camera, anchor="w", padx=20)
btn_take.pack(pady=6, padx=20, fill=tk.X)
add_hover_effect(btn_take, BTN_TAKE, lighten_color(BTN_TAKE))

btn_recognize = tk.Button(sidebar, text="🖼 Распознать (Фото)", width=22, height=2, bg=BTN_REC, fg=FG_COLOR, font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=recognize_photo, anchor="w", padx=20)
btn_recognize.pack(pady=6, padx=20, fill=tk.X)
add_hover_effect(btn_recognize, BTN_REC, lighten_color(BTN_REC))

btn_cam = tk.Button(sidebar, text="🎥 Распознать (Web)", width=22, height=2, bg=BTN_CAM, fg=FG_COLOR, font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=recognize_webcam, anchor="w", padx=20)
btn_cam.pack(pady=6, padx=20, fill=tk.X)
add_hover_effect(btn_cam, BTN_CAM, lighten_color(BTN_CAM))

btn_mask = tk.Button(sidebar, text="🎭 Анализ лица", width=22, height=2, bg=BTN_MASK, fg=FG_COLOR, font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=analyze_landmarks, anchor="w", padx=20)
btn_mask.pack(pady=6, padx=20, fill=tk.X)
add_hover_effect(btn_mask, BTN_MASK, lighten_color(BTN_MASK))

github_label = tk.Label(sidebar, text="💻 github.com/KiviPups", bg=BG_COLOR, fg=TEXT_MUTED, font=("Helvetica", 9, "underline"), cursor="hand2")
github_label.pack(side=tk.BOTTOM, pady=20)
github_label.bind("<Button-1>", open_github) 

main_area = tk.Frame(root, bg="#FFFFFF")
main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

header_frame = tk.Frame(main_area, bg="#FFFFFF")
header_frame.pack(fill=tk.X, pady=25, padx=30)
tk.Label(header_frame, text="Панель управления", font=("Helvetica", 18, "bold"), bg="#FFFFFF", fg=FG_COLOR).pack(side=tk.LEFT)

log_frame = tk.Frame(main_area, bg="#FFFFFF")
log_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))

tk.Label(log_frame, text="Системный журнал событий:", bg="#FFFFFF", fg=TEXT_MUTED, font=("Helvetica", 10)).pack(anchor="w", pady=(0, 10))

log_text = tk.Text(log_frame, state='disabled', bg=LOG_BG, fg=FG_COLOR, 
                   font=("Consolas", 10), relief="flat", padx=15, pady=15, 
                   highlightthickness=1, highlightbackground="#E2E2E2")
log_text.pack(fill=tk.BOTH, expand=True)

log("Система успешно обновлена. База данных SQLite подключена.")
log(f"Внедрен единый стандарт размера изображений (макс. ширина: {MAX_IMAGE_WIDTH}px).")
log("Устранена ошибка совместимости форматов памяти (dlib + cv2).")
log("Пожалуйста, нажмите 'Обновить базу', чтобы загрузить данные.\n")

root.mainloop()