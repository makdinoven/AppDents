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

        # размер логотипа: 25% ширины страницы
        logo_width = rect.width * 0.12
        logo_height = logo_width

        # Отступы от правого и нижнего краёв
        margin_right = 20  # 20 pt от правого края
        margin_bottom = 20  # 20 pt от нижнего края

        x1 = rect.width - margin_right
        x0 = x1 - logo_width
        y1 = rect.height - margin_bottom
        y0 = y1 - logo_height

        logo_rect = fitz.Rect(x0, y0, x1, y1)

        # вставляем картинку поверх текста
        page.insert_image(
            logo_rect,
            pixmap=logo_pix,
            keep_proportion=True,
            overlay=True,   # логотип сверху
        )

        if text:
            # Текст по центру внизу страницы
            text_box_height = rect.height * 0.03  # высота области под текст
            margin_bottom_text = rect.height * 0.015

            text_y1 = rect.height - margin_bottom_text
            text_y0 = text_y1 - text_box_height

            page.insert_textbox(
                fitz.Rect(0, text_y0, rect.width, text_y1),
                text,
                fontsize=14,  # крупнее шрифт
                align=1,  # 1 = центр
                color=(0, 0, 0),
                fill_opacity=0.4,  # можно подстроить по вкусу
            )

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()
