import cv2
import os
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

# ---------------------------------------------------------
# ПАСТЕЛЬНАЯ ПАЛИТРА "Sunny Morning"
# ---------------------------------------------------------
BG_COLOR = "#FFFBF0"       # Нежный кремовый фон
CONTENT_BG = "#FFFFFF"     # Чисто-белый для блоков
ACCENT_COLOR = "#F4D03F"   # Пастельный желтый/золотистый (кнопки)
BTN_HOVER = "#D4AC0D"      # Более насыщенный золотой (наведение)
TEXT_COLOR = "#5D4037"     # Темно-коричневый (для контраста)
MUTED_COLOR = "#A1887F"    # Теплый коричневато-серый (подписи)
LOG_BG = "#FFF9E3"         # Светло-желтый для логов

class ImageFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Image Analyzer")
        self.root.geometry("600x650")
        self.root.configure(bg=BG_COLOR)

        # Загрузка классификатора
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        self.create_gui()

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def open_github(self, event):
        webbrowser.open("https://github.com/KiviPups")

    def create_gui(self):
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg=BG_COLOR, padx=30, pady=30)
        main_frame.pack(expand=True, fill="both")

        # Заголовок
        tk.Label(main_frame, text="AI FILTER DASHBOARD", font=("Helvetica", 18, "bold"), 
                 bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=(0, 20))

        # Секция управления
        control_frame = tk.LabelFrame(main_frame, text="Управление", bg=BG_COLOR, fg=MUTED_COLOR, 
                                      font=("Helvetica", 10), padx=10, pady=10)
        control_frame.pack(fill="x", pady=(0, 20))

        self.btn_process = tk.Button(control_frame, text="Загрузить изображение", bg=ACCENT_COLOR, 
                                     fg="#3E2723", font=("Helvetica", 11, "bold"), relief="flat", 
                                     activebackground=BTN_HOVER, activeforeground="white", 
                                     command=self.process_image, cursor="hand2")
        self.btn_process.pack(fill="x", pady=5)

        # Терминал логов
        tk.Label(main_frame, text="Журнал событий:", bg=BG_COLOR, fg=TEXT_COLOR, font=("Helvetica", 10)).pack(anchor="w")
        
        self.log_text = tk.Text(main_frame, height=15, width=60, state='disabled', 
                                bg=LOG_BG, fg=TEXT_COLOR, font=("Consolas", 10), 
                                relief="flat", padx=15, pady=15)
        self.log_text.pack(fill="both", expand=True, pady=5)

        self.log("Система инициализирована. Ожидание пользователя...")

        # Футер
        footer = tk.Label(main_frame, text="github.com/KiviPups", bg=BG_COLOR, fg=MUTED_COLOR, 
                          font=("Helvetica", 9, "underline"), cursor="hand2")
        footer.pack(side=tk.BOTTOM, pady=(15, 0))
        footer.bind("<Button-1>", self.open_github)

    def process_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png")]
        )
        if not file_path:
            return

        img = cv2.imread(file_path)
        if img is None:
            self.log("[!] ОШИБКА: Файл не прочитан.")
            return

        self.log(f"\n--- Анализ: {os.path.basename(file_path)} ---")

        # 1. ФИЛЬТР РАЗМЕРА
        height, width, _ = img.shape
        self.log(f"[*] Разрешение: {width}x{height}px")
        
        if width < 150 or height < 150:
            self.log("[!] ВНИМАНИЕ: Слишком малый размер.")
            messagebox.showwarning("Размер", f"Изображение слишком маленькое ({width}x{height}px).")
        else:
            self.log("[+] Размер корректен.")

        # 2. ФИЛЬТР ЦВЕТА
        b, g, r = cv2.split(img)
        color_status = "Ч/Б" if np.array_equal(b, g) and np.array_equal(g, r) else "Цветное"
        self.log(f"[*] Тип цвета: {color_status}")

        # 3. ФИЛЬТР ШАБЛОНА
        self.log("[*] Поиск лиц...")
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            self.log(f"[+] Найдено лиц: {len(faces)}")
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 215, 255), 2) # Желтая рамка
            cv2.imshow("Результат анализа", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            self.log("[-] Лица не обнаружены.")
            messagebox.showinfo("Результат", "Ключевые контуры не найдены.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageFilterApp(root)
    root.mainloop()