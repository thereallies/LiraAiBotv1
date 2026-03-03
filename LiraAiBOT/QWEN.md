# 🤖 LiraAI MultiAssistant — Контекст для Qwen

## 📋 Обзор проекта

**LiraAI MultiAssistant** — мультимодальная платформа для создания интеллектуальных Telegram-ботов с поддержкой:
- 💬 Текстовых сообщений (LLM через OpenRouter/Groq/Cerebras)
- 🎤 Голосовых сообщений (STT/TTS)
- 📸 Изображений (анализ через Gemini, генерация через Polza.ai/Replicate)
- 🧠 Контекстной памяти (Supabase/SQLite)
- 🔧 Модульной архитектуры

**Основное применение**: Эксперт по обратной связи (FeedbackBot) для групповых чатов.

---

## 🏗️ Архитектура проекта

```
LiraAiBOT/
├── backend/
│   ├── api/                      # Telegram интеграция
│   │   ├── routes.py             # FastAPI маршруты
│   │   ├── telegram_core.py      # Низкоуровневые Telegram API вызовы
│   │   ├── telegram_polling.py   # Основной обработчик сообщений (2592 строки)
│   │   ├── telegram_vision.py    # Обработка изображений
│   │   ├── telegram_voice.py     # Обработка голосовых сообщений
│   │   └── telegram_photo_handler.py  # Обработчик фото для FeedbackBot
│   │
│   ├── core/                     # Ядро системы
│   │   └── feedback_bot.py       # FeedbackBot логика (эксперт по обратной связи)
│   │
│   ├── database/
│   │   └── users_db.py           # Работа с пользователями (Supabase/SQLite)
│   │                             # + Audit Log для действий администраторов
│   │
│   ├── internet/                 # Внешние API
│   │   └── web_search.py         # Поиск в интернете (Perplexity)
│   │
│   ├── llm/                      # LLM интеграции
│   │   ├── openrouter.py         # OpenRouter клиент (Solar, Trinity, GLM)
│   │   ├── groq.py               # Groq клиент (Llama 3.3/4, Kimi K2)
│   │   └── cerebras.py           # Cerebras клиент (сверхбыстрые модели)
│   │
│   ├── memory/                   # Система памяти
│   │   └── conversation_memory.py  # Контекстная память диалогов
│   │
│   ├── utils/                    # Утилиты
│   │   ├── keyboards.py          # Telegram клавиатуры
│   │   ├── mode_manager.py       # Управление режимами пользователей
│   │   └── group_manager.py      # Управление группами
│   │
│   ├── vision/                   # Обработка изображений
│   │   ├── gemini_image.py       # Gemini Vision API
│   │   └── hf_replicate.py       # Генерация через HuggingFace/Replicate
│   │
│   ├── voice/                    # Голосовые функции
│   │   ├── tts.py                # Text-to-Speech (gTTS/ElevenLabs)
│   │   └── stt.py                # Speech-to-Text (Whisper/SpeechRecognition)
│   │
│   ├── config.py                 # Централизованная конфигурация
│   └── main.py                   # Точка входа (FastAPI + polling)
│
├── data/                         # Данные (SQLite, кэш)
├── logs/                         # Логи
├── temp/                         # Временные файлы
├── .env                          # Переменные окружения
├── .env.example                  # Пример конфигурации
├── requirements.txt              # Python зависимости
├── ecosystem.config.js           # PM2 конфигурация
└── run.py                        # Альтернативный запуск
```

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd /Users/iluyshin.d/Desktop/LiraAiBOT
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать .env, указав:
# - TELEGRAM_BOT_TOKEN (от @BotFather)
# - OPENROUTER_API_KEY (или GROQ_API_KEY, CEREBRAS_API_KEY)
# - SUPABASE_URL и SUPABASE_KEY (опционально)
# - ADMIN_USER_ID (ваш Telegram user ID)
```

### 3. Запуск

```bash
# Из корня проекта
python run.py

# Или из backend
cd backend && python main.py

# Или через PM2 (продакшен)
pm2 start ecosystem.config.js
```

---

## 🔑 Ключевые компоненты

### `backend/config.py`
Централизованное управление конфигурацией:
- Динамическая загрузка API ключей (поддержка нескольких ключей)
- Настройки LLM моделей (температура, max_tokens)
- Конфигурация Telegram, ElevenLabs, BingX
- Пути к директориям

### `backend/api/telegram_polling.py`
Основной обработчик сообщений:
- Long polling для Telegram API
- Обработка текстов, фото, голосовых сообщений
- Система режимов (text/voice/photo/generation/auto)
- Выбор моделей через reply-клавиатуру
- Интеграция с FeedbackBot для групповых чатов

### `backend/database/users_db.py`
Управление пользователями и лимитами:
- **Supabase** (продакшен) или **SQLite** (локальная разработка)
- Уровни доступа: `admin` (безлимит), `subscriber` (5/день), `user` (3/день)
- Кэширование с TTL (5 минут)
- История генераций и диалогов
- Режим тех.работ

### `backend/core/feedback_bot.py`
Эксперт по обратной связи:
- Автоматическая обработка всех сообщений в группе
- Контекстная память (последние 20 сообщений)
- Режимы: АНАЛИЗ, КОУЧИНГ, РАЗВИТИЕ НАВЫКОВ, Q&A
- База знаний (~8000 токенов): SBI, COIN, STAR, DESC, GROW, Radical Candor

### `backend/llm/openrouter.py`
Клиент для OpenRouter API:
- Ротация API ключей при rate limit
- Fallback модели
- Поддержка chat completion формата

### `backend/utils/keyboards.py`
Telegram клавиатуры:
- Основное меню (reply)
- Выбор модели (reply)
- Inline-клавиатуры для генерации изображений

---

## 📡 Доступные модели

### Текстовые LLM

| Провайдер | Модели | Описание |
|-----------|--------|----------|
| **Groq** | `llama-3.3-70b`, `llama-4-maverick`, `llama-4-scout`, `kimi-k2` | Сверхбыстрые, бесплатные |
| **Cerebras** | `llama3.1-8b` | Молниеносные |
| **OpenRouter** | `solar-pro-3:free`, `trinity-mini:free`, `glm-4.5:free` | Качественные бесплатные |

### Генерация изображений

| Провайдер | Модели | Статус |
|-----------|--------|--------|
| **Polza.ai** | Z-Image | ✅ Работает |
| **Gemini** | Gemini 2.5 Flash | ⚠️ В разработке |

### Голосовые

| Функция | Провайдеры |
|---------|------------|
| **TTS** | gTTS (бесплатно), ElevenLabs (качество) |
| **STT** | Whisper (локально), SpeechRecognition (Google) |

---

## 🗄️ База данных

### Supabase (продакшен)

Таблицы:
- `users` — пользователи (user_id, username, access_level, created_at, last_seen)
- `generation_limits` — лимиты (daily_count, total_count, last_reset)
- `generation_history` — история генераций
- `dialog_history` — история диалогов
- `bot_settings` — настройки бота (тех.режим)
- `admin_audit_log` — журнал действий администраторов (audit log)

### SQLite (локальная разработка)

Файл: `data/bot.db`

Автоматический fallback если Supabase недоступен.
Таблица `admin_audit_log` создаётся автоматически при первом логировании.

---

## 🔧 Конфигурация (.env)

```bash
# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_GROUP_ID=-1001234567890  # ID группы для FeedbackBot

# === LLM API ===
OPENROUTER_API_KEY=sk-or-v1-xxx
GROQ_API_KEY=gsk_xxx
CEREBRAS_API_KEY=csk_xxx

# === Supabase ===
USE_SUPABASE=true
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx

# === Генерация изображений ===
HF_API_KEY=hf_xxx
REPLICATE_API_TOKEN=r8_xxx

# === Голос (опционально) ===
ELEVEN_API_KEY=xi_xxx
ELEVEN_VOICE_ID=xxx

# === Админ ===
ADMIN_USER_ID=123456789

# === Прочее ===
DEBUG=false
CORS_ORIGINS=*
```

---

## 📊 Уровни доступа

| Уровень | Лимит генераций | Описание |
|---------|-----------------|----------|
| `admin` | Безлимит | Полный доступ |
| `subscriber` | 5 в день | Подписчик |
| `user` | 3 в день | Базовый пользователь |

Сброс лимитов: каждые 24 часа (по московскому времени).

---

## 🎯 Режимы работы бота

| Режим | Описание |
|-------|----------|
| `auto` | Автоматическое определение типа сообщения |
| `text` | Текстовый диалог |
| `voice` | Распознавание голосовых сообщений |
| `photo` | Анализ изображений |
| `generation` | Генерация изображений по описанию |
| `help` | Справочная информация |
| `stats` | Статистика пользователя |

---

## 🧪 Тестирование

```bash
# Тест моделей
python test_models.py

# Тест генерации изображений
python test_hf_flux.py

# Тест Supabase
python test_supabase_tables.py

# Тест поиска (Perplexity)
python test_perplexity_websearch.py
```

---

## 🐛 Отладка

### Включить DEBUG логи

```bash
# В .env
DEBUG=true

# Или при запуске
export DEBUG=true && python backend/main.py
```

### Просмотр логов

```bash
# Логи бота
tail -f logs/bot.log

# Логи PM2
pm2 logs liraai-multiassistent
```

### Частые проблемы

| Проблема | Решение |
|----------|---------|
| Бот не отвечает | Проверить `TELEGRAM_BOT_TOKEN` в `.env` |
| Rate limit | API ключи ротируются автоматически |
| ffmpeg не найден | `sudo apt-get install ffmpeg` |
| Supabase недоступен | Автоматический fallback на SQLite |

---

## 📋 Audit Log (журнал действий администраторов)

### Команды для работы с audit log

| Команда | Описание |
|---------|----------|
| `/admin log` | Последние действия текущего администратора |
| `/admin log [user_id] [limit]` | Логи по пользователю |
| `/admin log --admin=[user_id]` | Логи администратора |
| `/admin admin_stats` | Статистика действий администратора |

### Автоматически логируемые действия

- `set_level` — изменение уровня доступа
- `remove_level` — сброс уровня до "user"
- `add_user` — добавление пользователя
- `remove_user` — удаление пользователя
- `view_history` — просмотр истории диалога

### Python API

```python
from backend.database.users_db import get_database

db = get_database()

# Логирование действия
db.log_admin_action(
    admin_user_id="123456789",
    admin_username="@admin",
    action_type="set_level",
    target_user_id="987654321",
    old_value="user",
    new_value="subscriber",
    success=True
)

# Получение записей
logs = db.get_admin_audit_log(admin_user_id="123456789", limit=20)

# Статистика администратора
stats = db.get_admin_stats("123456789")
```

### Миграция базы данных

```bash
# Выполнить SQL миграцию в Supabase
# Файл: supabase_admin_audit_migration.sql
```

См. полную документацию в **ADMIN_AUDIT_LOG.md**

---

## 📈 Расширение

### Добавление новой LLM модели

1. Добавить клиент в `backend/llm/` (по аналогии с `openrouter.py`)
2. Добавить настройки в `backend/config.py`
3. Добавить кнопку в `backend/utils/keyboards.py`
4. Обработать выбор в `backend/api/telegram_polling.py`

### Добавление новой команды

1. Обработать команду в `process_message()` (`telegram_polling.py`)
2. Добавить обработчик в соответствующий модуль
3. Добавить кнопку в клавиатуру (опционально)

### Интеграция нового API

1. Создать модуль в `backend/internet/` или `backend/vision/`
2. Добавить конфигурацию в `config.py`
3. Вызвать из основного обработчика

---

## 📝 Стили кода

- **Язык кода**: Python 3.8+
- **Язык комментариев**: Русский
- **Стиль**: PEP 8 с русскими комментариями
- **Логирование**: `logging` с именованными логгерами
- **Асинхронность**: `asyncio` + `aiohttp` для I/O операций

### Структура модуля

```python
"""
Описание модуля.
"""
import logging

logger = logging.getLogger("bot.module_name")

# Константы
CONSTANT = "value"

# Функции
def function_name(arg: str) -> str:
    """Docstring."""
    pass

# Классы
class ClassName:
    """Docstring."""
    pass
```

---

## 🔐 Безопасность

- `.env` файл в `.gitignore` — никогда не коммитьте ключи
- API ключи ротируются при rate limit
- CORS настраивается через `CORS_ORIGINS`
- Администратор устанавливается через `ADMIN_USER_ID`

---

## 📄 Документация проекта

В проекте есть подробные отчёты:

| Файл | Описание |
|------|----------|
| `README.md` | Общая информация |
| `LiraAI Plan.md` | План демонстрации FeedbackBot |
| `SUPABASE_SETUP.md` | Настройка Supabase |
| `LONG_TERM_MEMORY.md` | Система памяти |
| `IMAGE_GENERATION_REPORT.md` | Генерация изображений |
| `GEMINI_*.md` | Интеграция Gemini |
| `CEREBRAS_INTEGRATION.md` | Интеграция Cerebras |
| `FALLBACK_IMPLEMENTATION.md` | Fallback механизмы |
| `ADMIN_AUDIT_LOG.md` | 📋 Audit Log — журнал действий администраторов |

---

## 🎬 Сценарии использования

### 1. FeedbackBot (групповой чат)

```
Группа: "Обратная связь"
Бот автоматически:
- Обрабатывает ВСЕ сообщения (не нужно упоминать)
- Помнит контекст (20 последних сообщений)
- Определяет режим: АНАЛИЗ / КОУЧИНГ / ОБУЧЕНИЕ / Q&A
- Использует базу знаний (SBI, COIN, GROW и др.)
```

### 2. Персональный ассистент (приватный чат)

```
Пользователь:
- Общается с выбранной моделью (Groq/Cerebras/OpenRouter)
- Генерирует изображения через Z-Image
- Отправляет фото для анализа
- Распознаёт голосовые сообщения
```

### 3. Администрирование

```
Администратор:
- Управляет уровнями доступа пользователей
- Включает режим тех.работ
- Рассылает уведомления
- Смотрит статистику
- Audit Log: все действия логируются автоматически
```

**Команды администратора:**
- `/admin log` — просмотр audit log
- `/admin admin_stats` — статистика администратора
- `/admin set_level` — изменить уровень доступа
- `/admin history` — просмотр истории пользователя

---

## 🚀 Продакшен развёртывание

### PM2 конфигурация

`ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'liraai-multiassistent',
    script: 'backend/main.py',
    interpreter: '/path/to/venv/bin/python3',
    cwd: '/path/to/project',
    instances: 1,
    autorestart: true,
    max_memory_restart: '500M'
  }]
};
```

### Команды PM2

```bash
pm2 start ecosystem.config.js
pm2 restart liraai-multiassistent
pm2 stop liraai-multiassistent
pm2 logs liraai-multiassistent
pm2 monit
```

---

## 📞 Контакты

**Разработчик**: Danil Alekseevich  
**Канал**: [@liranexus](https://t.me/liranexus)

---

## ⚙️ Технические детали

### Зависимости (requirements.txt)

**Основные**:
- `fastapi`, `uvicorn` — веб-сервер
- `aiohttp`, `requests` — HTTP клиенты
- `telethon` — Telegram клиент
- `openai`, `tiktoken` — LLM интеграция
- `supabase` — база данных
- `gtts`, `SpeechRecognition`, `librosa` — голос
- `Pillow` — изображения
- `transformers`, `huggingface_hub` — ML

### Системные требования

- Python 3.8+
- ffmpeg (для обработки голоса)
- 512MB+ RAM
- 1GB+ свободного места

---

**LiraAI MultiAssistant v1.0.0** — Мультимодальная платформа для интеллектуальных ассистентов
