import sys
import os
import json

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QPlainTextEdit,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


GRADE_DISPLAY = {
    "4": "IV клас",
    "7": "VII клас",
    "10": "X клас",
    "12": "XII клас",
}

CATEGORIES = {
    "bel": "БЕЛ",
    "math": "МАТЕМАТИКА",
}


class LoginDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход")
        self.resize(320, 160)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        layout.addLayout(form)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Потребител")
        form.addRow("Потребител:", self.user_edit)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Парола")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Парола:", self.pass_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        buttons.accepted.connect(self.check_login)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def check_login(self):
        username = self.user_edit.text().strip()
        password = self.pass_edit.text().strip()

        if username == "root" and password == "toor":
            self.accept()
        else:
            QMessageBox.warning(self, "Грешка", "Невалидни потребител или парола.")


class QuestionDialog(QDialog):
    """
    Диалог за добавяне/редакция на един въпрос.
    Поддържа:
      - type: choice / text
      - question
      - answer
      - options (ако е choice)
      - image (по желание)
    """

    def __init__(self, parent=None, question_data=None):
        super().__init__(parent)
        self.setWindowTitle("Въпрос")

        self.resize(600, 600)

        self.question_data = question_data or {}

        layout = QVBoxLayout(self)

        form = QFormLayout()
        layout.addLayout(form)

        # Тип на въпроса
        self.type_combo = QComboBox()
        self.type_combo.addItem("Избираем (4 отговора)", "choice")
        self.type_combo.addItem("Свободен отговор", "text")
        form.addRow("Тип:", self.type_combo)

        # Текст на въпроса 
        self.question_edit = QPlainTextEdit()
        self.question_edit.setPlaceholderText("Въведете текста на въпроса...")
        self.question_edit.setMinimumHeight(120)
        self.question_edit.setFont(QFont("Helvetica", 12))
        form.addRow("Въпрос:", self.question_edit)

        # Верен отговор
        self.answer_edit = QLineEdit()
        self.answer_edit.setPlaceholderText("Верен отговор...")
        self.answer_edit.setMinimumHeight(20)
        self.answer_edit.setFont(QFont("Helvetica", 12))
        form.addRow("Верен отговор:", self.answer_edit)

        # Опции (ако е choice) 
        self.option_edits = []
        for i in range(4):
            le = QLineEdit()
            le.setPlaceholderText(f"Отговор {i+1}")
            le.setMinimumHeight(20)
            le.setFont(QFont("Helvetica", 12))
            self.option_edits.append(le)
            form.addRow(f"Вариант {i+1}:", le)

        # Картинка (по избор)
        self.image_edit = QLineEdit()
        self.image_edit.setPlaceholderText("име на файл от images/ (по избор)")
        self.image_edit.setMinimumHeight(20)
        self.image_edit.setFont(QFont("Helvetica", 11))
        form.addRow("Картинка:", self.image_edit)

        # бутони OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # ако редактираме съществуващ въпрос – попълваме полетата
        if question_data:
            qtype = question_data.get("type", "choice")
            idx = 0 if qtype == "choice" else 1
            self.type_combo.setCurrentIndex(idx)

            self.question_edit.setPlainText(question_data.get("question", ""))
            self.answer_edit.setText(question_data.get("answer", ""))

            if qtype == "choice":
                opts = question_data.get("options", [])
                for i in range(min(4, len(opts))):
                    self.option_edits[i].setText(opts[i])

            self.image_edit.setText(question_data.get("image", ""))

        # показваме/скриваме полетата за опции според type
        self.type_combo.currentIndexChanged.connect(self._update_type_visibility)
        self._update_type_visibility()

    def _update_type_visibility(self):
        qtype = self.type_combo.currentData()
        is_choice = (qtype == "choice")
        for le in self.option_edits:
            le.setEnabled(is_choice)
            le.setVisible(is_choice)

    def _on_accept(self):
        data = self.get_data()
        if data is not None:
            self.question_data = data
            self.accept()

    def get_data(self):
        """
        Връща dict във формата:
        {
            "type": "choice"/"text",
            "question": "...",
            "answer": "...",
            "options": [...],   # само за choice
            "image": "..."      # ако е попълнено
        }
        """
        qtype = self.type_combo.currentData()
        question = self.question_edit.toPlainText()
        answer = self.answer_edit.text().strip()
        image = self.image_edit.text().strip()

        if not question:
            QMessageBox.warning(self, "Грешка", "Моля въведете въпрос.")
            return None
        if not answer:
            QMessageBox.warning(self, "Грешка", "Моля въведете верния отговор.")
            return None

        data = {
            "type": qtype,
            "question": question,
            "answer": answer,
        }

        if qtype == "choice":
            options = [le.text().strip() for le in self.option_edits if le.text().strip()]
            if len(options) < 2:
                QMessageBox.warning(self, "Грешка", "Моля въведете поне 2 възможни отговора.")
                return None
            if answer not in options:
                QMessageBox.warning(
                    self,
                    "Грешка",
                    "Верният отговор трябва да съвпада с един от вариантите."
                )
                return None
            data["options"] = options

        if image:
            data["image"] = image

        return data


class QuestionEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Редактор на въпроси")
        self.resize(900, 650)

        base_path = os.path.dirname(os.path.abspath(__file__))
        self.questions_path = os.path.join(base_path, "questions")

        self.current_grade = None
        self.current_category = None
        self.questions = []

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ред за избор на клас и предмет
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.grade_combo = QComboBox()
        for g, label in GRADE_DISPLAY.items():
            self.grade_combo.addItem(label, g)
        top_row.addWidget(QLabel("Клас:"))
        top_row.addWidget(self.grade_combo)

        self.cat_combo = QComboBox()
        for key, label in CATEGORIES.items():
            self.cat_combo.addItem(label, key)
        top_row.addWidget(QLabel("Предмет:"))
        top_row.addWidget(self.cat_combo)

        load_btn = QPushButton("Зареди")
        load_btn.clicked.connect(self.load_questions)
        top_row.addWidget(load_btn)

        main_layout.addLayout(top_row)

        # списък с въпроси
        self.list_widget = QListWidget()
        font = QFont("Helvetica", 11)
        self.list_widget.setFont(font)
        main_layout.addWidget(self.list_widget, 1)

        # ред с бутони за CRUD
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        add_btn = QPushButton("Добави")
        edit_btn = QPushButton("Редактирай")
        delete_btn = QPushButton("Изтрий")
        save_btn = QPushButton("Запази")

        add_btn.clicked.connect(self.add_question)
        edit_btn.clicked.connect(self.edit_question)
        delete_btn.clicked.connect(self.delete_question)
        save_btn.clicked.connect(self.save_questions)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)

        main_layout.addLayout(btn_row)

    # -------------------------------------------------------
    #  Зареждане / запис на JSON
    # -------------------------------------------------------
    def get_current_filename(self):
        grade = self.grade_combo.currentData()
        cat = self.cat_combo.currentData()
        if not grade or not cat:
            return None
        return os.path.join(self.questions_path, f"{grade}_{cat}.json")

    def load_questions(self):
        filename = self.get_current_filename()
        if not filename:
            QMessageBox.warning(self, "Грешка", "Моля изберете клас и предмет.")
            return

        self.current_grade = self.grade_combo.currentData()
        self.current_category = self.cat_combo.currentData()

        if not os.path.exists(filename):
            # ако файлът не съществува – започваме с празен списък
            self.questions = []
            self.refresh_list()
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.questions = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Не мога да прочета файла:\n{e}")
            return

        if not isinstance(self.questions, list):
            QMessageBox.critical(self, "Грешка", "Файлът няма валиден формат (очаквам списък).")
            self.questions = []
            return

        self.refresh_list()

    def save_questions(self):
        filename = self.get_current_filename()
        if not filename:
            QMessageBox.warning(self, "Грешка", "Моля изберете клас и предмет.")
            return

        os.makedirs(self.questions_path, exist_ok=True)

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.questions, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Грешка", f"Не мога да запиша файла:\n{e}")
            return

        QMessageBox.information(self, "Готово", "Въпросите са записани успешно.")

    # -------------------------------------------------------
    #  Работа със списъка
    # -------------------------------------------------------
    def refresh_list(self):
        self.list_widget.clear()
        for i, q in enumerate(self.questions):
            text = q.get("question", "").strip().replace("\n", " ")
            if len(text) > 80:
                text = text[:77] + "..."
            item = QListWidgetItem(f"{i+1}. {text}")
            self.list_widget.addItem(item)

    def add_question(self):
        dlg = QuestionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if data:
                self.questions.append(data)
                self.refresh_list()

    def edit_question(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.questions):
            QMessageBox.warning(self, "Грешка", "Моля изберете въпрос за редакция.")
            return

        current = self.questions[row]
        dlg = QuestionDialog(self, current)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if data:
                self.questions[row] = data
                self.refresh_list()

    def delete_question(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.questions):
            QMessageBox.warning(self, "Грешка", "Моля изберете въпрос за изтриване.")
            return

        confirm = QMessageBox.question(
            self,
            "Потвърждение",
            "Сигурни ли сте, че искате да изтриете този въпрос?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.questions[row]
            self.refresh_list()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # първо – login
    login = LoginDialog()
    if login.exec() != QDialog.Accepted:
        sys.exit(0)

    window = QuestionEditor()
    window.show()
    sys.exit(app.exec())