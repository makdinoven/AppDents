import pymupdf as fitz
from pathlib import Path


def apply_watermark(
    input_path: Path,
    output_path: Path,
    logo_path: Path,
    text: str | None,
    opacity: float = 0.3,   # прозрачность только для текста
) -> None:
    """
    Накладывает логотип как вотермарку на каждую 10-ю страницу PDF.
    Логотип вставляется как есть (прозрачность берётся из PNG).
    """

    doc = fitz.open(input_path)

    # просто читаем PNG с логотипом
    logo_pix = fitz.Pixmap(str(logo_path))

    for i in range(len(doc)):
        page_num = i + 1  # 1-based
        # 1-я и каждая 10-я страница
        if page_num != 1 and page_num % 10 != 0:
            continue

        page = doc[i]
        rect = page.rect

        # фиксированные размеры логотипа (в «пикселях» PDF)
        logo_width = 50
        logo_height = 50

        # фиксированные отступы от правого и нижнего краёв
        margin_right = 20
        margin_bottom = 0

        x1 = rect.width - margin_right
        x0 = x1 - logo_width
        y1 = rect.height - margin_bottom
        y0 = y1 - logo_height

        logo_rect = fitz.Rect(x0, y0, x1, y1)

        # один раз вставляем логотип поверх текста
        page.insert_image(
            logo_rect,
            pixmap=logo_pix,
            keep_proportion=True,
            overlay=True,
        )

        if text:
            # Текст по центру внизу страницы
            text_box_height = rect.height * 0.03
            margin_bottom_text = rect.height * 0.015

            text_y1 = rect.height - margin_bottom_text
            text_y0 = text_y1 - text_box_height

            page.insert_textbox(
                fitz.Rect(0, text_y0, rect.width, text_y1),
                text,
                fontsize=14,
                align=1,          # центр
                color=(0, 0, 0),
                fill_opacity=opacity,
            )

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()
