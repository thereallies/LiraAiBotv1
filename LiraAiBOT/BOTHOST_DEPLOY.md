# 🚀 Деплой LiraAI Web на bothost.ru

**Полная инструкция по развёртыванию веб-интерфейса LiraAI на bothost.ru**

---

## 📋 Быстрый старт

### 1. Настройки в панели bothost.ru

Перейдите в панель управления ботом на bothost.ru и настройте:

| Поле | Значение | Примечание |
|------|----------|------------|
| **Веб-приложение** | ✅ **Включено** | Обязательно для webhook и web-интерфейса |
| **Порт веб-приложения** | `8001` | Порт из `backend/config.py` |
| **Кастомный домен** | `liraai.bothost.ru` | Или оставьте пустым для авто-домена |
| **Главный файл** | `index.py` | **Важно:** Точка входа для bothost |

⚠️ **Почему `index.py`?** Bothost.ru ищет файл в корне проекта (`/app/index.py`). Файл `index.py` импортирует приложение из `backend/main.py`.

### 2. Структура проекта

```
LiraAiBOT/
├── index.py          ← Точка входа для bothost.ru ✅
├── run.py            ← Для локальной разработки
├── backend/
│   └── main.py       ← Основное приложение FastAPI
├── .env              ← Переменные окружения
└── requirements.txt  ← Зависимости
```

---

## 🔐 2. Переменные окружения

Добавьте в разделе **Environment Variables** следующие переменные:

### Обязательные

```bash
# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# === ADMIN ===
ADMIN_USER_ID=1658547011

# === TEXT MODELS ===
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === IMAGE GENERATION ===
POLZA_API_KEY=pza_xxxxxxxxxxxxxxxxxxxxxxxxxx

# === DATABASE ===
USE_SUPABASE=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# === APP SETTINGS ===
DEV_MODE=false
DEBUG=false
CORS_ORIGINS=*
```

### Опциональные (для платежей)

```bash
# === YOOMONEY ===
YOOMONEY_WALLET=4100119485670330
YOOMONEY_SECRET=6CA85A92063C69296718B0B72E654352C8677A1E...
BASE_URL=https://liraai.bothost.ru
```

### Опциональные (дополнительные модели)

```bash
# === Gemini ===
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX

# === Replicate ===
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === ElevenLabs (голос) ===
ELEVEN_API_KEY=xi_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ELEVEN_VOICE_ID=XXXXXXXXXXXXXXXXXXXX
```

---

## 📦 3. Требования

Проект уже содержит обновлённый `requirements.txt` с необходимыми пакетами:

- `fastapi>=0.110`
- `uvicorn[standard]>=0.20.0`
- `jinja2` (для веб-шаблонов)
- `groq>=0.9.0`
- `replicate>=0.25.0`
- `python-multipart` (для загрузки файлов)
- `supabase>=2.0.0`

---

## 🌐 4. Доступ к веб-интерфейсу

После деплоя веб-интерфейс будет доступен по адресу:

```
https://liraai.bothost.ru/web
```

### Основные endpoints:

| URL | Описание |
|-----|----------|
| `/web` | Лендинг страница |
| `/web/app` | Рабочая зона пользователя |
| `/web/admin` | Админ-панель (только для admin) |
| `/api/web/*` | API endpoints |
| `/web-static/*` | Статические файлы (CSS, JS, изображения) |

---

## 🔧 5. Проверка работы

### 1. Проверка health endpoint

```bash
curl https://liraai.bothost.ru/health
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Проверка веб-интерфейса

Откройте в браузере:
```
https://liraai.bothost.ru/web
```

### 3. Проверка API

```bash
curl https://liraai.bothost.ru/api
```

---

## 🛠️ 6. Решение проблем

### Ошибка: "Port already in use"

**Проблема:** Порт 8001 уже занят.

**Решение:** Измените порт в `backend/config.py`:
```python
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8002,  # Измените на другой
    "debug": True,
}
```

И обновите порт в настройках bothost.ru.

### Ошибка: "ModuleNotFoundError: No module named 'groq'"

**Проблема:** Не установлен пакет groq.

**Решение:** Убедитесь, что `requirements.txt` содержит:
```
groq>=0.9.0
```

### Ошибка: "Telegram auth verification failed"

**Проблема:** Неверный `TELEGRAM_BOT_TOKEN`.

**Решение:** Проверьте токен в @BotFather.

### Ошибка: "User not found"

**Проблема:** Пользователь не существует в базе.

**Решение:** Убедитесь, что `ADMIN_USER_ID` установлен правильно.

---

## 📊 7. Мониторинг

### Логи в bothost.ru

1. Откройте панель bothost.ru
2. Перейдите в раздел **Logs**
3. Фильтруйте по уровню: `INFO`, `WARNING`, `ERROR`

### Ключевые сообщения в логах

```
✅ База данных инициализирована
✅ Администратор установлен: 1658547011
📱 Запуск Telegram polling...
✅ Telegram polling запущен
🎉 Бот полностью инициализирован и готов к работе!
```

---

## 🔒 8. Безопасность

### Обновления безопасности (применены)

✅ **IDOR protection** — проверка принадлежности сессии пользователю  
✅ **Rate limiting** — 5 попыток аутентификации в минуту  
✅ **HTTP-only cookies** — защита от XSS  
✅ **Session expiration** — 7 дней  

### Рекомендации

1. **Не коммитьте `.env`** в Git
2. **Используйте HTTPS** — bothost.ru предоставляет автоматически
3. **Обновляйте API ключи** каждые 3-6 месяцев
4. **Мониторьте логи** на предмет подозрительной активности

---

## 📝 9. Чек-лист перед деплоем

- [ ] `TELEGRAM_BOT_TOKEN` установлен
- [ ] `ADMIN_USER_ID` установлен
- [ ] `OPENROUTER_API_KEY` установлен
- [ ] `GROQ_API_KEY` установлен
- [ ] `POLZA_API_KEY` установлен
- [ ] `SUPABASE_URL` и `SUPABASE_KEY` установлены
- [ ] `USE_SUPABASE=true`
- [ ] Порт `8001` указан в настройках bothost.ru
- [ ] Главный файл `run.py` указан
- [ ] Веб-приложение включено

---

## 🎯 10. Тестирование для тестировщиков

### Вход через Telegram

1. Откройте `https://liraai.bothost.ru/web`
2. Нажмите кнопку **"Войти через Telegram"**
3. Подтвердите вход в Telegram
4. Переход в рабочую зону автоматически

### Dev-режим (локальное тестирование)

Для тестирования без Telegram:

1. Добавьте переменную: `DEV_MODE=true`
2. На лендинге появится форма "Локальная разработка"
3. Введите `ADMIN_USER_ID` и нажмите "Войти локально"

⚠️ **Важно:** Не используйте `DEV_MODE=true` в продакшене!

---

## 📞 Поддержка

При проблемах:

1. Проверьте логи в панели bothost.ru
2. Убедитесь, что все переменные окружения установлены
3. Проверьте доступность API ключей
4. Убедитесь, что порт 8001 свободен

---

**Версия инструкции**: 1.0.0  
**Дата**: 2026-03-08  
**Статус**: ✅ Готово к деплою
