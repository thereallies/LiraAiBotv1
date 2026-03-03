# 📋 Audit Log — Журнал аудита действий администраторов

## 📖 Описание

Система аудита действий администраторов в LiraAI MultiAssistant боте. Все действия администраторов логируются в таблицу `admin_audit_log` в Supabase (или SQLite для локальной разработки).

---

## 🗄️ Миграция базы данных

### 1. Выполните SQL миграцию в Supabase

```sql
-- Выполните файл: supabase_admin_audit_migration.sql
-- Через SQL Editor в Supabase Dashboard
```

**Шаги:**
1. Откройте [Supabase Dashboard](https://supabase.com/dashboard)
2. Выберите ваш проект
3. Перейдите в **SQL Editor**
4. Скопируйте содержимое файла `supabase_admin_audit_migration.sql`
5. Нажмите **Run**

### 2. Проверьте создание таблицы

Убедитесь, что таблица `admin_audit_log` создана:

```sql
SELECT * FROM admin_audit_log LIMIT 10;
```

### 3. Проверьте индексы

```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'admin_audit_log';
```

---

## 📊 Структура таблицы

### Таблица: `admin_audit_log`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGSERIAL | Уникальный ID записи |
| `admin_user_id` | TEXT | ID администратора |
| `admin_username` | TEXT | Username администратора |
| `action_type` | TEXT | Тип действия |
| `target_user_id` | TEXT | ID целевого пользователя |
| `target_username` | TEXT | Username целевого пользователя |
| `old_value` | TEXT | Старое значение |
| `new_value` | TEXT | Новое значение |
| `details` | JSONB | Дополнительные детали |
| `chat_id` | TEXT | ID чата где выполнено действие |
| `message_id` | BIGINT | ID сообщения с командой |
| `created_at` | TIMESTAMPTZ | Время выполнения (MSK) |
| `success` | BOOLEAN | Успешно ли выполнено |

---

## 🔧 Типы действий (action_type)

| Действие | Описание |
|----------|----------|
| `set_level` | Изменение уровня доступа пользователя |
| `remove_level` | Сброс уровня доступа до "user" |
| `add_user` | Добавление пользователя в базу |
| `remove_user` | Удаление пользователя из базы |
| `view_history` | Просмотр истории диалога пользователя |
| `view_stats` | Просмотр статистики |
| `maintenance_mode` | Включение/выключение режима тех.работ |

---

## 🤖 Команды администратора

### Просмотр Audit Log

#### `/admin log` - Последние действия

Показывает последние 20 действий текущего администратора.

```
/admin log
```

#### `/admin log [user_id] [limit]` - Логи по пользователю

Показывает действия над указанным пользователем.

```
/admin log 1658547011 50
```

#### `/admin log --admin=[user_id]` - Логи администратора

Показывает действия указанного администратора.

```
/admin log --admin=123456789
```

#### `/admin log --target=[user_id]` - Логи по цели

Показывает действия над указанной целью.

```
/admin log --target=987654321
```

---

### Статистика администратора

#### `/admin admin_stats` - Личная статистика

Показывает статистику действий текущего администратора.

```
/admin admin_stats
```

**Вывод:**
- 🔧 Всего действий
- ✅ Успешных действий
- ❌ Ошибок
• Изменений уровня
• Добавлено пользователей
• Удалено пользователей
• Просмотров истории

---

### Просмотр истории пользователя

#### `/admin history <user_id> [limit]`

Показывает историю диалога пользователя.

```
/admin history 1658547011 50
```

**Автоматически логируется** как `view_history`.

---

### Управление пользователями

Все команды управления пользователями автоматически логируются:

#### `/admin set_level [user_id] [level]`

```
/admin set_level 123456789 subscriber
```

**Лог:**
- `action_type`: `set_level`
- `target_user_id`: `123456789`
- `old_value`: `user`
- `new_value`: `subscriber`

#### `/admin remove_level [user_id]`

```
/admin remove_level 123456789
```

**Лог:**
- `action_type`: `remove_level`
- `target_user_id`: `123456789`
- `old_value`: `subscriber`
- `new_value`: `user`

#### `/admin add_user [user_id]`

```
/admin add_user 123456789
```

**Лог:**
- `action_type`: `add_user`
- `target_user_id`: `123456789`

#### `/admin remove_user [user_id]`

```
/admin remove_user 123456789
```

**Лог:**
- `action_type`: `remove_user`
- `target_user_id`: `123456789`

---

## 📈 Примеры использования

### Пример 1: Проверка кто изменил уровень пользователя

```sql
SELECT 
    admin_username,
    action_type,
    old_value,
    new_value,
    created_at
FROM admin_audit_log
WHERE target_user_id = '123456789'
  AND action_type = 'set_level'
ORDER BY created_at DESC;
```

### Пример 2: Статистика действий администратора за неделю

```sql
SELECT 
    action_type,
    COUNT(*) as count,
    SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END) as successful
FROM admin_audit_log
WHERE admin_user_id = '123456789'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY action_type;
```

### Пример 3: Все неудачные действия

```sql
SELECT *
FROM admin_audit_log
WHERE success = FALSE
ORDER BY created_at DESC
LIMIT 20;
```

### Пример 4: Активность администраторов

```sql
SELECT 
    admin_username,
    COUNT(*) as total_actions,
    MAX(created_at) as last_action
FROM admin_audit_log
GROUP BY admin_username
ORDER BY total_actions DESC;
```

---

## 🔍 Python API (для разработчиков)

### Логирование действия

```python
from backend.database.users_db import get_database

db = get_database()

db.log_admin_action(
    admin_user_id="123456789",
    admin_username="@admin",
    action_type="set_level",
    target_user_id="987654321",
    old_value="user",
    new_value="subscriber",
    chat_id="-1001234567890",
    message_id=12345,
    success=True,
    details={"reason": "premium subscription"}
)
```

### Получение записей из audit log

```python
# Все записи
logs = db.get_admin_audit_log(limit=50)

# По администратору
logs = db.get_admin_audit_log(admin_user_id="123456789", limit=20)

# По целевому пользователю
logs = db.get_admin_audit_log(target_user_id="987654321", limit=20)

# По типу действия
logs = db.get_admin_audit_log(action_type="set_level", limit=20)
```

### Получение статистики администратора

```python
stats = db.get_admin_stats(admin_user_id="123456789")

# Возвращает:
# {
#     "total_actions": 50,
#     "successful_actions": 48,
#     "failed_actions": 2,
#     "level_changes": 20,
#     "users_added": 15,
#     "users_removed": 5,
#     "history_views": 10
# }
```

---

## 🔐 Безопасность

### RLS (Row Level Security)

По умолчанию RLS отключён. Для включения:

```sql
ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;

-- Политика: только админы могут читать логи
CREATE POLICY admin_read_audit ON admin_audit_log
    FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM users 
        WHERE users.user_id = admin_audit_log.admin_user_id 
        AND users.access_level = 'admin'
    ));
```

### Проверка прав в боте

Все команды проверяют права администратора:

```python
if not db.is_admin(user_id):
    await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
    return
```

---

## 🛠️ Локальная разработка (SQLite)

Для локальной разработки используется SQLite. Таблица создаётся автоматически при первом логировании.

### Просмотр логов в SQLite

```bash
# Подключитесь к базе
sqlite3 data/bot.db

# Просмотр записей
SELECT * FROM admin_audit_log ORDER BY created_at DESC LIMIT 20;
```

---

## 📊 Мониторинг и алерты

### SQL запрос для мониторинга подозрительной активности

```sql
-- Много удалений пользователей за час
SELECT 
    admin_username,
    COUNT(*) as removals
FROM admin_audit_log
WHERE action_type = 'remove_user'
  AND created_at >= NOW() - INTERVAL '1 hour'
GROUP BY admin_username
HAVING COUNT(*) > 5;
```

### Telegram уведомление о подозрительной активности

Добавьте в `telegram_polling.py`:

```python
# После действия администратора
if action_type == "remove_user":
    stats = db.get_admin_stats(user_id)
    if stats.get('users_removed', 0) > 10:  # Больше 10 удалений
        # Отправить уведомление супер-админу
        await send_telegram_message(
            SUPER_ADMIN_ID,
            f"⚠️ Подозрительная активность!\n\n"
            f"Админ {user_id} удалил {stats['users_removed']} пользователей за сессию."
        )
```

---

## 📝 Best Practices

1. **Всегда логируйте действия администратора**
   - Вызов `log_admin_action()` должен быть в каждой админской команде

2. **Указывайте детали в JSON**
   ```python
   details = {
       "reason": "user requested",
       "previous_complaints": 3,
       "chat_context": "spam report"
   }
   ```

3. **Проверяйте успех перед логированием**
   ```python
   success = db.set_user_access_level(target_user_id, new_level)
   db.log_admin_action(..., success=success)
   ```

4. **Используйте кэш для частых запросов**
   ```python
   # Кэшируйте результаты get_admin_audit_log
   # TTL: 1-5 минут
   ```

5. **Регулярно проверяйте audit log**
   - Раз в неделю запускайте отчёт по активности администраторов

---

## 🔧 Устранение неполадок

### Проблема: Логи не записываются

**Решение:**
1. Проверьте что таблица создана: `SELECT * FROM admin_audit_log LIMIT 1;`
2. Проверьте права доступа: `GRANT ALL ON admin_audit_log TO service_role;`
3. Проверьте логи бота на ошибки

### Проблема: Медленные запросы

**Решение:**
1. Убедитесь что индексы созданы
2. Используйте лимиты: `LIMIT 50`
3. Добавьте фильтрацию по дате

### Проблема: SQLite vs Supabase рассинхронизация

**Решение:**
1. При переключении на Supabase данные из SQLite не мигрируют автоматически
2. Для миграции используйте скрипт экспорта/импорта

---

## 📄 Файлы проекта

| Файл | Описание |
|------|----------|
| `supabase_admin_audit_migration.sql` | SQL миграция для Supabase |
| `backend/database/users_db.py` | Методы для работы с audit log |
| `backend/api/telegram_polling.py` | Команды администратора |

---

**Версия**: 1.0.0  
**Дата**: 2026-03-03  
**Статус**: ✅ Готово к использованию
