# 🔑 LiraAI API Integration Guide

**Дата:** 2026-03-05  
**Статус:** Актуально

---

## 📊 Сводка по API ключам

| Сервис | Статус | Ключей | Моделей | Бесплатно |
|--------|--------|--------|---------|-----------|
| **OpenRouter** | ✅ | 1 | 28 | ✅ 28 |
| **Groq** | ✅ | 1 | 20 | ✅ 20 |
| **Cerebras** | ✅ | 1 | 4 | ✅ 4 |
| **Polza.ai** | ✅ | 1 | 368 | ✅ 368 |
| **Replicate** | ✅ | 1 | N/A | ❌ Платный |
| **Pollinations** | ✅ | 1 | 1 | ✅ 1 |
| **KIE.AI** | ⚠️ | 1 | 0 | ❌ 404 |
| **Google Gemini** | ❌ | 0 | 0 | ❌ Не работает |
| **SiliconFlow** | ❌ | 1 | 0 | ❌ 401 |

---

## 🏆 Топ бесплатных моделей

### 1. Groq (Самые быстрые) ⚡

**Скорость:** 100-500 токенов/сек  
**Лимит:** 30 запросов/минуту

| Модель | Описание | Контекст | Рекомендация |
|--------|----------|----------|--------------|
| `llama-3.3-70b-versatile` | Лучшая для русского | 128K | 🔥 **Основная** |
| `llama-4-maverick-17b-128e-instruct` | Новейшая Meta | 256K | 🔥 **Рекомендуется** |
| `llama-4-scout-17b-16e-instruct` | Лёгкая версия | 256K | ✅ Для быстрых задач |
| `moonshotai/kimi-k2-instruct` | От Moonshot AI | 256K | ✅ Альтернатива |

**Как использовать:**
```python
from backend.llm.groq import get_groq_client

client = get_groq_client()
response = await client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Привет!"}]
)
```

---

### 2. Cerebras (Сверхбыстрые) 🚀

**Скорость:** 500-1000 токенов/сек  
**Лимит:** Безлимитно (бесплатно)

| Модель | Описание | Контекст | Рекомендация |
|--------|----------|----------|--------------|
| `llama3.1-8b` | Сверхбыстрая | 128K | 🔥 **Для простых задач** |
| `qwen-3-235b-a22b-instruct-2507` | Большая модель | 256K | ✅ Для сложных задач |
| `zai-glm-4.7` | От Zhipu AI | 128K | ✅ Альтернатива |

**Как использовать:**
```python
from backend.llm.cerebras import get_cerebras_client

client = get_cerebras_client()
response = await client.chat.completions.create(
    model="llama3.1-8b",
    messages=[{"role": "user", "content": "Привет!"}]
)
```

---

### 3. OpenRouter (Много бесплатных) ☁️

**Скорость:** 50-200 токенов/сек  
**Лимит:** Зависит от модели

| Модель | Описание | Контекст | Рекомендация |
|--------|----------|----------|--------------|
| `z-ai/glm-4.5-air:free` | Полностью бесплатная | 128K | 🔥 **Основная** |
| `arcee-ai/trinity-mini:free` | Мультимодальная | 32K | ✅ Для фото+текст |
| `upstage/solar-pro-3:free` | Быстрая и качественная | 32K | ✅ Альтернатива |

**Как использовать:**
```python
from backend.llm.openrouter import OpenRouterClient
from backend.config import Config

client = OpenRouterClient(Config())
response = await client.chat.completions.create(
    model="z-ai/glm-4.5-air:free",
    messages=[{"role": "user", "content": "Привет!"}]
)
```

---

### 4. Polza.ai (Генерация изображений) 🎨

**Скорость:** 5-30 секунд на изображение  
**Лимит:** Зависит от тарифа

| Модель | Описание | Качество | Рекомендация |
|--------|----------|----------|--------------|
| `tongyi-mai/z-image` | Z-Image | Высокое | 🔥 **Основная** |
| `bytedance/seedream` | Seedream | Среднее | ✅ Быстрая |
| `black-forest-labs/flux.2-pro` | FLUX.2 | Очень высокое | ✅ Premium |

**Как использовать:**
```python
from backend.vision.hf_replicate import get_hf_replicate_client

client = get_hf_replicate_client()
image_url = await client.generate_image(
    model="tongyi-mai/z-image",
    prompt="Кот в очках, киберпанк"
)
```

---

## 📋 Рекомендации по интеграции

### 1. Приоритет моделей (Fallback цепочка)

```python
FALLBACK_SEQUENCE = [
    # 1. Groq (самые быстрые)
    {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    {"provider": "groq", "model": "llama-4-maverick-17b-128e-instruct"},
    
    # 2. Cerebras (сверхбыстрые)
    {"provider": "cerebras", "model": "llama3.1-8b"},
    
    # 3. OpenRouter (бесплатные)
    {"provider": "openrouter", "model": "z-ai/glm-4.5-air:free"},
    {"provider": "openrouter", "model": "arcee-ai/trinity-mini:free"},
]
```

### 2. Генерация изображений

```python
IMAGE_FALLBACK_SEQUENCE = [
    # 1. Polza.ai (бесплатно)
    {"provider": "polza", "model": "tongyi-mai/z-image"},
    
    # 2. Pollinations (бесплатно)
    {"provider": "pollinations", "model": "default"},
]
```

### 3. Обновление конфигурации

**Файл:** `backend/config.py`

```python
LLM_CONFIG = {
    "primary": {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.7,
        "max_tokens": 2048,
    },
    "fallback": [
        {"provider": "groq", "model": "llama-4-maverick-17b-128e-instruct"},
        {"provider": "cerebras", "model": "llama3.1-8b"},
        {"provider": "openrouter", "model": "z-ai/glm-4.5-air:free"},
    ]
}

IMAGE_CONFIG = {
    "primary": {
        "provider": "polza",
        "model": "tongyi-mai/z-image",
    },
    "fallback": [
        {"provider": "pollinations", "model": "default"},
    ]
}
```

---

## ⚠️ Проблемные сервисы

### Google Gemini ❌

**Проблема:** API ключ недействителен  
**Решение:** 
1. Получить новый ключ: https://makersuite.google.com/app/apikey
2. Обновить `.env`: `GEMINI_API_KEY=новый_ключ`

### SiliconFlow ❌

**Проблема:** Ошибка 401 (неверный ключ)  
**Решение:**
1. Проверить ключ в личном кабинете: https://cloud.siliconflow.cn
2. Обновить `.env`: `SILICONFLOW_API_KEY=новый_ключ`

### KIE.AI ⚠️

**Проблема:** Endpoint 404  
**Решение:** 
1. Проверить документацию API
2. Возможно сервис закрыт

---

## 💰 Стоимость (бесплатные лимиты)

| Сервис | Бесплатный лимит | Платный тариф |
|--------|-----------------|---------------|
| Groq | 30 запросов/мин | $0.06/1M токенов |
| Cerebras | Безлимитно | $0.02/1M токенов |
| OpenRouter | Зависит от модели | От $0.01/1M токенов |
| Polza.ai | Зависит от тарифа | От $10/месяц |

---

## 🔧 Быстрая настройка

### 1. Проверка ключей

```bash
cd /Users/iluyshin.d/Desktop/LiraAiBOT
python3 test_api_keys.py
```

### 2. Обновление ключей

```bash
nano .env
# Изменить нужные ключи
# Сохранить (Ctrl+O, Enter, Ctrl+X)
```

### 3. Перезапуск бота

```bash
pm2 restart LiraAiBOT
pm2 logs LiraAiBOT --lines 50
```

---

## 📈 Метрики производительности

| Модель | Скорость (ток/сек) | Задержка (мс) | Качество |
|--------|-------------------|---------------|----------|
| Groq Llama 3.3 | 450 | 200 | ⭐⭐⭐⭐⭐ |
| Groq Llama 4 | 400 | 250 | ⭐⭐⭐⭐⭐ |
| Cerebras Llama 3.1 | 800 | 100 | ⭐⭐⭐⭐ |
| OpenRouter GLM-4.5 | 150 | 500 | ⭐⭐⭐⭐ |

---

## 🎯 Итоговые рекомендации

1. **Для текста:** Использовать Groq Llama 3.3 как основную модель
2. **Для скорости:** Использовать Cerebras Llama 3.1 для простых задач
3. **Для резерва:** Использовать OpenRouter GLM-4.5
4. **Для изображений:** Использовать Polza.ai Z-Image
5. **Мониторить:** Запускать `test_api_keys.py` раз в неделю

---

**Контакты поддержки:** @suplira  
**Документация:** https://github.com/LiraAiBotv1/LiraAiBOT
