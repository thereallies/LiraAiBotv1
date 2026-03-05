# 🧠 Cerebras GPT-oss 120B Added

**Дата:** 2026-03-05 21:31  
**Статус:** ✅ Завершено

---

## ✅ ДОБАВЛЕНА НОВАЯ МОДЕЛЬ

### Cerebras GPT-oss 120B

**Характеристики:**
- **Размер:** 120 миллиардов параметров
- **Скорость:** ~400 токенов/секунду
- **Контекст:** 128K токенов
- **Качество:** ⭐⭐⭐
- **Статус:** ✅ **БЕСПЛАТНО РАБОТАЕТ**

---

## 📁 ОБНОВЛЁННЫЕ ФАЙЛЫ

### 1. backend/utils/keyboards.py

**Добавлена кнопка:**
```python
{"text": "🧠 Cerebras GPT-oss 120B"}
```

**Обновлена функция `get_model_from_button`:**
```python
"🧠 Cerebras GPT-oss 120B": "cerebras-gpt",
```

### 2. backend/api/telegram_polling.py

**Обновлен обработчик:**
```python
if text in ["🚀 Groq Llama 3.3", "🦙 Groq Llama 4", "🔍 Groq Scout", "🌙 Groq Kimi K2",
           "⚡ Cerebras Llama 3.1", "🧠 Cerebras GPT-oss 120B"]:
```

**Добавлено название модели:**
```python
"cerebras-gpt": "🧠 GPT-oss 120B (Cerebras)"
```

**Обновлён текст сообщения:**
```
🚀 Llama 3.3 - лучшая для русского
🦙 Llama 4 - новейшая от Meta
🔍 Scout - легкая и быстрая
🌙 Kimi K2 - от Moonshot AI
⚡ Cerebras Llama 3.1 - сверхбыстрая
🧠 GPT-oss 120B - большая модель
```

### 3. backend/llm/cerebras.py

**Добавлена модель:**
```python
self.available_models = {
    "cerebras-llama": "llama3.1-8b",
    "cerebras-gpt": "gpt-oss-120b",
}
```

---

## 🎹 ОБНОВЛЁННАЯ КЛАВИАТУРА

```
[🚀 Groq Llama 3.3] [🦙 Groq Llama 4]
[🔍 Groq Scout] [🌙 Groq Kimi K2]
[⚡ Cerebras Llama 3.1] [🧠 Cerebras GPT-oss 120B]
[◀️ Назад к меню]
```

---

## 📊 ВСЕГО МОДЕЛЕЙ

| Сервис | Моделей | Статус |
|--------|---------|--------|
| **Groq** | 4 | ✅ Все работают |
| **Cerebras** | 2 | ✅ Все работают |
| **ИТОГО** | 6 | ✅ 6/6 |

---

## 🧪 ТЕСТИРОВАНИЕ

**Тесты Cerebras:**
- ✅ `llama3.1-8b` - РАБОТАЕТ
- ✅ `gpt-oss-120b` - РАБОТАЕТ
- ❌ `zai-glm-4.7` - 404 (исключена)
- ❌ `qwen-3-235b-a22b-instruct-2507` - 404 (исключена)

**Бот перезапущен:** ✅  
**Ошибок нет:** ✅  
**Клавиатура обновлена:** ✅

---

## 🚀 ИСПОЛЬЗОВАНИЕ

1. Напишите `/start`
2. Нажмите "🤖 Выбрать модель"
3. Выберите "🧠 Cerebras GPT-oss 120B"
4. Напишите сообщение - бот ответит через GPT-oss 120B

---

**Контакты:** @suplira  
**Документация:** https://github.com/LiraAiBotv1/LiraAiBOT
