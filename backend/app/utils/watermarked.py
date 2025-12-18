import pymupdf as fitz
from pathlib import Path


def apply_watermark(
    input_path: Path,
    output_path: Path,
    logo_path: Path,
    text: str | None,
    opacity: float = 0.3,
) -> None:
    doc = fitz.open(input_path)

    # базовый pixmap логотипа
    pix = fitz.Pixmap(str(logo_path))

    # гарантируем альфа-канал и задаём прозрачность
    if not pix.alpha:
        # добавляем альфу, все значения 255 (полностью непрозрачный)
        pix = fitz.Pixmap(pix, 1)

    pixel_count = pix.width * pix.height
    alpha_value = int(255 * opacity)  # 0..255
    alphas = bytes([alpha_value] * pixel_count)
    pix.set_alpha(alphas)

    logo_pix = pix  # готовый полупрозрачный логотип

    for i in range(len(doc)):
        page_num = i + 1
        if page_num != 1 and page_num % 10 != 0:
            continue

        page = doc[i]
        rect = page.rect

        logo_width = 50
        logo_height = 50
        margin_right = 20
        margin_top = 20  # вверх, чтобы не закрывать подписи

        x1 = rect.width - margin_right
        x0 = x1 - logo_width
        y0 = margin_top
        y1 = y0 + logo_height
        logo_rect = fitz.Rect(x0, y0, x1, y1)

        page.insert_image(
            logo_rect,
            pixmap=logo_pix,
            keep_proportion=True,
            overlay=True,
        )

        # если отдельный текст не нужен – этот блок можно удалить
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
