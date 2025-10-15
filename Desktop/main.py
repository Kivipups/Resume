import sys
import os
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTextBrowser, QTextEdit, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QPixmap, QIcon, QPalette, QBrush
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

class CalculatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Калькулятор по весу ингредиентов")
        self.setFixedSize(600, 500)
        
        # Данные о продукции
        self.products = {
            "Молочный шоколад 'Sock-o-late'": {
                "total_weight": 85,
                "ingredients": {
                    "какао бобы": 25,
                    "сливки": 15,
                    "молоко сухое": 10,
                    "сахар": 20,
                    "какао масло": 10,
                    "растительное масло": 3,
                    "ванильный сахар": 2
                }
            },
            "Белый шоколад 'Sock-o-late Racist Edition'": {
                "total_weight": 80,
                "ingredients": {
                    "какао масло": 30,
                    "сухое молоко": 25,
                    "сахар": 20,
                    "ванильный сахар": 5
                }
            },
            "Батончик 'Dinker Town'": {
                "total_weight": 45,
                "ingredients": {
                    "воздушные злаки": 15,
                    "карамель": 10,
                    "арахис": 8,
                    "фирменный молочный шоколад": 12
                }
            },
            "Батончик 'Dinker Decoy'": {
                "total_weight": 40,
                "ingredients": {
                    "воздушный рис": 15,
                    "нуга": 12,
                    "фирменный молочный шоколад": 13
                }
            },
            "Шоколадное яйцо 'Dinker No Prize'": {
                "total_weight": 35,
                "ingredients": {
                    "фирменный молочный шоколад": 20,
                    "карамельная начинка": 15
                }
            },
            "Мини-батончик 'Dinker Credit Cards'": {
                "total_weight": 20,
                "ingredients": {
                    "вафля": 6,
                    "карамель": 4,
                    "фирменный белый шоколад": 10
                }
            },
            "Кекс 'Dinker Toxic'": {
                "total_weight": 80,
                "ingredients": {
                    "шоколадный бисквит": 50,
                    "кремовая начинка": 20,
                    "фирменный молочный шоколад (глазурь)": 10
                }
            },
            "Пончик 'Dinker Null'": {
                "total_weight": 60,
                "ingredients": {
                    "дрожжевое тесто": 40,
                    "сахарная глазурь": 15,
                    "кондитерская посыпка": 5
                }
            },
            "Батончик 'Dinker BuyElo'": {
                "total_weight": 50,
                "ingredients": {
                    "вафля": 15,
                    "кремовая начинка": 12,
                    "измельченный миндаль": 8,
                    "фирменный молочный шоколад": 15
                }
            }
        }
        
        self.current_product = None
        self.original_ratios = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Выбор продукта
        product_layout = QHBoxLayout()
        product_layout.addWidget(QLabel("Выберите продукт:"))
        self.product_combo = QComboBox()
        self.product_combo.addItems(self.products.keys())
        self.product_combo.currentTextChanged.connect(self.product_changed)
        product_layout.addWidget(self.product_combo)
        product_layout.addStretch()
        layout.addLayout(product_layout)
        
        # Информация о продукте
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #D2B48C; font-weight: bold; margin: 10px;")
        layout.addWidget(self.info_label)
        
        # Таблица ингредиентов
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Ингредиент", "Вес (г)", "Доля (%)"])
        self.table.cellChanged.connect(self.cell_changed)
        layout.addWidget(self.table)
        
        # Итоговая информация
        result_layout = QHBoxLayout()
        result_layout.addWidget(QLabel("Количество продуктов:"))
        self.quantity_label = QLabel("1")
        self.quantity_label.setStyleSheet("font-weight: bold; color: #D2B48C;")
        result_layout.addWidget(self.quantity_label)
        result_layout.addStretch()
        
        result_layout.addWidget(QLabel("Общий вес:"))
        self.total_weight_label = QLabel("0 г")
        self.total_weight_label.setStyleSheet("font-weight: bold; color: #D2B48C;")
        result_layout.addWidget(self.total_weight_label)
        layout.addLayout(result_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        self.reset_button = QPushButton("Сбросить")
        self.reset_button.clicked.connect(self.reset_values)
        button_layout.addWidget(self.reset_button)
        
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Загружаем первый продукт
        self.product_changed(self.product_combo.currentText())
    
    def product_changed(self, product_name):
        self.current_product = product_name
        product_data = self.products[product_name]
        
        # Блокируем сигналы чтобы избежать рекурсии
        self.table.cellChanged.disconnect()
        
        # Очищаем таблицу
        self.table.setRowCount(0)
        
        # Заполняем таблицу
        ingredients = product_data["ingredients"]
        total_weight = product_data["total_weight"]
        
        self.table.setRowCount(len(ingredients))
        
        self.original_ratios = {}
        row = 0
        for ingredient, weight in ingredients.items():
            ratio = weight / total_weight
            self.original_ratios[ingredient] = ratio
            
            # Ингредиент
            self.table.setItem(row, 0, QTableWidgetItem(ingredient))
            self.table.item(row, 0).setFlags(Qt.ItemFlag.ItemIsEnabled)
            
            # Вес
            weight_item = QTableWidgetItem(str(weight))
            self.table.setItem(row, 1, weight_item)
            
            # Доля
            percentage_item = QTableWidgetItem(f"{ratio*100:.1f}%")
            percentage_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 2, percentage_item)
            
            row += 1
        
        # Обновляем информацию
        self.update_product_info()
        
        # Подключаем сигнал обратно
        self.table.cellChanged.connect(self.cell_changed)
    
    def cell_changed(self, row, column):
        if column != 1:  # Нас интересуют только изменения в столбце веса
            return
            
        try:
            # Блокируем сигналы чтобы избежать рекурсии
            self.table.cellChanged.disconnect()
            
            new_weight = float(self.table.item(row, 1).text())
            ingredient = self.table.item(row, 0).text()
            
            # Получаем оригинальное соотношение для этого ингредиента
            original_ratio = self.original_ratios[ingredient]
            
            # Вычисляем новый общий вес на основе измененного ингредиента
            new_total_weight = new_weight / original_ratio
            
            # Обновляем все ингредиенты пропорционально
            for i in range(self.table.rowCount()):
                current_ingredient = self.table.item(i, 0).text()
                current_ratio = self.original_ratios[current_ingredient]
                new_ingredient_weight = current_ratio * new_total_weight
                
                self.table.setItem(i, 1, QTableWidgetItem(f"{new_ingredient_weight:.1f}"))
                self.table.setItem(i, 2, QTableWidgetItem(f"{current_ratio*100:.1f}%"))
            
            # Обновляем информацию о продукте
            self.update_product_info()
            
        except ValueError:
            # Если введено не число, восстанавливаем предыдущее значение
            pass
        finally:
            # Подключаем сигнал обратно
            self.table.cellChanged.connect(self.cell_changed)
    
    def update_product_info(self):
        if not self.current_product:
            return
            
        product_data = self.products[self.current_product]
        original_total_weight = product_data["total_weight"]
        
        # Вычисляем текущий общий вес и количество продуктов
        current_total_weight = 0
        for i in range(self.table.rowCount()):
            try:
                weight = float(self.table.item(i, 1).text())
                current_total_weight += weight
            except ValueError:
                pass
        
        quantity = current_total_weight / original_total_weight
        
        self.quantity_label.setText(f"{quantity:.2f}")
        self.total_weight_label.setText(f"{current_total_weight:.1f} г")
        
        self.info_label.setText(
            f"Продукт: {self.current_product} | "
            f"Оригинальный вес: {original_total_weight} г | "
            f"Текущий вес: {current_total_weight:.1f} г"
        )
    
    def reset_values(self):
        # Сбрасываем значения к оригинальным
        self.product_changed(self.current_product)

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('mainwindow.ui', self)
        
        # Установка затемненного фонового изображения
        self.set_dark_background()
        
        # ОТКРЫТИЕ ВО ВЕСЬ ЭКРАН
        self.showMaximized()
        
        # Загружаем логотип
        self.load_logo()
        
        # Подключаем обработчики кнопок
        self.aboutCompanyButton.clicked.connect(self.show_about_company)
        self.calculatorButton.clicked.connect(self.show_calculator)
        
        # Настройка обработки ссылок для текстовых виджетов
        self.setup_link_handling()
    
    def setup_link_handling(self):
        """Настройка обработки ссылок для всех текстовых виджетов"""
        # Если у вас есть QTextBrowser с HTML контентом
        text_widgets = [
            getattr(self, attr) for attr in dir(self) 
            if isinstance(getattr(self, attr, None), (QTextBrowser, QTextEdit))
        ]
        
        for widget in text_widgets:
            widget.setOpenExternalLinks(True)
    
    def handle_link_click(self, url):
        """Обработчик кликов по ссылкам"""
        QDesktopServices.openUrl(url)
    
    def set_dark_background(self):
        """Установка затемненного фонового изображения"""
        try:
            background_path = "background.jpg"  # Можно изменить на нужное изображение
            if os.path.exists(background_path):
                pixmap = QPixmap(background_path)
                if not pixmap.isNull():
                    # Масштабируем изображение под размер окна
                    scaled_pixmap = pixmap.scaled(
                        self.size(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Создаем затемненную версию изображения
                    dark_pixmap = self.create_darkened_pixmap(scaled_pixmap)
                    
                    # Устанавливаем как фон
                    palette = QPalette()
                    palette.setBrush(QPalette.ColorRole.Window, QBrush(dark_pixmap))
                    self.setPalette(palette)
                    print("Фоновое изображение установлено")
            else:
                # Если изображение не найдено, используем темный градиент
                self.setStyleSheet("""
                    QMainWindow {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                            stop:0 #2b1b0e, stop:1 #1a1008);
                    }
                """)
                print("Фоновое изображение не найдено, использован градиент")
        except Exception as e:
            print(f"Ошибка установки фона: {e}")
            # Резервный вариант - темный градиент
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2b1b0e, stop:1 #1a1008);
                }
            """)
    
    def create_darkened_pixmap(self, pixmap):
        """Создает затемненную версию изображения"""
        try:
            # Создаем копию pixmap
            dark_pixmap = QPixmap(pixmap.size())
            dark_pixmap.fill(Qt.GlobalColor.transparent)
            
            # Рисуем затемненное изображение
            from PyQt6.QtGui import QPainter
            painter = QPainter(dark_pixmap)
            painter.setOpacity(0.6)  # Уровень затемнения (0.6 = 40% затемнения)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            return dark_pixmap
        except Exception as e:
            print(f"Ошибка создания затемненного изображения: {e}")
            return pixmap
    
    def resizeEvent(self, event):
        """Обработчик изменения размера окна для обновления фона"""
        super().resizeEvent(event)
        self.set_dark_background()
    
    def load_logo(self):
        try:
            logo_path = "logo2.png"
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Проверяем размер изображения
                    if pixmap.width() <= 150 and pixmap.height() <= 150:
                        # Если изображение маленькое, используем без масштабирования
                        self.logoLabel.setPixmap(pixmap)
                    else:
                        # Если большое, масштабируем с качеством
                        scaled_pixmap = pixmap.scaled(
                            150, 150,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.logoLabel.setPixmap(scaled_pixmap)
                    
                    self.logoLabel.setText("")
                    self.logoLabel.setScaledContents(True)
                    print("Логотип загружен оптимальным способом")
        except Exception as e:
            print(f"Ошибка: {e}")
            self.logoLabel.setText("ЛОГОТИП")
    
    def show_about_company(self):
        about_text = """
<h2>О компании 'Dinker'</h2>
<p><b>Основана:</b> 2025 год</p>
<p><b>Специализация:</b> Производство высококачественных кондитерских изделий</p>
<br>
<h3>Основатели компании:</h3>
<b>Сучилин Михаил Максимович</b> - Решала команды. Несёт ответственность за предприятие и нашу горе-команду.<br><br>
<b>Тишин Денис Анатольевич</b> - Главный разраб и доставала Дипсика, создавший это окно и приложение в целом.<br><br>
<b>Пластунов Даниил Викторович</b> - Мастер кривых линий, создавший 2D план-схему предприятия.<br><br>
<b>Маркин Кирилл Евгеньевич</b> - Автор того самого значка, создавший логотип нашей недокомпании.<br><br>
<b>Умрихина Кристина Александровна</b> - Дизайнер-садист, придумавшая дизайн нашей кноподавки.<br><br>
<b>Пачас Иван Константинович</b> - Конструктор (не)съедобной еды, придумавший шоколадки и их состав.<br><br>
<b>Беспалов Андрей АндрееВИЧ</b> - Верховный сочинитель. Создатель самого цитируемого текста в компании.<br><br>
<b>Репко Максим Юрьевич</b> - Крёстный отец нашей компании. Главный одобрятель нашего бардака.<br>
</ul>
<br>
<p>Мы гордимся нашими традициями качества и инновационными подходами к производству.</p>
"""
        QMessageBox.about(self, "О компании", about_text)
    
    def show_calculator(self):
        calculator = CalculatorDialog(self)
        calculator.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Используйте файл .ico вместо .png
    try:
        app.setWindowIcon(QIcon('icon.ico'))
        print("Иконка приложения установлена")
    except Exception as e:
        print(f"Не удалось установить иконку: {e}")
    
    window = MyWindow()
    window.show()
    sys.exit(app.exec())