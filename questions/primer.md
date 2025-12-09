# Kartinki s vupros i fixiran otgovor

{
    "type": "choice",
    "question": "Колко е обиколката на този правоъгълник?",
    "image": "pravougulnik1.png",
    "options": ["12 см", "18 см", "20 см", "24 см"],
    "answer": "24 см"
}

// Kartinki i svoboden text

{
    "type": "text",
    "question": "Какво животно е показано на картинката?",
    "image": "koala.png",
    "answer": "коала"
}
# kartinkata trqbva da e 800x200 px
# ako iskate da ima samo kartinka na "question": "" (ostavqme prazen string)

#####################################
# python3 -m venv venv              #
# Widnwos -> venv\Scripts\activate  #
# Linux -> source venv/bin/activate #
# pip install PySide6 Pillow        #
# ###################################
# venv\Scripts\activate             #
# pip install pyinstaller           #
#####################################################################################################################
# pyinstaller --noconsole --icon=icon.ico ^ --add-data "images;images" ^ --add-data "questions;questions" ^ main.py #
#####################################################################################################################