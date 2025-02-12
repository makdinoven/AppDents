FROM python:3.12-slim

# 1. Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev-compat \
    libmariadb-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# 2. Установка рабочей директории
WORKDIR /app

# 3. Копируем requirements.txt и устанавливаем пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем исходный код
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
