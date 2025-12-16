import pymupdf as fitz
from pathlib import Path


def apply_watermark(
    input_path: Path,
    output_path: Path,
    logo_path: Path,
    text: str | None,
    opacity: float = 0.3,
) -> None:
    """
    Накладывает логотип + текст как вотермарку на каждую 10-ю страницу PDF.

    - input_path: исходный PDF
    - output_path: путь, куда сохранить результат
    - logo_path: PNG-логотип
    - text: строка текста под/над логотипом или None
    - opacity: прозрачность (0..1)
    """
    doc = fitz.open(input_path)
    logo_bytes = Path(logo_path).read_bytes()

    for i in range(len(doc)):
        page_num = i + 1  # 1-based
        if page_num % 10 != 0:
            continue

        page = doc[i]
        rect = page.rect

        # Размер логотипа: 25% ширины страницы
        logo_width = rect.width * 0.25
        logo_height = logo_width

        # Снизу по центру
        x0 = (rect.width - logo_width) / 2
        y0 = rect.height - logo_height - 20  # отступ 20pt от нижнего края
        x1 = x0 + logo_width
        y1 = y0 + logo_height

        # Вставляем картинку
        page.insert_image(
            fitz.Rect(x0, y0, x1, y1),
            stream=logo_bytes,
            keep_proportion=True,
            overlay=True,
        )

        if text:
            # Текст чуть выше логотипа
            text_y = y0 - 10
            page.insert_textbox(
                fitz.Rect(0, text_y - 20, rect.width, text_y),
                text,
                fontsize=10,
                align=1,  # центр
                color=(0, 0, 0),
                fill_opacity=opacity,
            )

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()
