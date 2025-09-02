FROM python:3.12-slim

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
    libharfbuzz0b libpng16-16 \
    # 👉 добавляем отсутствующие библиотеки
    libxcb-cursor0 libxkbcommon-x11-0 \
 && rm -rf /var/lib/apt/lists/*

# Установка Calibre
RUN wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin

# Проверка
RUN /opt/calibre/ebook-convert --version

ENV PATH="/opt/calibre:${PATH}"
ENV EBOOK_CONVERT_BIN="/opt/calibre/ebook-convert"
ENV CALIBRE_NO_NATIVE_FILEDIALOG=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
