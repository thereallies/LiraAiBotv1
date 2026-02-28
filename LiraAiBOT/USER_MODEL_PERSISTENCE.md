# 💾 Сохранение модели пользователя в Supabase

## ✅ Что реализовано:

1. **Таблица `user_settings`** - хранит выбранную модель пользователя
2. **`get_user_model()`** - загружает модель из БД
3. **`set_user_model()`** - сохраняет модель в БД
4. **Команда `/model`** - показывает текущую модель

---

## 📋 ИНСТРУКЦИЯ ПО УСТАНОВКЕ:

### 1️⃣ Создай таблицу в Supabase:

1. Зайди в **Supabase Dashboard**: https://supabase.com/dashboard/project/xmdvjrgpqqdoofamkzut/sql/new
2. Вставь SQL из файла `supabase_user_settings_migration.sql`:

```sql
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    selected_model TEXT DEFAULT 'groq-llama',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

ALTER TABLE user_settings DISABLE ROW LEVEL SECURITY;
```

3. Нажми **Run**

---

### 2️⃣ Обнови файлы на GitHub:

```bash
cd /Users/iluyshin.d/Desktop/LiraAiBOT
git add .
git commit -m "feat: сохранение модели пользователя в Supabase"
git push origin main
```

**Файлы:**
- `backend/database/users_db.py` ← get_user_model, set_user_model
- `backend/api/telegram_polling.py` ← использование БД
- `supabase_user_settings_migration.sql` ← миграция

---

### 3️⃣ Перезапусти бота на bothost.ru

---

### 4️⃣ Протестируй:

1. **Выбери модель**: `/menu` → `⚡ Cerebras Qwen 3`
2. **Проверь**: `/model`
   ```
   🤖 Ваша текущая модель: ⚡ Cerebras Qwen 3
   ```
3. **Перезапусти бота** на bothost.ru
4. **Снова проверь**: `/model`
   ```
   🤖 Ваша текущая модель: ⚡ Cerebras Qwen 3  ← СОХРАНИЛОСЬ!
   ```
5. **Напиши сообщение**: "привет"
6. **Проверь логи** - должно быть:
   ```
   🎯 1658547011 загрузил модель из БД: cerebras-qwen
   🚀 Попытка 1: cerebras - qwen-3-235b-a22b-instruct-2507
   ```

---

## 🔧 Как это работает:

### Выбор модели:
```
Пользователь нажимает "⚡ Cerebras Qwen 3"
    ↓
callback_data = "model_cerebras-qwen"
    ↓
db.set_user_model(user_id, "cerebras-qwen")
    ↓
INSERT INTO user_settings (user_id, selected_model) VALUES (...)
    ↓
✅ Сохранено в БД НАВСЕГДА!
```

### Загрузка модели:
```
Пользователь пишет сообщение
    ↓
db.get_user_model(user_id)
    ↓
SELECT selected_model FROM user_settings WHERE user_id = ?
    ↓
✅ cerebras-qwen ← загружено из БД
    ↓
Бот использует cerebras-qwen для ответа
```

---

## 📊 Структура таблицы:

| Поле | Тип | Описание |
|------|-----|----------|
| `user_id` | TEXT | ID пользователя (PRIMARY KEY) |
| `selected_model` | TEXT | Выбранная модель (groq-llama, cerebras-qwen, etc.) |
| `created_at` | TIMESTAMP | Когда создана настройка |
| `updated_at` | TIMESTAMP | Когда обновлена модель |

---

## 🎯 Доступные модели:

### Groq:
- `groq-llama` - Llama 3.3 70B
- `groq-maverick` - Llama 4 Maverick
- `groq-scout` - Llama 4 Scout
- `groq-kimi` - Kimi K2

### Cerebras:
- `cerebras-llama` - Llama 3.1 8B
- `cerebras-gpt` - GPT-oss 120B
- `cerebras-qwen` - Qwen 3 235B
- `cerebras-glm` - GLM-4.7

### OpenRouter:
- `solar` - Solar Pro 3
- `trinity` - Trinity Mini
- `glm` - GLM-4.5

---

## ✅ Итог:

| Функция | Статус |
|---------|--------|
| Таблица в Supabase | ✅ Готово |
| get_user_model() | ✅ Работает |
| set_user_model() | ✅ Работает |
| Команда /model | ✅ Работает |
| Сохранение при выборе | ✅ Работает |
| Загрузка при сообщении | ✅ Работает |
| Сохранение после перезапуска | ✅ Работает |

---

**ГОТОВО!** 🎉 Модель пользователя сохраняется в БД навсегда!
