# ⚡ Быстрая настройка Audit Log

## 1️⃣ Выполните SQL миграцию в Supabase

1. Откройте [Supabase Dashboard](https://supabase.com/dashboard)
2. Выберите ваш проект
3. Перейдите в **SQL Editor**
4. Скопируйте и выполните содержимое файла `supabase_admin_audit_migration.sql`

```sql
-- Скопируйте весь файл supabase_admin_audit_migration.sql
-- и выполните в SQL Editor
```

## 2️⃣ Проверьте создание таблицы

```sql
-- Должна вернуться пустая таблица
SELECT * FROM admin_audit_log LIMIT 5;
```

## 3️⃣ Запустите бота

```bash
cd /Users/iluyshin.d/Desktop/LiraAiBOT
python backend/main.py
```

## 4️⃣ Протестируйте функциональность

### Запустите тестовый скрипт

```bash
python test_audit_log.py
```

**Ожидаемый результат:**
```
🧪 Тестирование Audit Log функциональности
1️⃣ Тест: Логирование действия set_level
   Результат: ✅ Успешно
2️⃣ Тест: Логирование действия add_user
   Результат: ✅ Успешно
...
✅ Тестирование завершено!
```

### Или протестируйте в Telegram

1. Откройте бота в Telegram
2. Отправьте команду `/admin` (должны быть права администратора)
3. Попробуйте команды:

```
/admin log              # Последние действия
/admin admin_stats      # Ваша статистика
/admin set_level 123456789 subscriber  # Изменение уровня (логируется)
/admin history 123456789  # Просмотр истории (логируется)
```

## 5️⃣ Проверьте логи в Supabase

```sql
-- Последние 10 записей
SELECT 
    action_type,
    admin_username,
    target_user_id,
    old_value,
    new_value,
    created_at
FROM admin_audit_log
ORDER BY created_at DESC
LIMIT 10;
```

## 📋 Что логируется автоматически

| Действие | Команда | Тип в логе |
|----------|---------|------------|
| Изменение уровня | `/admin set_level` | `set_level` |
| Сброс уровня | `/admin remove_level` | `remove_level` |
| Добавление пользователя | `/admin add_user` | `add_user` |
| Удаление пользователя | `/admin remove_user` | `remove_user` |
| Просмотр истории | `/admin history` | `view_history` |

## 🎯 Примеры использования

### Просмотреть все действия администратора

```
/admin log --admin=123456789
```

### Просмотреть действия над пользователем

```
/admin log 987654321 50
```

### Проверить статистику администратора

```
/admin admin_stats
```

## 🔧 Устранение неполадок

### Логи не записываются

1. Проверьте что таблица создана:
   ```sql
   SELECT COUNT(*) FROM admin_audit_log;
   ```

2. Проверьте права доступа:
   ```sql
   GRANT ALL ON admin_audit_log TO service_role;
   ```

3. Проверьте логи бота на ошибки

### Ошибка "table does not exist"

Выполните SQL миграцию из шага 1.

### Бот работает но логи не пишутся

Проверьте что используете Supabase (не SQLite):
```python
from backend.database.users_db import USE_SUPABASE
print(f"Using Supabase: {USE_SUPABASE}")
```

## 📚 Документация

Полная документация: **ADMIN_AUDIT_LOG.md**

---

**Готово!** 🎉 Audit Log полностью настроен и работает.
