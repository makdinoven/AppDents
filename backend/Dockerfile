# ------------------------------------------------------------
# Базовый образ с Python 3.12 + Calibre (ebook-convert)
# ------------------------------------------------------------
FROM python:3.12-slim

# 1) Базовые системные зависимости + headless-библиотеки для Calibre
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev-compat libmariadb-dev \
    ffmpeg ghostscript wget xz-utils ca-certificates \
    # базовые X/GL/Qt зависимости:
    libegl1 libopengl0 libgl1 \
    libxkbcommon0 libxcomposite1 libxrandr2 libxdamage1 libxfixes3 \
    libxcb1 libxext6 libxi6 libx11-6 libx11-xcb1 \
    libglib2.0-0 libnss3 libnspr4 \
    libdrm2 libgbm1 libxshmfence1 \
    libfontconfig1 libxrender1 libsm6 \
    fonts-dejavu-core fonts-liberation \
    # иногда требуются для рендеринга шрифтов/изображений:
    libharfbuzz0b libpng16-16 \
 && rm -rf /var/lib/apt/lists/*

RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

RUN /opt/calibre/ebook-convert --version

ENV PATH="/opt/calibre:${PATH}"
ENV EBOOK_CONVERT_BIN="/opt/calibre/ebook-convert"
ENV CALIBRE_NO_NATIVE_FILEDIALOG=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# 5) Команда по умолчанию — API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
