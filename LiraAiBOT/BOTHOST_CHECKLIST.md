# 🚀 Чек-лист для деплоя на bothost.ru

## ✅ Файлы

- [ ] `index.py` — точка входа (создан ✅)
- [ ] `backend/main.py` — основное приложение
- [ ] `requirements.txt` — зависимости (обновлён ✅)
- [ ] `Dockerfile` — инструкция сборки (создан ✅)
- [ ] `.dockerignore` — исключение для Docker (создан ✅)
- [ ] `.env` — переменные окружения (загрузить в панель bothost.ru)

## ⚙️ Настройки в панели bothost.ru

| Поле | Значение |
|------|----------|
| Веб-приложение | ✅ Включено |
| Порт веб-приложения | `8001` |
| Кастомный домен | `liraai.bothost.ru` (или пусто) |
| Главный файл | `index.py` |

## 🐳 Dockerfile

Проект содержит `Dockerfile` для bothost.ru:
- Использует Python 3.11
- Устанавливает ffmpeg для обработки голоса
- Запускает через `index.py`
- Создаёт директории `/app/data`, `/app/logs`, `/app/temp`

**Если bothost.ru использует свой Dockerfile**, убедитесь что CMD указывает на `index.py`:
```dockerfile
CMD ["python", "index.py"]
```

## 🔐 Переменные окружения (загрузить в панель)

### Обязательные:
```bash
TELEGRAM_BOT_TOKEN=ваш_токен
ADMIN_USER_ID=ваш_id
OPENROUTER_API_KEY=sk-or-v1-xxx
GROQ_API_KEY=gsk_xxx
CEREBRAS_API_KEY=csk_xxx
POLZA_API_KEY=pza_xxx
USE_SUPABASE=true
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=ваш_ключ
DEV_MODE=false
CORS_ORIGINS=*
```

## 🧪 Проверка после деплоя

1. Откройте `https://liraai.bothost.ru/health`
   - Ожидается: `{"status": "healthy", "version": "1.0.0"}`

2. Откройте `https://liraai.bothost.ru/web`
   - Ожидается: лендинг страница

3. Войдите через Telegram или Dev-режим

4. Проверьте `/web/app` и `/web/admin`

## 🐛 Если что-то пошло не так

### Ошибка: "can't open file '/app/index.py'"
**Решение:** Убедитесь, что главный файл указан как `index.py`

### Ошибка: "ModuleNotFoundError: No module named 'backend'"
**Решение:** Проверьте, что `index.py` в корне проекта

### Ошибка: "Port already in use"
**Решение:** Убедитесь, что порт указан как `8001`

### Ошибка: "No module named 'groq'"
**Решение:** Проверьте, что `requirements.txt` содержит `groq>=0.9.0`

---

**Создано:** 2026-03-08
**Версия:** 1.0
