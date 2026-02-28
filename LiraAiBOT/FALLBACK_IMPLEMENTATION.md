# 🔄 Fallback логика для LiraAI

## Логика работы:

1. Пользователь выбирает модель (например, Cerebras Qwen 3)
2. Бот пытается сделать запрос к выбранной модели
3. **Ошибка** → Бот пробует fallback:
   - Cerebras → Groq → OpenRouter
   - Groq → Cerebras → OpenRouter  
   - OpenRouter → Groq → Cerebras
4. **Fallback сработал** → Бот уведомляет:
   ```
   ⚠️ Модель [оригинальная] временно недоступна
   ✅ Переключаюсь на [fallback модель]
   ```

## Реализация:

```python
# В telegram_polling.py заменить обработку LLM запроса

# Получаем модель пользователя
original_model_key = user_models.get(user_id, "groq-llama")
model_key = original_model_key
model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
client_type, model = model_info

# Fallback порядок
fallback_order = []
if client_type == "groq":
    fallback_order = [
        ("groq", model, model_key),  # Оригинальная
        ("cerebras", "llama3.1-8b", "cerebras-llama"),  # Fallback 1
        ("openrouter", "upstage/solar-pro-3:free", "solar"),  # Fallback 2
    ]
elif client_type == "cerebras":
    fallback_order = [
        ("cerebras", model, model_key),  # Оригинальная
        ("groq", "llama-3.3-70b-versatile", "groq-llama"),  # Fallback 1
        ("openrouter", "upstage/solar-pro-3:free", "solar"),  # Fallback 2
    ]
else:  # openrouter
    fallback_order = [
        ("openrouter", model, model_key),  # Оригинальная
        ("groq", "llama-3.3-70b-versatile", "groq-llama"),  # Fallback 1
        ("cerebras", "llama3.1-8b", "cerebras-llama"),  # Fallback 2
    ]

for retry, (c_type, mdl, m_key) in enumerate(fallback_order):
    try:
        # Выбираем клиент
        if c_type == "groq":
            client = groq_client
        elif c_type == "cerebras":
            client = cerebras_client
        else:
            client = llm_client

        response = await client.chat_completion(...)
        
        # Успех!
        if retry > 0:
            # Fallback сработал - уведомляем
            await send_telegram_message(chat_id, f"⚠️ Модель недоступна, переключаюсь на fallback...")
        
        # Сохраняем в историю
        db.save_dialog_message(user_id, "user", text, model=m_key)
        db.save_dialog_message(user_id, "assistant", response, model=m_key)
        break
        
    except Exception as e:
        if retry == len(fallback_order) - 1:
            # Все попытки исчерпаны
            await send_telegram_message(chat_id, "❌ Все модели недоступны...")
            return
```

## Модели:

### Groq (быстрые):
- Llama 3.3 70B
- Llama 4 Maverick
- Llama 4 Scout
- Kimi K2

### Cerebras (сверхбыстрые):
- Llama 3.1 8B ✅
- GPT-oss 120B
- Qwen 3 235B
- GLM-4.7

### OpenRouter (качественные, fallback):
- Solar Pro 3
- Trinity Mini
- GLM-4.5
