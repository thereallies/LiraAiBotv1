"""
Точка входа для деплоя на bothost.ru
Импортирует и запускает приложение из backend/main.py

Bothost.ru автоматически запускает uvicorn с этим файлом.
Просто экспортируем FastAPI приложение.
"""
import sys
import os
from pathlib import Path

# Добавляем корень проекта в path чтобы 'backend' был доступен как модуль
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Загружаем переменные окружения из .env
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Импортируем FastAPI приложение из backend.main
from backend.main import app

# Экспортируем для uvicorn/gunicorn
__all__ = ["app"]


