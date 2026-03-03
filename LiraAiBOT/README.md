# 🤖 LiraAI MultiAssistant

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Мультимодальная платформа для создания интеллектуальных Telegram-ботов с поддержкой текста, голоса, изображений и системой оплаты.**

---

## 🌟 Возможности

### 🤖 AI Функции
- **Текстовая обработка**: Общение через LLM (OpenRouter, Groq, Cerebras)
- **Голосовые сообщения**: STT (распознавание) и TTS (синтез речи)
- **Генерация изображений**: Multiple providers (Polza.ai, Gemini, Replicate)
- **Анализ изображений**: Vision API для описания фото

### 💳 Платежная система
- **ЮMoney интеграция**: Приём платежей 100₽
- **Уровни доступа**: `user` → `sub+` (30 генераций/день)
- **WebApp оплата**: Встроенное окно оплаты в Telegram
- **Ручное подтверждение**: Админ-команда `/admin pay_confirm`

### 📊 Администрирование
- **Audit Log**: Журнал всех действий администраторов
- **Управление пользователями**: Повышение/понижение уровней
- **Статистика**: Детальная статистика по пользователям
- **Рассылки**: Уведомления всем пользователям

### 🗄️ База данных
- **Supabase**: PostgreSQL для продакшена
- **SQLite**: Fallback для локальной разработки
- **Долговременная память**: История диалогов

---

## 🏗️ Архитектура

```
LiraAiBOT/
├── backend/
│   ├── api/
│   │   ├── telegram_polling.py      # Основной обработчик сообщений
│   │   ├── telegram_core.py         # Telegram API клиент
│   │   ├── telegram_vision.py       # Обработка изображений
│   │   ├── telegram_voice.py        # Обработка голоса
│   │   └── payment_server.py        # Платежный сервер (FastAPI)
│   ├── core/
│   │   └── feedback_bot.py          # FeedbackBot логика
│   ├── database/
│   │   └── users_db.py              # Работа с пользователями + Audit Log
│   ├── llm/
│   │   ├── openrouter.py            # OpenRouter клиент
│   │   ├── groq.py                  # Groq клиент
│   │   └── cerebras.py              # Cerebras клиент
│   ├── vision/
│   │   ├── gemini_image.py          # Gemini Vision API
│   │   └── hf_replicate.py          # HuggingFace/Replicate
│   ├── voice/
│   │   ├── tts.py                   # Text-to-Speech
│   │   └── stt.py                   # Speech-to-Text
│   ├── utils/
│   │   ├── keyboards.py             # Telegram клавиатуры
│   │   ├── mode_manager.py          # Менеджер режимов
│   │   └── group_manager.py         # Менеджер групп
│   ├── templates/
│   │   └── pay.html                 # WebApp страница оплаты
│   ├── config.py                    # Конфигурация
│   └── main.py                      # Точка входа
├── data/                            # Данные (SQLite)
├── logs/                            # Логи
├── temp/                            # Временные файлы
├── .env.example                     # Пример конфигурации
├── requirements.txt                 # Зависимости
├── ecosystem.config.js              # PM2 конфигурация
└── README.md                        # Этот файл
```

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваши ключи:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# LLM (выберите один или несколько)
OPENROUTER_API_KEY=sk-or-v1-xxx
GROQ_API_KEY=gsk_xxx
CEREBRAS_API_KEY=csk_xxx

# Генерация изображений
POLZA_API_KEY=pza_xxx
GEMINI_API_KEY=xxx

# База данных (опционально)
USE_SUPABASE=true
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# ЮMoney оплата (опционально)
YOOMONEY_WALLET=4100119485670330
BASE_URL=http://your-server:8001
```

### 3. Запуск

```bash
# Основной бот
cd backend && python main.py

# Или через PM2 (продакшен)
pm2 start ecosystem.config.js
```

---

## 💳 Уровни доступа

| Уровень | Лимит генераций | Описание |
|---------|-----------------|----------|
| `user` | 3 в день | Базовый уровень |
| `subscriber` | 5 в день | Подписчик |
| `sub+` | 30 в день | **Оплата 100₽** |
| `admin` | Безлимит | Администратор |

### Процесс оплаты

1. Пользователь исчерпывает лимит → появляется кнопка **"💳 Оплатить sub+ (100₽)"**
2. Нажимает → открывается WebApp с ссылкой на ЮMoney
3. Оплачивает 100₽ на кошелек `4100119485670330`
4. Админ получает уведомление → отправляет `/admin pay_confirm [user_id]`
5. Пользователь получает уровень `sub+` (30 генераций/день)

---

## 🎯 Telegram команды

### Пользовательские
- `/start` - Главное меню
- `/stats` - Личная статистика
- `/menu` - Показать клавиатуру
- `/hide` - Скрыть клавиатуру
- `/generate [описание]` - Генерация изображения

### Админ команды
- `/admin` - Админ панель
- `/admin users` - Список пользователей
- `/admin set_level [id] [level]` - Установить уровень
- `/admin remove_level [id]` - Снять уровень
- `/admin pay_confirm [id]` - Подтвердить оплату sub+
- `/admin history [id]` - История пользователя
- `/admin log` - Audit log
- `/admin admin_stats` - Статистика администратора
- `/admin broadcast [сообщение]` - Рассылка

---

## 📊 Audit Log

Все действия администраторов логируются в таблицу `admin_audit_log`:

```sql
CREATE TABLE admin_audit_log (
    id BIGSERIAL PRIMARY KEY,
    admin_user_id TEXT,
    action_type TEXT,           -- set_level, add_user, pay_confirm, ...
    target_user_id TEXT,
    old_value TEXT,
    new_value TEXT,
    details JSONB,
    created_at TIMESTAMPTZ
);
```

### Просмотр логов

```bash
# В Telegram
/admin log

# В Supabase
SELECT * FROM admin_audit_log ORDER BY created_at DESC LIMIT 20;
```

---

## 🔧 Настройка

### LLM модели

```python
# backend/config.py
LLM_CONFIG = {
    "model": "upstage/solar-pro-3:free",  # OpenRouter
    "fallback_model": "arcee-ai/trinity-mini:free",
    "temperature": 0.7,
    "max_tokens": 2048,
}
```

### Доступные модели

| Провайдер | Модели | Статус |
|-----------|--------|--------|
| **Groq** | Llama 3.3, Llama 4, Kimi K2 | ✅ Быстрые |
| **Cerebras** | Llama 3.1 8B | ✅ Сверхбыстрые |
| **OpenRouter** | Solar, Trinity, GLM | ✅ Бесплатные |

### Генерация изображений

| Провайдер | Модели | Статус |
|-----------|--------|--------|
| **Polza.ai** | Z-Image | ✅ Работает |
| **Gemini** | Gemini 2.5 Flash | ✅ Работает |
| **Replicate** | FLUX | ✅ Работает |

---

## 📡 API Эндпоинты

### FastAPI сервер

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/health` | GET | Проверка здоровья |
| `/api/message` | POST | Текстовое сообщение |
| `/api/image/generate` | POST | Генерация изображения |

### Payment server

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/pay` | GET | WebApp страница оплаты |
| `/payment-success` | GET | Страница успеха |
| `/health` | GET | Проверка здоровья |

---

## 🛠️ Развёртывание

### Bothost (bothost.ru)

См. инструкцию в [`BOTHOST_ENV.md`](BOTHOST_ENV.md):

```bash
# 1. Создайте .env
nano .env

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Запустите через PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Docker (опционально)

```bash
docker build -t liraai-bot .
docker run -d --env-file .env liraai-bot
```

---

## 🧪 Тестирование

```bash
# Тест генерации изображений
python test_hf_flux.py

# Тест Supabase
python test_supabase_tables.py

# Тест Audit Log
python test_audit_log.py
```

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| [`README.md`](README.md) | Основная документация |
| [`BOTHOST_ENV.md`](BOTHOST_ENV.md) | Развёртывание на Bothost |
| [`YOOMONEY_SETUP.md`](YOOMONEY_SETUP.md) | Настройка ЮMoney оплаты |
| [`ADMIN_AUDIT_LOG.md`](ADMIN_AUDIT_LOG.md) | Audit Log документация |
| [`SUB+_IMPLEMENTATION_REPORT.md`](SUB+_IMPLEMENTATION_REPORT.md) | Отчёт о реализации sub+ |
| [`QWEN.md`](QWEN.md) | Контекст для разработки |

---

## 🔐 Безопасность

- ✅ Все API ключи в `.env` (в `.gitignore`)
- ✅ HMAC-SHA256 подпись WebApp URL
- ✅ Audit Log всех действий администраторов
- ✅ Проверка прав доступа для админ команд
- ✅ RLS (Row Level Security) для Supabase

---

## 📈 Мониторинг

```bash
# Статус процессов
pm2 status

# Логи в реальном времени
pm2 logs --lines 100

# Мониторинг ресурсов
pm2 monit
```

---

## 🐛 Устранение неполадок

### Бот не отвечает
```bash
# Проверьте токен
cat .env | grep TELEGRAM_BOT_TOKEN

# Перезапустите
pm2 restart liraai-bot

# Проверьте логи
pm2 logs liraai-bot --err
```

### Ошибки генерации
```bash
# Проверьте API ключи
cat .env | grep API_KEY

# Проверьте лимиты
/admin stats
```

### Проблемы с оплатой
```bash
# Проверьте payment server
pm2 logs liraai-payment

# Проверьте BASE_URL
cat .env | grep BASE_URL
```

---

## 🤝 Вклад

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

---

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

---

## 📞 Контакты

**Разработчик**: Danil Alekseevich  
**Telegram**: [@liranexus](https://t.me/liranexus)  
**Bothost**: [bothost.ru](https://bothost.ru)

---

## 🎯 Планы развития

- [ ] Рекуррентные платежи (ежемесячная подписка)
- [ ] Несколько тарифов (sub+, pro, premium)
- [ ] Промокоды и скидки
- [ ] Реферальная программа
- [ ] Другие платёжные системы (CloudPayments, Robokassa)

---

**LiraAI MultiAssistant v2.0** — Мультимодальная платформа с системой оплаты

[![Bothost](https://img.shields.io/badge/Powered%20by-Bothost-blue)](https://bothost.ru)
[![Supabase](https://img.shields.io/badge/Database-Supabase-green)](https://supabase.com)
