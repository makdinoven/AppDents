# ------------------------------------------------------------
# Базовый образ с Python 3.12 + Calibre (ebook-convert)
# ------------------------------------------------------------
FROM python:3.12-slim

# 1) Базовые системные зависимости + headless-библиотеки для Calibre
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libmariadb-dev-compat \
        libmariadb-dev \
        ffmpeg \
        ghostscript \
        wget \
        xz-utils \
        ca-certificates \
        libglib2.0-0 \
        libxrender1 \
        libfontconfig1 \
        libxext6 \
        libsm6 \
        libx11-6 \
        libnss3 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*


# 2) Установка Calibre через официальный инсталлятор
#    Скрипт кладёт бинарники в /opt/calibre и создаёт symlink'и
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin \
    && /opt/calibre/ebook-convert --version

# 3) ENV: прокинем путь к Calibre и укажем бинарь для наших тасок
ENV PATH="/opt/calibre:${PATH}"
ENV EBOOK_CONVERT_BIN="/opt/calibre/ebook-convert"
ENV CALIBRE_NO_NATIVE_FILEDIALOG=1

# 4) Python-приложение (как было)
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

# 5) Команда по умолчанию — API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
