import tkinter as tk
from tkinter import messagebox, ttk
import os
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# --- Пути ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "text_classifier.pkl")
VECTORIZER_FILE = os.path.join(BASE_DIR, "vectorizer.pkl")
DATA_FILE = os.path.join(BASE_DIR, "data.pkl") # Файл для хранения истории обучения

# --- Палитра: Pastel Yellow ---
COLORS = {
    "bg": "#fdfcf0",
    "card": "#fdf5d6",
    "text": "#6b5d43",
    "accent": "#f5c667",
    "muted": "#a39977",
    "white": "#ffffff"
}

class TextAiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pastel Sentiment AI (Manual Feedback)")
        self.root.geometry("500x750")
        self.root.configure(bg=COLORS["bg"])
        
        # Загрузка или инициализация данных
        self.load_data()
        
        self.init_app_model()
        self.setup_styles()
        self.create_gui()

    def load_data(self):
        """Загрузка истории обучения из файла"""
        if os.path.exists(DATA_FILE):
            self.texts, self.labels = joblib.load(DATA_FILE)
        else:
            # Базовые данные, если файла нет
            self.texts = ["Отличный сайт!", "Python - язык программирования.", "Ужасная программа.", "Нормальный проект."]
            self.labels = [3, 2, 0, 1]

    def init_app_model(self):
        """Инициализация модели на основе имеющихся данных"""
        self.vectorizer = CountVectorizer()
        X_vectors = self.vectorizer.fit_transform(self.texts)
        self.model = MultinomialNB()
        self.model.fit(X_vectors, self.labels)

    def train_and_save(self):
        """Переобучение и сохранение всех файлов"""
        # 1. Обучаем
        self.vectorizer = CountVectorizer()
        X_vectors = self.vectorizer.fit_transform(self.texts)
        self.model = MultinomialNB()
        self.model.fit(X_vectors, self.labels)
        
        # 2. Сохраняем модель и историю данных
        joblib.dump(self.model, MODEL_FILE)
        joblib.dump(self.vectorizer, VECTORIZER_FILE)
        joblib.dump((self.texts, self.labels), DATA_FILE)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=10, background=COLORS["accent"], troughcolor=COLORS["white"])

    def create_gui(self):
        # ... (GUI) ...
        header = tk.Frame(self.root, bg=COLORS["bg"])
        header.pack(fill="x", padx=20, pady=20)
        tk.Label(header, text="SENTIMENT AI", font=("Segoe UI", 16, "bold"), bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        
        card_input = tk.Frame(self.root, bg=COLORS["card"], padx=20, pady=20)
        card_input.pack(fill="x", padx=20, pady=5)
        
        self.input_text = tk.Text(card_input, height=3, bg=COLORS["white"], fg=COLORS["text"], font=("Segoe UI", 11), relief="flat", padx=10, pady=10)
        self.input_text.pack(fill="x")
        
        # Кнопка теперь ТОЛЬКО анализирует
        tk.Button(card_input, text="Анализировать", bg=COLORS["accent"], fg=COLORS["text"], 
                  relief="flat", font=("Segoe UI", 10, "bold"), command=self.analyze_text).pack(fill="x", pady=(10, 0))

        card_result = tk.Frame(self.root, bg=COLORS["card"], padx=20, pady=20)
        card_result.pack(fill="x", padx=20, pady=10)
        
        self.lbl_verdict = tk.Label(card_result, text="Введите текст...", font=("Segoe UI", 14, "bold"), bg=COLORS["card"], fg=COLORS["text"])
        self.lbl_verdict.pack(anchor="w")

        self.bars = {}
        for code, name in [(3, "Позитив"), (2, "Нейтрал"), (1, "Смеш."), (0, "Негатив")]:
            row = tk.Frame(card_result, bg=COLORS["card"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name, bg=COLORS["card"], fg=COLORS["text"], width=8).pack(side=tk.LEFT)
            bar = ttk.Progressbar(row, length=150, mode='determinate', style="TProgressbar")
            bar.pack(side=tk.LEFT, padx=10, expand=True, fill="x")
            self.bars[code] = bar

        # Блок обратной связи (обучение только здесь)
        tk.Label(self.root, text="Обучить верному классу:", bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=(10, 5))
        btn_frame = tk.Frame(self.root, bg=COLORS["bg"])
        btn_frame.pack()
        for label, name in zip([3, 2, 1, 0], ["Позитив", "Нейтрал", "Смеш.", "Негатив"]):
            tk.Button(btn_frame, text=name, bg=COLORS["white"], fg=COLORS["text"], relief="flat", 
                      command=lambda l=label: self.add_to_training(l)).pack(side=tk.LEFT, padx=5)

    def analyze_text(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text: return
        X_test = self.vectorizer.transform([text])
        prediction = self.model.predict(X_test)[0]
        probabilities = self.model.predict_proba(X_test)[0]
        
        classes = {3: "ПОЗИТИВ", 2: "НЕЙТРАЛЬНО", 1: "СМЕШАННО", 0: "НЕГАТИВ"}
        self.lbl_verdict.config(text=classes[prediction])
        for code in self.bars.keys():
            self.bars[code]['value'] = probabilities[code] * 100

    def add_to_training(self, correct_label):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text: return
        
        # Только теперь мы добавляем данные и обучаем
        self.texts.append(text)
        self.labels.append(correct_label)
        self.train_and_save()
        
        messagebox.showinfo("Обучение", "Данные приняты в базу и модель обновлена!")

if __name__ == "__main__":
    root = tk.Tk()
    app = TextAiApp(root)
    root.mainloop()