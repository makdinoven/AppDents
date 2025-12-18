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
    Накладывает логотип как вотермарку на каждую 10-ю страницу PDF.
    Логотип (PNG/SVG) делается полупрозрачным через Pixmap.
    """

    doc = fitz.open(input_path)

    # исходный pixmap логотипа
    base_pix = fitz.Pixmap(str(logo_path))

    # делаем полупрозрачный pixmap
    if base_pix.alpha:  # есть альфа-канал
        rgb = fitz.Pixmap(base_pix, 0)      # RGB
        alpha = fitz.Pixmap(base_pix, 1)    # A
        alpha = alpha.copy()
        alpha.samples = bytes(int(ch * opacity) for ch in alpha.samples)
        logo_pix = fitz.Pixmap(rgb, alpha)
        rgb = None
        alpha = None
    else:
        logo_pix = base_pix.copy()
        logo_pix.samples = bytes(int(ch * opacity) for ch in logo_pix.samples)

    for i in range(len(doc)):
        page_num = i + 1  # 1-based
        # 1-я и каждая 10-я страница
        if page_num != 1 and page_num % 10 != 0:
            continue

        page = doc[i]
        rect = page.rect

        # размеры логотипа
        logo_width = 50
        logo_height = 50

        # отступы — ставим в правый верхний угол
        margin_right = 20
        margin_top = 20

        x1 = rect.width - margin_right
        x0 = x1 - logo_width
        y0 = margin_top
        y1 = y0 + logo_height

        logo_rect = fitz.Rect(x0, y0, x1, y1)

        # вставляем полупрозрачный логотип
        page.insert_image(
            logo_rect,
            pixmap=logo_pix,
            keep_proportion=True,
            overlay=True,
        )

        # если отдельный текст не нужен (он уже в логотипе) — этот блок можно удалить
        if text:
            text_box_height = rect.height * 0.03
            margin_bottom_text = rect.height * 0.015

            text_y1 = rect.height - margin_bottom_text
            text_y0 = text_y1 - text_box_height

            page.insert_textbox(
                fitz.Rect(0, text_y0, rect.width, text_y1),
                text,
                fontsize=14,
                align=1,
                color=(0, 0, 0),
                fill_opacity=opacity,
            )

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()
