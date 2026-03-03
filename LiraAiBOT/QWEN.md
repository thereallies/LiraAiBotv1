# 🤖 LiraAI MultiAssistant — QWEN.md

**Контекст для разработки и взаимодействия с проектом**

---

## 📋 Обзор проекта

**LiraAI MultiAssistant** — мультимодальная платформа для создания интеллектуальных Telegram-ботов с поддержкой:

- 💬 **Текстовая обработка**: LLM через OpenRouter, Groq, Cerebras
- 🎤 **Голосовые сообщения**: STT/TTS (распознавание и синтез)
- 🎨 **Генерация изображений**: Polza.ai, Gemini, Replicate
- 📸 **Анализ изображений**: Vision API
- 💳 **Платежная система**: ЮMoney интеграция (100₽ → sub+)
- 📊 **Audit Log**: Журнал действий администраторов
- 🗄️ **База данных**: Supabase (PostgreSQL) + SQLite fallback

**Основное применение**: Эксперт по обратной связи (FeedbackBot) для групповых чатов.

---

## 🏗️ Архитектура

```
LiraAiBOT/
├── backend/
│   ├── api/
│   │   ├── telegram_polling.py      # Основной обработчик (2900 строк)
│   │   ├── telegram_core.py         # Telegram API клиент
│   │   ├── telegram_vision.py       # Обработка изображений
│   │   ├── telegram_voice.py        # Обработка голоса
│   │   └── payment_server.py        # Платежный сервер (FastAPI)
│   ├── core/
│   │   └── feedback_bot.py          # FeedbackBot логика
│   ├── database/
│   │   └── users_db.py              # Users + Audit Log + Payments (1870 строк)
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
│   ├── config.py                    # Конфигурация (255 строк)
│   └── main.py                      # Точка входа (FastAPI)
├── data/                            # SQLite база данных
├── logs/                            # Логи бота
├── temp/                            # Временные файлы
├── .github/                         # GitHub шаблоны
├── docs/                            # Документация
└── .env                             # Переменные окружения
```

---

## 🚀 Быстрый старт

### Установка зависимостей

```bash
cd /Users/iluyshin.d/Desktop/LiraAiBOT
pip install -r requirements.txt
```

### Настройка окружения

```bash
cp .env.example .env
# Отредактируйте .env с вашими ключами
```

**Ключевые переменные**:
```bash
TELEGRAM_BOT_TOKEN=your_token
OPENROUTER_API_KEY=sk-or-v1-xxx
GROQ_API_KEY=gsk_xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
YOOMONEY_WALLET=4100119485670330
BASE_URL=http://your-server:8001
```

### Запуск

```bash
# Локальная разработка
cd backend && python main.py

# Продакшен (PM2)
pm2 start ecosystem.config.js
pm2 save
```

---

## 💳 Уровни доступа

| Уровень | Лимит | Описание |
|---------|-------|----------|
| `user` | 3/день | Базовый |
| `subscriber` | 5/день | Подписчик |
| `sub+` | 30/день | **Оплата 100₽** |
| `admin` | Безлимит | Администратор |

### Процесс оплаты

1. Пользователь исчерпывает лимит → кнопка "💳 Оплатить sub+ (100₽)"
2. WebApp → ссылка на ЮMoney (`https://yoomoney.ru/to/4100119485670330`)
3. Оплата 100₽
4. Админ: `/admin pay_confirm [user_id]`
5. Пользователь получает `sub+` (30 генераций/день)

---

## 🎯 Telegram команды

### Пользовательские
- `/start` — Главное меню
- `/stats` — Личная статистика
- `/menu` — Показать клавиатуру
- `/generate [описание]` — Генерация изображения

### Админ команды
- `/admin` — Админ панель
- `/admin users` — Список пользователей
- `/admin set_level [id] [level]` — Установить уровень
- `/admin remove_level [id]` — Снять уровень
- `/admin pay_confirm [id]` — **Подтвердить оплату sub+**
- `/admin history [id]` — История пользователя
- `/admin log` — Audit log
- `/admin admin_stats` — Статистика администратора
- `/admin broadcast [сообщение]` — Рассылка

---

## 🗄️ База данных

### Таблицы Supabase

| Таблица | Назначение |
|---------|------------|
| `users` | Пользователи (user_id, access_level, username) |
| `generation_limits` | Лимиты (daily_count, total_count) |
| `generation_history` | История генераций |
| `dialog_history` | История диалогов |
| `payments` | **Платежи** (payment_id, user_id, status) |
| `admin_audit_log` | **Audit Log** (action_type, admin_user_id, details) |
| `bot_settings` | Настройки бота |
| `user_settings` | Настройки пользователей |

### Ключевые методы (users_db.py)

```python
db = get_database()

# Пользователи
db.add_or_update_user(user_id, username, first_name)
db.get_user_access_level(user_id)  # → 'user', 'sub+', 'admin'
db.set_user_access_level(user_id, 'sub+')

# Лимиты
db.check_generation_limit(user_id)  # → {allowed, daily_count, daily_limit}
db.increment_generation_count(user_id, prompt)

# Audit Log
db.log_admin_action(admin_user_id, action_type, target_user_id, ...)
db.get_admin_audit_log(limit=20)
db.get_admin_stats(admin_user_id)

# Payments
db.create_payment(payment_id, user_id, chat_id, amount)
db.get_payment(payment_id)
db.update_payment_status(payment_id, 'success')
```

---

## 🔧 Конфигурация

### backend/config.py

**LLM настройки**:
```python
LLM_CONFIG = {
    "model": "upstage/solar-pro-3:free",
    "fallback_model": "arcee-ai/trinity-mini:free",
    "temperature": 0.7,
    "max_tokens": 2048,
}
```

**Доступные модели**:
| Провайдер | Модели | Статус |
|-----------|--------|--------|
| **Groq** | Llama 3.3, Llama 4, Kimi K2 | ✅ Быстрые |
| **Cerebras** | Llama 3.1 8B | ✅ Сверхбыстрые |
| **OpenRouter** | Solar, Trinity, GLM | ✅ Бесплатные |

---

## 📝 Стандарты разработки

### Стиль кода

- **Python**: PEP 8
- **Имена**: `snake_case` (переменные), `PascalCase` (классы)
- **Комментарии**: Русские
- **Docstrings**: Обязательно для публичных функций

### Пример

```python
"""
Модуль для обработки платежей через ЮMoney.
"""
import logging
from typing import Optional

logger = logging.getLogger("bot.payment")


class PaymentProcessor:
    """Обработчик платежей."""
    
    def process_payment(self, user_id: str, amount: int) -> bool:
        """
        Обрабатывает платёж пользователя.
        
        Args:
            user_id: ID пользователя в Telegram
            amount: Сумма платежа в рублях
            
        Returns:
            True если платёж успешен
        """
        logger.info(f"💳 Обработка платежа: user_id={user_id}, amount={amount}")
        return True
```

### Логирование

```python
logger = logging.getLogger("bot.module_name")

logger.debug("Отладочная информация")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.critical("Критическая ошибка")
```

---

## 🧪 Тестирование

```bash
# Тест Audit Log
python test_audit_log.py

# Тест генерации изображений
python test_hf_flux.py

# Тест Supabase
python test_supabase_tables.py
```

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| [`README.md`](README.md) | ⭐ Главная документация |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Руководство для контрибьюторов |
| [`CHANGELOG.md`](CHANGELOG.md) | История изменений (v1.0.0 - v2.0.0) |
| [`SECURITY.md`](SECURITY.md) | Политика безопасности |
| [`BOTHOST_ENV.md`](BOTHOST_ENV.md) | Развёртывание на Bothost |
| [`YOOMONEY_SETUP.md`](YOOMONEY_SETUP.md) | Настройка ЮMoney |
| [`ADMIN_AUDIT_LOG.md`](ADMIN_AUDIT_LOG.md) | Audit Log документация |
| [`GITHUB_SETUP.md`](GITHUB_SETUP.md) | Публикация на GitHub |

---

## 🔐 Безопасность

- ✅ `.env` в `.gitignore`
- ✅ HMAC-SHA256 подпись WebApp URL
- ✅ Audit Log всех действий администраторов
- ✅ Проверка прав для админ команд
- ✅ RLS (Row Level Security) для Supabase

---

## 🛠️ Развёртывание

### Bothost (bothost.ru)

```bash
# 1. Установка
pip install -r requirements.txt

# 2. Настройка .env
nano .env

# 3. Запуск через PM2
pm2 start ecosystem.config.js --name liraai-bot
pm2 save
pm2 startup
```

### Мониторинг

```bash
pm2 status
pm2 logs liraai-bot --lines 100
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

### Ошибки timezone
- Конвертация UTC → Moscow time
- `get_moscow_now()` возвращает datetime с timezone
- При сравнении используйте `.replace(tzinfo=None)`

### Проблемы с оплатой
```bash
# Проверьте payment server
pm2 logs liraai-payment

# Проверьте BASE_URL
cat .env | grep BASE_URL
```

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
- [ ] Другие платёжные системы

---

**LiraAI MultiAssistant v2.0** — Мультимодальная платформа с системой оплаты

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
