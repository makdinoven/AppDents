import pymupdf as fitz
from pathlib import Path


def load_logo_with_opacity(logo_path: str, opacity_logo: float) -> fitz.Pixmap:
    """
    Загружает PNG и применяет к нему прозрачность (0..1),
    возвращает Pixmap, который можно передать в insert_image.
    """
    pix = fitz.Pixmap(logo_path)

    # если нет альфа-канала — добавляем
    if not pix.alpha:
        pix = fitz.Pixmap(pix, 1)

    alpha_val = int(max(0, min(1, opacity_logo)) * 255)
    pixel_count = pix.width * pix.height
    alphas = bytes([alpha_val] * pixel_count)
    pix.set_alpha(alphas)
    return pix


def apply_watermark(
    input_path: Path,
    output_path: Path,
    logo_path: Path,
    text: str | None,
    opacity: float = 0.3,       # прозрачность текста
    opacity_logo: float = 0.3,  # прозрачность логотипа
) -> None:
    """
    Накладывает логотип как вотермарку на каждую 10-ю страницу PDF.
    """

    doc = fitz.open(input_path)

    # готовим логотип с альфой один раз
    logo_pix = load_logo_with_opacity(str(logo_path), opacity_logo)

    for i in range(len(doc)):
        page_num = i + 1  # 1-based
        # только 1-я и каждая 10-я страница
        if page_num != 1 and page_num % 10 != 0:
            continue

        page = doc[i]
        rect = page.rect

        # Размер логотипа: 25% ширины страницы
        logo_width = rect.width * 0.25
        logo_height = logo_width

        # Снизу по центру
        x0 = (rect.width - logo_width) / 2
        y0 = rect.height - logo_height - 20
        x1 = x0 + logo_width
        y1 = y0 + logo_height
        logo_rect = fitz.Rect(x0, y0, x1, y1)

        # Вставляем картинку (pixmap, а НЕ stream)
        page.insert_image(
            logo_rect,
            pixmap=logo_pix,
            keep_proportion=True,
            overlay=True,   # логотип поверх текста
        )

        if text:
            text_y = y0 - 10
            page.insert_textbox(
                fitz.Rect(0, text_y - 20, rect.width, text_y),
                text,
                fontsize=10,
                align=1,
                color=(0, 0, 0),
                fill_opacity=opacity,
            )

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()
