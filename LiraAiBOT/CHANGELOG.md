# 📝 История изменений (Changelog)

Все заметные изменения в проекте будут задокументированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
версии следуют [Semantic Versioning](https://semver.org/lang/ru/).

---

## [2.0.0] - 2026-03-03

### ✨ Добавлено

- **Платежная система ЮMoney**
  - Приём платежей 100₽ через WebApp
  - Автоматическое создание платежей в базе данных
  - Ручное подтверждение через `/admin pay_confirm`
  - Уведомления пользователей об успешной оплате

- **Уровень доступа `sub+`**
  - Лимит 30 генераций изображений в день
  - Оплата 100₽ для получения уровня
  - Автоматическое обновление лимитов

- **Audit Log**
  - Таблица `admin_audit_log` в Supabase
  - Логирование всех действий администраторов
  - Команда `/admin log` для просмотра
  - Статистика администратора `/admin admin_stats`

- **Новые админ команды**
  - `/admin pay_confirm [user_id]` - Подтверждение оплаты
  - `/admin admin_stats` - Статистика администратора
  - `/admin log [user_id]` - Просмотр логов

- **Методы базы данных**
  - `log_admin_action()` - Логирование действий
  - `get_admin_audit_log()` - Получение записей
  - `get_admin_stats()` - Статистика администратора
  - `create_payment()` - Создание платежа
  - `get_payment()` - Получение платежа
  - `update_payment_status()` - Обновление статуса

### 🔧 Изменено

- **Обновлено отображение уровней**
  - `sub+` → "🚀 sub+ (30/день)"
  - `subscriber` → "⭐ Подписчик (5/день)"
  - `user` → "👤 Пользователь (3 в день)"

- **Улучшена обработка timezone**
  - Конвертация UTC в Moscow time
  - Исправление ошибок `offset-naive`

- **Обновлена документация**
  - Новый `README.md` с полной информацией
  - `BOTHOST_ENV.md` для развёртывания на Bothost
  - `YOOMONEY_SETUP.md` для настройки платежей
  - `ADMIN_AUDIT_LOG.md` для Audit Log

### 🐛 Исправлено

- **Ошибки timezone в `check_generation_limit`**
  - Конвертация `last_reset` из Supabase
  - Исправление `can't subtract offset-naive and offset-aware datetimes`

- **Кэширование статистики**
  - Отключено кэширование для актуальных данных
  - Принудительное обновление из БД

- **Отображение уровня `sub+`**
  - Добавлено во все `level_info` словари
  - Обновлены `telegram_polling.py` и `callback_handler.py`

### 🗄️ База данных

- **Новые таблицы**
  - `payments` - Платежи пользователей
  - `admin_audit_log` - Журнал действий администраторов

- **Миграции**
  - `supabase_payments_migration.sql` - Создание таблицы платежей
  - `supabase_admin_audit_migration.sql` - Создание таблицы аудита

### 📁 Новые файлы

- `backend/payment_server.py` - Платежный сервер (FastAPI)
- `backend/templates/pay.html` - WebApp страница оплаты
- `BOTHOST_ENV.md` - Инструкция для Bothost
- `YOOMONEY_SETUP.md` - Настройка ЮMoney
- `ADMIN_AUDIT_LOG.md` - Audit Log документация
- `SUB+_IMPLEMENTATION_REPORT.md` - Отчёт о реализации
- `CONTRIBUTING.md` - Руководство для контрибьюторов
- `CHANGELOG.md` - История изменений

### ⚙️ Конфигурация

- **Новые переменные окружения**
  ```bash
  YOOMONEY_WALLET=4100119485670330
  YOOMONEY_SECRET=xxx
  BASE_URL=http://your-server:8001
  ```

- **Обновлён `.env.example`**
  - Добавлены переменные для ЮMoney
  - Добавлены переменные для Supabase

---

## [1.5.0] - 2026-02-15

### ✨ Добавлено

- **FeedbackBot**
  - Эксперт по обратной связи для групповых чатов
  - Контекстная память (20 последних сообщений)
  - Режимы: АНАЛИЗ, КОУЧИНГ, ОБУЧЕНИЕ, Q&A

- **Модели обратной связи**
  - SBI (Situation-Behavior-Impact)
  - COIN (Context-Observation-Impact-Next)
  - STAR (Situation-Task-Action-Result)
  - DESC (Describe-Express-Specify-Consequences)
  - GROW (Goal-Reality-Options-Will)

### 🔧 Изменено

- **Улучшена обработка групповых чатов**
  - Автоматическое сохранение ID групп
  - Обработка всех сообщений без упоминания

---

## [1.4.0] - 2026-02-01

### ✨ Добавлено

- **Генерация изображений**
  - Polza.ai (Z-Image)
  - Gemini Image API
  - HuggingFace/Replicate (FLUX)

- **Выбор модели генерации**
  - Inline-клавиатура с моделями
  - Разные модели для разных уровней доступа

### 🔧 Изменено

- **Лимиты генераций**
  - `user`: 3 генерации/день
  - `subscriber`: 5 генераций/день
  - `admin`: безлимит

---

## [1.3.0] - 2026-01-15

### ✨ Добавлено

- **Supabase интеграция**
  - Таблица `users` с уровнями доступа
  - Таблица `generation_limits` с лимитами
  - Таблица `generation_history` с историей
  - Таблица `dialog_history` с диалогами

- **Долговременная память**
  - Сохранение истории диалогов
  - Контекст для LLM

### 🔧 Изменено

- **SQLite fallback**
  - Автоматическое переключение при недоступности Supabase

---

## [1.2.0] - 2026-01-01

### ✨ Добавлено

- **Голосовые функции**
  - STT (Speech-to-Text) через SpeechRecognition
  - TTS (Text-to-Speech) через gTTS

- **Множественные боты**
  - Поддержка нескольких Telegram токенов
  - Ротация токенов

### 🔧 Изменено

- **Улучшена обработка ошибок**
  - Retry logic для API запросов
  - Graceful degradation

---

## [1.1.0] - 2025-12-15

### ✨ Добавлено

- **LLM интеграции**
  - OpenRouter (Solar, Trinity, GLM)
  - Groq (Llama 3.3, Llama 4, Kimi K2)
  - Cerebras (сверхбыстрые модели)

- **Режимы работы**
  - Auto, Text, Voice, Photo, Generation
  - Reply-клавиатура для выбора

### 🔧 Изменено

- **Оптимизация запросов**
  - Кэширование ответов
  - Batch requests

---

## [1.0.0] - 2025-12-01

### ✨ Добавлено

- **Первый релиз**
  - Базовая функциональность Telegram бота
  - Текстовая обработка через LLM
  - Анализ изображений
  - FastAPI сервер

---

## 📝 Версии

- **MAJOR** (2.0.0) - Breaking changes
- **MINOR** (1.5.0) - Новые функции (обратная совместимость)
- **PATCH** (1.5.1) - Исправления ошибок

---

## 🔗 Ссылки

- [GitHub Releases](https://github.com/your-repo/LiraAiBOT/releases)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

---

**LiraAI MultiAssistant Development Team**
