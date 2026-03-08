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

# Делаем entrypoint исполняемым
RUN chmod +x /app/docker-entrypoint.sh

# Запускаем через универсальный entrypoint для Bothost
CMD ["/app/docker-entrypoint.sh"]
