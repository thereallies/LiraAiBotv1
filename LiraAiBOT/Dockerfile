# Dockerfile для LiraAI Bot на bothost.ru
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt первым для кэширования
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём директории для данных и логов
RUN mkdir -p /app/data /app/logs /app/temp && chmod -R 777 /app

# Проверяем, что index.py существует
RUN test -f /app/index.py || (echo "❌ index.py не найден!" && exit 1)

# Запускаем через index.py (точка входа для bothost)
CMD ["python", "index.py"]
