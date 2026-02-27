"""
Главный файл запуска Telegram бота.
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к корню проекта в sys.path для правильных импортов
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Импорты API
from api import routes
from api.telegram_polling import start_telegram_polling

# Настройка логирования
os.makedirs('logs', exist_ok=True)

# Настройка уровня логирования
log_level = logging.DEBUG if os.environ.get("DEBUG", "false").lower() == "true" else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("bot.main")

# Создание FastAPI приложения
app = FastAPI(
    title="LiraAI MultiAssistent API",
    description="Мультимодальный Telegram бот с поддержкой текста, голоса и изображений",
    version="1.0.0"
)

# CORS middleware - настраиваем разрешенные источники
cors_origins = os.environ.get("CORS_ORIGINS", "").split(",") if os.environ.get("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Подключение маршрутов
app.include_router(routes.router, prefix="/api")

# Статические файлы
frontend_path = Path(__file__).parent.parent / "frontend" / "public"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("🚀 Запуск LiraAI MultiAssistent v1.0.0")

    try:
        # Создаем необходимые директории
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("temp", exist_ok=True)

        # Инициализируем базу данных
        from backend.database.users_db import get_database
        db = get_database()
        logger.info(f"✅ База данных инициализирована")
        
        # Устанавливаем администратора из переменной окружения
        admin_user_id = os.environ.get("ADMIN_USER_ID")
        if admin_user_id:
            db.add_or_update_user(admin_user_id, first_name="Admin")
            db.set_user_access_level(admin_user_id, "admin")
            logger.info(f"✅ Администратор установлен: {admin_user_id}")
        else:
            logger.warning("⚠️ ADMIN_USER_ID не установлен в .env")

        # Запускаем Telegram polling
        logger.info("📱 Запуск Telegram polling...")
        asyncio.create_task(start_telegram_polling())
        logger.info("✅ Telegram polling запущен")

        logger.info("🎉 Бот полностью инициализирован и готов к работе!")

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации: {e}")
        # Не падаем - polling будет работать даже если сервер не запустился
        logger.info("⚠️ Продолжаем работу без веб-сервера...")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    logger.info("🛑 Завершение работы бота...")
    logger.info("✅ Бот завершил работу корректно")

@app.get("/")
async def root():
    """Главная страница"""
    return {"message": "LiraAI MultiAssistent API v1.0.0"}

@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Запуск сервера
    from backend.config import API_CONFIG
    uvicorn.run(
        "main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=False,
        log_level="info"
    )

