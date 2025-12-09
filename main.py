import sys
import os
import json
import random

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QPushButton,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt

from PIL import Image


GRADE_DISPLAY = {
    "4": "IV",
    "5": "V",
    "6": "VI",
    "7": "VII",
    "8": "VIII",
    "9": "IX",
    "10": "X",
    "11": "XI",
    "12": "XII"
}


class QuizApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Quiz app v1.0")
        self.showFullScreen()

        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.questions_path = os.path.join(self.base_path, "questions")
        self.images_path = os.path.join(self.base_path, "images")

        # състояние
        self.grade = None
        self.category = None
        self.questions = []          # избраните въпроси за теста
        self.current_question = None
        self.current_index = -1      # индекс на текущия въпрос
        self.correct_answers = 0
        self.total_questions = 0

        # лог на отговорите за преглед след края
        self.answers_log = []        # тук пазим всеки въпрос + отговорите
        self.review_index = 0        # текущ индекс в режим преглед

        # флаг за текстов въпрос – дали вече е проверен (за текущия престой на екрана)
        self._text_already_checked = False

        # основен widget и layout (в scroll area)
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(40, 30, 40, 30)
        self.main_layout.setSpacing(30)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.main_widget)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # прозрачен фон, за да се вижда background-а
        self.main_widget.setStyleSheet("background-color: transparent;")
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.viewport().setStyleSheet("background: transparent;")

        self.setCentralWidget(self.scroll_area)

        # динамични widgets
        self.answer_input = None
        self.feedback_label = None
        self.next_button = None
        self.check_button = None
        self.option_buttons = []

        # background
        self.apply_background()

        # стил на рамки и бутони
        self.panel_color = "rgba(69, 90, 100, 200)"   # рамка
        self.header_color = "rgba(69, 90, 100, 200)"  # header

        self.button_style = """
            QPushButton {
                background-color: rgba(241, 245, 249, 190);
                color: #1f2933;
                border-radius: 18px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(222, 231, 241, 210);
            }
            /* да не посивява текста, когато е disabled */
            QPushButton:disabled {
                background-color: rgba(241, 245, 249, 190);
                color: #1f2933;
            }
        """

        self.primary_button_style = """
            QPushButton {
                background-color: rgba(52, 152, 219, 200);
                color: white;
                border-radius: 18px;
                padding: 10px 22px;
            }
            QPushButton:hover {
                background-color: rgba(41, 128, 185, 210);
            }
            QPushButton:disabled {
                background-color: rgba(52, 152, 219, 120);
                color: rgba(255, 255, 255, 220);
            }
        """

        self.danger_button_style = """
            QPushButton {
                background-color: rgba(231, 76, 60, 200);
                color: white;
                border-radius: 18px;
                padding: 10px 22px;
            }
            QPushButton:hover {
                background-color: rgba(192, 57, 43, 210);
            }
        """

        self.success_button_style = """
            QPushButton {
                background-color: rgba(39, 174, 96, 200);
                color: white;
                border-radius: 18px;
                padding: 10px 22px;
            }
            QPushButton:hover {
                background-color: rgba(30, 132, 73, 210);
            }
        """
        
        self.selected_button_style = """
            QPushButton {
                background-color: rgba(59, 130, 246, 230);
                color: white;
                border-radius: 18px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(37, 99, 235, 240);
            }
        """

        self.show_grade_screen()

    # -------------------------------------------------------
    #  background
    # -------------------------------------------------------
    def apply_background(self):
        bg_path = os.path.join(self.images_path, "background.jpg")
        if not os.path.exists(bg_path):
            print("background.jpg не е намерен!")
            self.setStyleSheet("QMainWindow { background-color: #3a4046; }")
            return

        bg_path_css = bg_path.replace("\\", "/")
        print("BG PATH CSS:", bg_path_css)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url("{bg_path_css}");
                background-position: center;
                background-repeat: no-repeat;
                background-color: #3a4046;
            }}
        """)

    # -------------------------------------------------------
    #  UI
    # -------------------------------------------------------
    def clear_central(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.answer_input = None
        self.feedback_label = None
        self.next_button = None
        self.check_button = None
        self.option_buttons = []
        self._text_already_checked = False

    def create_header(self, text: str):
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.header_color};
                border-radius: 26px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 10, 30, 10)

        label = QLabel(text)
        label.setStyleSheet("color: white; background-color: transparent;")
        label.setFont(QFont("Helvetica", 26, QFont.Bold))

        header_layout.addStretch()
        header_layout.addWidget(label)
        header_layout.addStretch()

        self.main_layout.addWidget(header, 0, Qt.AlignHCenter | Qt.AlignTop)

    def create_panel(self, fixed_width: int = None, fixed_height: int = None) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.panel_color};
                border-radius: 26px;
            }}
        """)
        if fixed_width is not None:
            panel.setFixedWidth(fixed_width)
        if fixed_height is not None:
            panel.setFixedHeight(fixed_height)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        return panel

    def create_button_widget(
        self,
        text: str,
        on_click,
        *,
        primary=False,
        danger=False,
        success=False,
        font_size=16,
    ) -> QPushButton:
        btn = QPushButton(text)
        if danger:
            btn.setStyleSheet(self.danger_button_style)
        elif primary:
            btn.setStyleSheet(self.primary_button_style)
        elif success:
            btn.setStyleSheet(self.success_button_style)
        else:
            btn.setStyleSheet(self.button_style)

        font = QFont("Helvetica", font_size, QFont.Bold)
        btn.setFont(font)

        btn.clicked.connect(lambda checked=False, fn=on_click: fn())
        return btn

    # -------------------------------------------------------
    #  Избор на клас
    # -------------------------------------------------------
    def show_grade_screen(self):
        self.clear_central()

        self.create_header("Моля изберете клас")

        panel = self.create_panel(fixed_width=600, fixed_height=180)
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(10)
        panel.layout().addLayout(grid)

        grades = ["4", "7", "10", "12"]
        r, c = 0, 0
        for grade in grades:
            text = GRADE_DISPLAY.get(grade, f"{grade} клас")

            def handler(g=grade):
                self.select_grade(g)

            btn = self.create_button_widget(text, handler, font_size=16)
            btn.setMinimumHeight(40)
            grid.addWidget(btn, r, c)
            c += 1
            if c > 1:  # 2 бутона на ред
                c = 0
                r += 1

        self.main_layout.addWidget(panel, 1, Qt.AlignHCenter | Qt.AlignVCenter)

        close_btn = self.create_button_widget(
            "ЗАТВОРИ", self.close, danger=True, font_size=16
        )
        self.main_layout.addWidget(close_btn, 0, Qt.AlignHCenter | Qt.AlignBottom)

    def select_grade(self, grade: str):
        self.grade = grade
        self.show_category_screen()

    # -------------------------------------------------------
    #  Избор на предмет
    # -------------------------------------------------------
    def show_category_screen(self):
        self.clear_central()

        self.create_header("Моля изберете предмет")

        panel = self.create_panel(fixed_width=600, fixed_height=180)
        layout = panel.layout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(10)
        layout.addLayout(grid)

        btn_bel = self.create_button_widget(
            "БЕЛ",
            lambda: self.load_questions("bel"),
            font_size=16,
        )
        btn_math = self.create_button_widget(
            "МАТЕМАТИКА",
            lambda: self.load_questions("math"),
            font_size=16,
        )

        grid.addWidget(btn_bel, 0, 0)
        grid.addWidget(btn_math, 0, 1)

        self.main_layout.addWidget(panel, 1, Qt.AlignHCenter | Qt.AlignVCenter)

        btn_back = self.create_button_widget(
            "НАЗАД",
            self.show_grade_screen,
            danger=True,
            font_size=14,
        )
        self.main_layout.addWidget(btn_back, 0, Qt.AlignCenter)

    # -------------------------------------------------------
    #  Зареждане на въпроси
    # -------------------------------------------------------
    def load_questions(self, category: str):
        self.category = category
        filename = f"{self.grade}_{self.category}.json"
        filepath = os.path.join(self.questions_path, filename)

        if not os.path.exists(filepath):
            QMessageBox.critical(self, "Грешка", f"Файлът {filename} липсва!")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                all_questions = json.load(f)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Грешка", f"{filename} е с грешен JSON!")
            return

        if not all_questions:
            QMessageBox.critical(self, "Грешка", "Файлът е празен!")
            return

        # нов тест -> чистим старите отговори
        self.answers_log = []
        self.current_question = None
        self.current_index = -1

        # взимаме до 10 въпроса
        self.questions = random.sample(all_questions, min(10, len(all_questions)))
        random.shuffle(self.questions)
        self.correct_answers = 0
        self.total_questions = len(self.questions)

        self.next_question()
        
    # -----------------------------------------------------
    #  функция за бутон ПРЕДАЙ
    # -----------------------------------------------------
    
    def update_next_button_label(self):
        if self.next_button:
            if self.current_index == len(self.questions) - 1:
                self.next_button.setText("ПРЕДАЙ")
            else:
                self.next_button.setText("НАПРЕД")


    # -------------------------------------------------------
    #  Показване на текущия въпрос
    # -------------------------------------------------------
    def show_current_question(self):
        self.clear_central()

        if self.current_index < 0 or self.current_index >= len(self.questions):
            self.show_final_screen()
            return

        self.current_question = self.questions[self.current_index]

        self.create_header("Въпрос")

        text = self.current_question["question"]
        has_image = bool(self.current_question.get("image"))

        question_panel = self.create_panel(fixed_width=1000)
        q_layout = question_panel.layout()

        # scroll за въпроса + картинката
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        scroll.viewport().setStyleSheet("background-color: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background-color: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(10)

        q_label = QLabel(text)
        q_label.setStyleSheet("color: white; background-color: transparent;")
        q_label.setWordWrap(True)
        q_label.setAlignment(Qt.AlignCenter)
        q_label.setFont(QFont("Helvetica", 20, QFont.Bold))
        inner_layout.addWidget(q_label)

        if has_image:
            img_label = self.create_image_label(self.current_question["image"])
            if img_label is not None:
                inner_layout.addWidget(img_label, 0, Qt.AlignCenter)

        scroll.setWidget(inner)
        scroll.setFixedHeight(150 if not has_image else 245) # когато имаме картинка рамката се разширява, за да поберем 800х200

        q_layout.addWidget(scroll)
        self.main_layout.addWidget(question_panel, 0, Qt.AlignHCenter | Qt.AlignTop)

        if self.current_question["type"] == "choice":
            self.show_choice_question()
        else:
            self.show_text_question()

        self.update_next_button_label()

    # -------------------------------------------------------
    #  Навигация: Напред / Назад
    # -------------------------------------------------------
    def next_question(self):
        next_index = self.current_index + 1
        if next_index >= len(self.questions):
            self.show_final_screen()
            return
        self.current_index = next_index
        self.show_current_question()

    def prev_question(self):
        prev_index = self.current_index - 1
        if prev_index < 0:
            return
        self.current_index = prev_index
        self.show_current_question()

    # -------------------------------------------------------
    #  Картинка към въпрос
    # -------------------------------------------------------
    def create_image_label(self, img_name: str):
        img_path = os.path.join(self.images_path, img_name)
        if not os.path.exists(img_path):
            QMessageBox.critical(self, "Грешка", f"Картинката '{img_name}' липсва!")
            return None

        img = Image.open(img_path)
        max_w = 800
        max_h = 200
        w, h = img.size
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        tmp_path = os.path.join(self.images_path, "_temp_render.png")
        img.save(tmp_path)
        pix = QPixmap(tmp_path)
        try:
            os.remove(tmp_path)
        except OSError:
            pass

        lbl = QLabel()
        lbl.setPixmap(pix)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("background-color: transparent;")
        return lbl
    
    # -------------------------------------------------------
    #  Въпрос с 4 отговора
    # -------------------------------------------------------
    def show_choice_question(self):
        self.option_buttons = []

        options = list(self.current_question["options"])
        random.shuffle(options)

        answers_panel = self.create_panel(fixed_width=950, fixed_height=150)
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(10)
        answers_panel.layout().addLayout(grid)

        idx = 0
        for r in range(2):
            for c in range(2):
                if idx >= len(options):
                    break
                opt_text = options[idx]

                def handler(o=opt_text):
                    self.mark_answer(o)

                btn = self.create_button_widget(opt_text, handler, font_size=16)
                btn.setMinimumHeight(40)
                grid.addWidget(btn, r, c)
                self.option_buttons.append(btn)
                idx += 1

        self.main_layout.addWidget(answers_panel, 0, Qt.AlignHCenter | Qt.AlignVCenter)

        # ред с бутони Назад / Напред
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        back_btn = self.create_button_widget(
            "НАЗАД", self.prev_question, danger=True, font_size=16
        )
        self.next_button = self.create_button_widget(
            "НАПРЕД", self.next_question, primary=True, font_size=16
        )
        self.next_button.setEnabled(False)
        self.update_next_button_label()

        btn_row.addWidget(back_btn)
        btn_row.addWidget(self.next_button)

        btn_container = QWidget()
        btn_container.setLayout(btn_row)
        self.main_layout.addWidget(btn_container, 0, Qt.AlignHCenter | Qt.AlignBottom)

        # ако вече имаме запис за този въпрос – възстановяваме избора
        for entry in self.answers_log:
            if entry["type"] == "choice" and entry["question"] == self.current_question["question"]:
                saved_answer = entry["user_answer"]
                for btn in self.option_buttons:
                    if btn.text() == saved_answer:
                        btn.setStyleSheet(self.selected_button_style)
                    else:
                        btn.setStyleSheet(self.button_style)
                self.next_button.setEnabled(True)
                break

    def mark_answer(self, selected: str):
        correct = self.current_question["answer"]

        # търсим стар запис за този въпрос
        existing_index = None
        for i, entry in enumerate(self.answers_log):
            if entry["type"] == "choice" and entry["question"] == self.current_question["question"]:
                existing_index = i
                break

        # ако има стар запис – коригираме точките
        if existing_index is not None:
            prev_entry = self.answers_log.pop(existing_index)
            if prev_entry.get("was_counted"):
                self.correct_answers -= 1

        # визуално: само избраният отговор е син, останалите е по default
        for btn in self.option_buttons:
            if btn.text() == selected:
                btn.setStyleSheet(self.selected_button_style)
            else:
                btn.setStyleSheet(self.button_style)

        is_correct = (selected.strip().lower() == correct.strip().lower())

        entry = {
            "type": "choice",
            "question": self.current_question["question"],
            "correct": correct,
            "user_answer": selected,
            "image": self.current_question.get("image"),
            "was_counted": False
        }

        if is_correct:
            self.correct_answers += 1
            entry["was_counted"] = True

        self.answers_log.append(entry)

        if self.next_button:
            self.next_button.setEnabled(True)

    # -------------------------------------------------------
    #  Въпрос със свободен текст
    # -------------------------------------------------------
    def show_text_question(self):
        panel = self.create_panel(fixed_width=950, fixed_height=150)
        layout = panel.layout()

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Моля въведете верният отговор")
        self.answer_input.setFont(QFont("Helvetica", 18))
        self.answer_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(241, 245, 249, 190);
                border-radius: 12px;
                padding: 6px 10px;
                border: 1px solid rgba(255, 255, 255, 80);
                color: black;
            }
        """)
        layout.addWidget(self.answer_input)

        self.main_layout.addWidget(panel, 0, Qt.AlignHCenter | Qt.AlignVCenter)

        # feedback рамка – не я ползваме за верния отговор, но е оставена за бъдещи съобщения
        self.feedback_label = QLabel()
        self.feedback_label.setVisible(False)
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setFont(QFont("Helvetica", 16, QFont.Bold))
        self.feedback_label.setFixedHeight(70)
        self.feedback_label.setStyleSheet("background-color: transparent;")
        self.main_layout.addWidget(self.feedback_label, 0, Qt.AlignHCenter)

        # ред с бутони НАЗАД / НАПРЕД
        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        back_btn = self.create_button_widget(
            "НАЗАД", self.prev_question, danger=True, font_size=16
        )
        self.next_button = self.create_button_widget(
            "НАПРЕД", self.submit_text_and_next, primary=True, font_size=16
        )
        
        self.update_next_button_label()

        btn_row.addWidget(back_btn)
        btn_row.addWidget(self.next_button)

        btn_container = QWidget()
        btn_container.setLayout(btn_row)
        self.main_layout.addWidget(btn_container, 0, Qt.AlignHCenter | Qt.AlignBottom)

        self._text_already_checked = False

        # ако вече има отговор за този въпрос – попълваме полето
        for entry in self.answers_log:
            if entry["type"] == "text" and entry["question"] == self.current_question["question"]:
                self.answer_input.setText(entry["user_answer"])
                break

    def submit_text_and_next(self):
        if not self._text_already_checked:
            self.check_text_answer()
            self._text_already_checked = True
        self.next_question()

    def check_text_answer(self):
        if not self.answer_input:
            return

        user_raw = self.answer_input.text().strip()
        user = user_raw.lower()
        placeholder = "моля въведете верният отговор"
        if user == placeholder:
            user = ""

        correct_raw = self.current_question["answer"].strip()
        correct = correct_raw.lower()

        self.answer_input.setEnabled(False)

        if getattr(self, "check_button", None):
            self.check_button.setEnabled(False)

        is_correct = (user == correct)

        # търсим стар запис за този въпрос
        existing_index = None
        for i, entry in enumerate(self.answers_log):
            if entry["type"] == "text" and entry["question"] == self.current_question["question"]:
                existing_index = i
                break

        # ако има стар запис – коригираме точките
        if existing_index is not None:
            prev_entry = self.answers_log.pop(existing_index)
            prev_correct = prev_entry["correct"].strip().lower()
            prev_user = prev_entry["user_answer"].strip().lower()
            if prev_user == prev_correct:
                self.correct_answers -= 1

        if is_correct:
            self.correct_answers += 1

        self.answers_log.append({
            "type": "text",
            "question": self.current_question["question"],
            "correct": correct_raw,
            "user_answer": user_raw,
            "image": self.current_question.get("image")
        })

    # -------------------------------------------------------
    #  Финален екран
    # -------------------------------------------------------
    def show_final_screen(self):
        self.clear_central()

        self.create_header("Резултат")

        panel = self.create_panel(fixed_width=600, fixed_height=180)
        layout = panel.layout()

        label = QLabel(f"Верни отговори: {self.correct_answers} / {self.total_questions}")
        label.setStyleSheet("color: white; background-color: transparent;")
        label.setFont(QFont("Helvetica", 26, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        if self.total_questions > 0:
            percent = round((self.correct_answers / self.total_questions) * 100)
        else:
            percent = 0

        percent_label = QLabel(f"Успеваемост: {percent}%")
        percent_label.setStyleSheet("color: white; background-color: transparent;")
        percent_label.setFont(QFont("Helvetica", 22, QFont.Bold))
        percent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(percent_label)

        self.main_layout.addWidget(panel, 0, Qt.AlignHCenter | Qt.AlignTop)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(30)

        start_btn = self.create_button_widget(
            "НАЧАЛО", self.show_grade_screen, success=True, font_size=18
        )
        review_btn = self.create_button_widget(
            "ПРЕГЛЕД",
            self.start_review_mode,
            primary=True,
            font_size=18,
        )
        close_btn = self.create_button_widget(
            "ЗАТВОРИ", self.close, danger=True, font_size=18
        )

        btn_row.addWidget(start_btn)
        btn_row.addWidget(review_btn)
        btn_row.addWidget(close_btn)

        container = QWidget()
        container.setLayout(btn_row)
        self.main_layout.addWidget(container, 0, Qt.AlignHCenter | Qt.AlignTop)

    # -------------------------------------------------------
    #  Режим: преглед на въпросите
    # -------------------------------------------------------
    def start_review_mode(self):
        if not self.answers_log:
            QMessageBox.information(self, "Преглед", "Няма запазени въпроси за преглед.")
            return

        self.review_index = 0
        self.show_review_question()

    def show_review_question(self):
        self.clear_central()

        total = len(self.answers_log)
        item = self.answers_log[self.review_index]

        self.create_header(f"Преглед на въпросите ({self.review_index + 1} / {total})")

        panel = self.create_panel(fixed_width=1000)
        layout = panel.layout()

        # scroll зона за въпроса + картинката
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        scroll.viewport().setStyleSheet("background-color: transparent;")

        inner = QWidget()
        inner.setStyleSheet("background-color: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(10)

        q_label = QLabel(item["question"])
        q_label.setStyleSheet("color: white; background-color: transparent;")
        q_label.setWordWrap(True)
        q_label.setAlignment(Qt.AlignCenter)
        q_label.setFont(QFont("Helvetica", 20, QFont.Bold))
        inner_layout.addWidget(q_label)

        if item.get("image"):
            img_label = self.create_image_label(item["image"])
            if img_label:
                inner_layout.addWidget(img_label, 0, Qt.AlignCenter)

        scroll.setWidget(inner)
        scroll.setFixedHeight(220)

        layout.addWidget(scroll)

        # вашият отговор
        user_answer = item.get("user_answer", "").strip()
        correct = item.get("correct", "").strip()

        if item["type"] == "choice":
            is_correct = item.get("was_counted", False)
        else:
            is_correct = (user_answer.lower() == correct.lower())

        if is_correct:
            bg = "rgba(39, 174, 96, 200)"
        else:
            bg = "rgba(192, 57, 43, 200)"

        user_label = QLabel(f"Вашият отговор: {user_answer or '—'}")
        user_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: white;
                border-radius: 14px;
                padding: 8px 12px;
            }}
        """)
        user_label.setAlignment(Qt.AlignCenter)
        user_label.setWordWrap(True)
        layout.addWidget(user_label)

        correct_label = QLabel(f"Верен отговор: {correct}")
        correct_label.setStyleSheet("color: white; background-color: transparent;")
        correct_label.setFont(QFont("Helvetica", 18, QFont.Bold))
        correct_label.setAlignment(Qt.AlignCenter)
        correct_label.setWordWrap(True)
        layout.addWidget(correct_label)

        self.main_layout.addWidget(panel, 0, Qt.AlignHCenter | Qt.AlignTop)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)

        prev_btn = self.create_button_widget(
            "Предишен",
            self.prev_review_question,
            primary=True,
            font_size=16,
        )
        next_btn = self.create_button_widget(
            "Следващ",
            self.next_review_question,
            primary=True,
            font_size=16,
        )
        back_btn = self.create_button_widget(
            "Продължи",
            self.show_final_screen,
            success=True,
            font_size=16,
        )

        if self.review_index == 0:
            prev_btn.setEnabled(False)
        if self.review_index >= total - 1:
            next_btn.setEnabled(False)

        btn_row.addWidget(prev_btn)
        btn_row.addWidget(next_btn)
        btn_row.addWidget(back_btn)

        container = QWidget()
        container.setLayout(btn_row)
        self.main_layout.addWidget(container, 0, Qt.AlignHCenter | Qt.AlignVCenter)

    def prev_review_question(self):
        if self.review_index > 0:
            self.review_index -= 1
            self.show_review_question()

    def next_review_question(self):
        if self.review_index < len(self.answers_log) - 1:
            self.review_index += 1
            self.show_review_question()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuizApp()
    window.show()
    sys.exit(app.exec())