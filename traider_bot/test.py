from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdf_output = 'output.pdf'
text = "Пример текста с кириллицей: Шелковый краб"

# Создаем объект Canvas
c = canvas.Canvas(pdf_output, pagesize=letter)

# Регистрация шрифта для поддержки Unicode
pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))

# Установка шрифта
c.setFont("Arial", 12)

# Добавление текста в документ
c.drawString(100, 750, text)

# Сохранение PDF
c.save()
