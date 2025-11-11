FROM python:3.12-slim

ARG DEBIAN_FRONTEND=noninteractive

# 1) Базовые нативные пакеты (как у тебя) + доп. зависимости для нормализаций и OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev-compat libmariadb-dev \
    ffmpeg ghostscript wget xz-utils ca-certificates \
    # графические/Qt deps для Calibre GUI-библиотек, нужных его CLI
    libegl1 libopengl0 libgl1 \
    libxkbcommon0 libxcomposite1 libxrandr2 libxdamage1 libxfixes3 \
    libxcb1 libxext6 libxi6 libx11-6 libx11-xcb1 \
    libglib2.0-0 libnss3 libnspr4 \
    libdrm2 libgbm1 libxshmfence1 \
    libfontconfig1 libxrender1 libsm6 \
    fonts-dejavu-core fonts-liberation \
    libharfbuzz0b libpng16-16 \
    libxcb-cursor0 libxkbcommon-x11-0 \
    # 🔹 НОВОЕ: стек нормализаций и OCR
    qpdf mupdf-tools \            # qpdf + mutool (для clean/linearize)
    ocrmypdf \                    # сам OCR-оркестратор
    tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus \  # движок и языки
    pngquant unpaper \            # ускорение и авто-очистка страниц (по желанию)
 && rm -rf /var/lib/apt/lists/*

# 2) Установка Calibre (как у тебя)
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# 3) Проверки версий (важно для диагностики на старте контейнера)
RUN /opt/calibre/ebook-convert --version \
 && ocrmypdf --version \
 && tesseract --version \
 && qpdf --version \
 && mutool -v

# 4) ENV для приложения и Calibre/OCR
ENV PATH="/opt/calibre:${PATH}"
ENV EBOOK_CONVERT_BIN="/opt/calibre/ebook-convert"
ENV CALIBRE_NO_NATIVE_FILEDIALOG=1
ENV PYTHONUNBUFFERED=1

# 🔹 Настройки по умолчанию для нашего пайплайна (можешь переопределять в compose)
# — включаем OCR-вставку (применяется в OCR-ветке, если PDF — скан)
ENV CALIBRE_ENABLE_OCR=1
ENV OCR_LANGS="eng+rus"
# — набор флагов, которые ты использовал в коде
ENV OCR_OPTS="--skip-text --rotate-pages --deskew --clean-final --optimize 3"

# — стратегия префлайта и сторожей (равны тем, что у тебя в коде/ENV)
ENV CALIBRE_PDF_PREFLIGHT_STRATEGY="gs,mutool,qpdf"
ENV CALIBRE_STALL_NO_OUTPUT_SECS="1000"
ENV CALIBRE_STALL_NO_PROGRESS_SECS="2600"
ENV CALIBRE_MAX_STAGE_SECS="5400"
ENV CALIBRE_PROGRESS_HEARTBEAT="60"
ENV CALIBRE_CONVERT_LOG_LEVEL="INFO"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
