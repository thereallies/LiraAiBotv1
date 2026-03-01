"""
Конфигурационный файл для Telegram бота.
Содержит все основные настройки и параметры.
"""
import os
from pathlib import Path
from typing import List

# Загружаем .env файл если он существует
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл: {env_path}")
except ImportError:
    print("⚠️ python-dotenv не установлен")
except Exception as e:
    print(f"⚠️ Ошибка загрузки .env: {e}")

# Базовые пути
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Создаем директории, если они не существуют
for dir_path in [DATA_DIR, TEMP_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

def get_all_openrouter_keys() -> List[str]:
    """
    Динамически собирает все доступные OpenRouter API ключи из переменных окружения.
    """
    ordered_keys: List[str] = []

    def add_key(value: str):
        if value and value != "your_openrouter_api_key" and value not in ordered_keys:
            ordered_keys.append(value)

    # Основной ключ
    add_key(os.environ.get("OPENROUTER_API_KEY", ""))

    # Нумерованные ключи
    i = 1
    while True:
        env_name = f"OPENROUTER_API_KEY{i}"
        val = os.environ.get(env_name, "")
        if not val:
            break
        add_key(val)
        i += 1

    # PAID ключ (добавляем в конец, чтобы использовать его после обычных)
    add_key(os.environ.get("OPENROUTER_API_KEY_PAID", ""))

    return ordered_keys

# Получаем все доступные ключи
OPENROUTER_API_KEYS = get_all_openrouter_keys()
OPENROUTER_API_KEY = OPENROUTER_API_KEYS[0] if OPENROUTER_API_KEYS else ""

# Telegram токены (поддержка нескольких ботов)
def get_all_telegram_tokens() -> List[str]:
    """
    Динамически собирает все доступные Telegram токены из переменных окружения.
    """
    ordered_tokens: List[str] = []

    def add_token(value: str):
        if value and value != "your_telegram_bot_token" and value not in ordered_tokens:
            ordered_tokens.append(value)

    # Основной токен
    add_token(os.environ.get("TELEGRAM_BOT_TOKEN", ""))

    # Нумерованные токены
    i = 2
    while True:
        env_name = f"TELEGRAM_BOT_TOKEN{i}"
        val = os.environ.get(env_name, "")
        if not val:
            break
        add_token(val)
        i += 1

    return ordered_tokens

TELEGRAM_BOT_TOKENS = get_all_telegram_tokens()
TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKENS[0] if TELEGRAM_BOT_TOKENS else ""
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", "")

# API ключи для генерации изображений
HF_API_KEY = os.environ.get("HF_API_KEY", "") or os.environ.get("HF_API_TOKEN", "")
STABLE_HORDE_API_KEY = os.environ.get("STABLE_HORDE_API_KEY", "")
DEEPAI_API_KEY = os.environ.get("DEEPAI_API_KEY", "")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")

# BingX API для криптотрейдинга
BINGX_API_KEY = os.environ.get("BINGX_API_KEY", "")
BINGX_SECRET_KEY = os.environ.get("BINGX_SECRET_KEY", "")
BINGX_API_URL = os.environ.get("BINGX_API_URL", "https://open-api.bingx.com")
BINGX_TESTNET = os.environ.get("BINGX_TESTNET", "false").lower() == "true"

# ElevenLabs API ключи (можно несколько)
def get_all_eleven_keys() -> List[str]:
    """Собирает все ElevenLabs API ключи"""
    keys = []
    # Основной ключ
    key = os.environ.get("ELEVEN_API_KEY", "") or os.environ.get("ELEVEN_API", "")
    if key:
        keys.append(key)
    # Дополнительные ключи
    for i in range(2, 5):
        env_key = f"ELEVEN_API{i}"
        val = os.environ.get(env_key, "")
        if val:
            keys.append(val)
    return keys

ELEVEN_API_KEYS = get_all_eleven_keys()
ELEVEN_VOICE_ID = os.environ.get("ELEVEN_VOICE_ID", "")
ELEVEN_VOICE_ID_MALE = os.environ.get("ELEVEN_VOICE_ID_MALE", "")
ELEVEN_VOICE_ID_FEMALE = os.environ.get("ELEVEN_VOICE_ID_FEMALE", "")
ELEVEN_MODEL_ID = os.environ.get("ELEVEN_MODEL_ID", "eleven_multilingual_v2")
ELEVEN_PROXIES = os.environ.get("ELEVEN_PROXIES", "")

# Дополнительные настройки
LLM_API = os.environ.get("LLM_API", "")
ENABLE_AUTONOMOUS_GROUP_CHAT = os.environ.get("ENABLE_AUTONOMOUS_GROUP_CHAT", "false").lower() == "true"
AUTONOMOUS_INTERVAL_HOURS = int(os.environ.get("AUTONOMOUS_INTERVAL_HOURS", "1"))
MAX_CONVERSATION_EXCHANGES = int(os.environ.get("MAX_CONVERSATION_EXCHANGES", "50"))

# Настройки FeedbackBot
FEEDBACK_BOT_ENABLED = os.environ.get("FEEDBACK_BOT_ENABLED", "false").lower() == "true"
FEEDBACK_BOT_GROUP_IDS = [gid.strip() for gid in os.environ.get("FEEDBACK_BOT_GROUP_IDS", "").split(",") if gid.strip()]
FEEDBACK_KNOWLEDGE_DIR = BASE_DIR / "data" / "feedback_knowledge"

# Настройки LLM
# Используем бесплатные модели: Solar, Trinity, GLM
LLM_CONFIG = {
    "model": "upstage/solar-pro-3:free",  # Бесплатная Solar Pro 3
    "fallback_model": "arcee-ai/trinity-mini:free",  # Бесплатная Trinity Mini
    "temperature": 0.7,
    "max_tokens": 2048,  # Увеличено для полных ответов
}

# Настройки эмбеддингов
EMBEDDING_CONFIG = {
    "model": "text-embedding-3-small",
    "dimensions": 384,
    "local_fallback": "all-MiniLM-L6-v2",
}

# Настройки API
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8001,  # Изменен порт из-за конфликта с 8000
    "debug": True,
}

# Настройки Telegram бота
# Группы для отправки сообщений (загружаются из .env)
def load_telegram_group_ids() -> List[str]:
    """Загружает ID групп из .env файла"""
    try:
        # Импортируем только когда нужно, чтобы избежать циклических импортов
        import sys
        from pathlib import Path
        utils_path = Path(__file__).parent / "utils"
        if str(utils_path) not in sys.path:
            sys.path.insert(0, str(utils_path.parent))
        from utils.group_manager import get_all_group_ids
        return get_all_group_ids()
    except Exception as e:
        # При ошибке возвращаем пустой список (группы загрузятся позже)
        return []

TELEGRAM_GROUP_IDS = load_telegram_group_ids()

TELEGRAM_CONFIG = {
    "token": TELEGRAM_BOT_TOKEN,
    "tokens": TELEGRAM_BOT_TOKENS,  # Список всех токенов
    "group_ids": TELEGRAM_GROUP_IDS,  # ID групп для отправки сообщений
    "use_webhook": False,
}

# Настройки голосовых моделей
VOICE_CONFIG = {
    "tts": {
        "model": "gtts",
        "language": "ru",
    },
    "stt": {
        "model": "whisper",
        "language": "ru",
    }
}

class Config:
    """Централизованный класс конфигурации"""
    
    def __init__(self):
        self.HOST = API_CONFIG["host"]
        self.PORT = API_CONFIG["port"]
        self.DEBUG = API_CONFIG["debug"]
        
        self.OPENROUTER_API_KEYS = OPENROUTER_API_KEYS
        self.TELEGRAM_BOT_TOKENS = TELEGRAM_BOT_TOKENS
        self.TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN
        self.EMBEDDING_API_KEY = EMBEDDING_API_KEY
        self.HF_API_KEY = HF_API_KEY
        self.STABLE_HORDE_API_KEY = STABLE_HORDE_API_KEY
        self.DEEPAI_API_KEY = DEEPAI_API_KEY
        self.REPLICATE_API_TOKEN = REPLICATE_API_TOKEN
        
        # BingX API
        self.BINGX_API_KEY = BINGX_API_KEY
        self.BINGX_SECRET_KEY = BINGX_SECRET_KEY
        self.BINGX_API_URL = BINGX_API_URL
        self.BINGX_TESTNET = BINGX_TESTNET
        
        # ElevenLabs
        self.ELEVEN_API_KEYS = ELEVEN_API_KEYS
        self.ELEVEN_VOICE_ID = ELEVEN_VOICE_ID
        self.ELEVEN_VOICE_ID_MALE = ELEVEN_VOICE_ID_MALE
        self.ELEVEN_VOICE_ID_FEMALE = ELEVEN_VOICE_ID_FEMALE
        self.ELEVEN_MODEL_ID = ELEVEN_MODEL_ID
        self.ELEVEN_PROXIES = ELEVEN_PROXIES
        
        # Дополнительные настройки
        self.LLM_API = LLM_API
        self.ENABLE_AUTONOMOUS_GROUP_CHAT = ENABLE_AUTONOMOUS_GROUP_CHAT
        self.AUTONOMOUS_INTERVAL_HOURS = AUTONOMOUS_INTERVAL_HOURS
        self.MAX_CONVERSATION_EXCHANGES = MAX_CONVERSATION_EXCHANGES
        
        # FeedbackBot настройки
        self.FEEDBACK_BOT_ENABLED = FEEDBACK_BOT_ENABLED
        self.FEEDBACK_BOT_GROUP_IDS = FEEDBACK_BOT_GROUP_IDS
        self.FEEDBACK_KNOWLEDGE_DIR = FEEDBACK_KNOWLEDGE_DIR
        
        self.LLM_CONFIG = LLM_CONFIG
        self.EMBEDDING_CONFIG = EMBEDDING_CONFIG
        self.VOICE_CONFIG = VOICE_CONFIG
        self.TELEGRAM_CONFIG = TELEGRAM_CONFIG
        
        self.BASE_DIR = BASE_DIR
        self.DATA_DIR = DATA_DIR
        self.TEMP_DIR = TEMP_DIR
        self.LOGS_DIR = LOGS_DIR

