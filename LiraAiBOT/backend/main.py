"""
Главный файл запуска Telegram бота.
"""
import asyncio
import logging
import sys
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# ============================================
# Автоматическая установка зависимостей
# Для bothost.ru и других серверов
# ============================================

def install_requirements():
    """Устанавливает зависимости из requirements.txt"""
    req_path = Path(__file__).parent.parent / "requirements.txt"
    if req_path.exists():
        print(f"📦 Проверка зависимостей из {req_path}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(req_path), "-q", "--upgrade"
            ])
            print("✅ Все зависимости установлены!")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Ошибка установки зависимостей: {e}")
            print("⚠️ Продолжаю работу с доступными пакетами...")
    else:
        print(f"⚠️ requirements.txt не найден: {req_path}")

# Устанавливаем зависимости если не запущены в режиме разработки
if not os.environ.get("DEV_MODE", "false").lower() == "true":
    install_requirements()

# Устанавливаем критичные пакеты если не установлены
try:
    import supabase
except ImportError:
    print("⚠️ Устанавливаю supabase...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "-q"])
    print("✅ supabase установлен!")

try:
    from google import genai
except ImportError:
    print("⚠️ Устанавливаю google-genai...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-genai>=1.0.0", "-q"])
    print("✅ google-genai установлен!")

try:
    import telethon
except ImportError:
    print("⚠️ Устанавливаю telethon...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon", "-q"])
    print("✅ telethon установлен!")

try:
    import huggingface_hub
except ImportError:
    print("⚠️ Устанавливаю huggingface_hub...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub", "-q"])
    print("✅ huggingface_hub установлен!")

# Проверяем ffmpeg для обработки голоса
def check_ffmpeg():
    """Проверяет наличие ffmpeg в системе"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ ffmpeg найден")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ ffmpeg не найден! Голосовые функции могут не работать.")
        print("⚠️ Для установки выполните: sudo apt-get install ffmpeg")
        return False

check_ffmpeg()

# Добавляем путь к корню проекта в sys.path для правильных импортов
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn

# Импорты API
from api import routes
from backend.web.routes import router as web_router

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

# Импортируем telegram_polling ПОСЛЕ настройки логирования
from api.telegram_polling import start_telegram_polling

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
app.include_router(web_router)

# Статические файлы
frontend_path = Path(__file__).parent.parent / "frontend" / "public"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

web_static_path = Path(__file__).parent / "web" / "static"
if web_static_path.exists():
    app.mount("/web-static", StaticFiles(directory=str(web_static_path)), name="web-static")

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
            # Добавляем админа только если база доступна
            try:
                db.add_or_update_user(admin_user_id, first_name="Admin")
                db.set_user_access_level(admin_user_id, "admin")
                logger.info(f"✅ Администратор установлен: {admin_user_id}")
                # Принудительно обновляем кэш админа
                from backend.database.users_db import _user_cache
                if admin_user_id in _user_cache:
                    _user_cache[admin_user_id]["access_level"] = "admin"
                    logger.info(f"📝 Кэш админа обновлён")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось установить админа: {e}")
                logger.info("ℹ️ Админ будет добавлен при первом запросе")
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
        logger.info("⚠️ Продолжаем работу...")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    logger.info("🛑 Завершение работы бота...")
    logger.info("✅ Бот завершил работу корректно")

@app.get("/")
async def root():
    """Корень домена ведёт в веб-интерфейс."""
    return RedirectResponse(url="/web", status_code=302)

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
        app,
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=False,
        log_level="info"
    )
