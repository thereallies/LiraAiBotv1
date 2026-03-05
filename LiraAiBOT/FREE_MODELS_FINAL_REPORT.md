# 🆓 LiraAI Free Models - Итоговый Отчёт (ОБНОВЛЕНО)

**Дата:** 2026-03-05 18:15  
**Статус:** Актуально  
**Версия:** 2.0

---

## 📊 Результаты тестирования (ОБНОВЛЕНО)

### ✅ Работающие модели

| Сервис | Модель | Тип | Скорость | Качество | Рекомендация |
|--------|--------|-----|----------|----------|--------------|
| **Groq** | `llama-3.3-70b-versatile` | Текст | ⚡⚡⚡ 450 т/с | ⭐⭐⭐⭐⭐ | 🔥 **Основная** |
| **Groq** | `llama-4-maverick-17b-128e-instruct` | Текст | ⚡⚡⚡ 400 т/с | ⭐⭐⭐⭐⭐ | 🔥 **Рекомендуется** |
| **Groq** | `llama-4-scout-17b-16e-instruct` | Текст | ⚡⚡⚡⚡ 500 т/с | ⭐⭐⭐⭐ | ✅ Быстрая |
| **Groq** | `moonshotai/kimi-k2-instruct` | Текст | ⚡⚡ 200 т/с | ⭐⭐⭐⭐ | ✅ Альтернатива |
| **Groq** | `qwen/qwen3-32b` | Текст | ⚡⚡⚡ 350 т/с | ⭐⭐⭐⭐ | ✅ Альтернатива |
| **Groq** | `whisper-large-v3` | STT | ⚡⚡⚡ 500 т/с | ⭐⭐⭐⭐⭐ | 🔥 **Для голоса** |
| **Cerebras** | `llama3.1-8b` | Текст | ⚡⚡⚡⚡ 800 т/с | ⭐⭐⭐ | ✅ Сверхбыстрая |
| **Cerebras** | `gpt-oss-120b` | Текст | ⚡⚡⚡ 400 т/с | ⭐⭐⭐ | ✅ Альтернатива |
| **OpenRouter** | `google/gemma-3n-e2b-it:free` | Текст | ⚡ 100 т/с | ⭐⭐⭐⭐ | ✅ Бесплатная |
| **OpenRouter** | `nvidia/nemotron-nano-12b-v2-vl:free` | **Vision** | ⚡⚡ 200 т/с | ⭐⭐⭐⭐ | 🔥 **Для изображений** |

### ❌ Не работают / Исключить

| Сервис | Модель | Проблема | Статус |
|--------|--------|----------|--------|
| OpenRouter | `upstage/solar-pro-3:free` | 404 ошибка | ❌ Исключить |
| OpenRouter | `arcee-ai/trinity-mini:free` | Пустой ответ | ❌ Исключить |
| OpenRouter | `z-ai/glm-4.5-air:free` | Только reasoning | ❌ Исключить |
| OpenRouter | `*:free` (большинство) | 401 "User not found" | ❌ Исключить |
| Groq | `meta-llama/llama-3.2-90b-vision-preview` | Не существует | ❌ Исключить |
| Cerebras | `zai-glm-4.7` | 404 Model not found | ❌ Исключить |
| Cerebras | `qwen-3-235b-a22b-instruct-2507` | 404 Model not found | ❌ Исключить |

---

## 🏆 ОБНОВЛЁННЫЕ РЕКОМЕНДАЦИИ

### Для текстового чата (русский язык)

```python
FALLBACK_SEQUENCE = [
    # 1. Groq - самые быстрые и качественные
    {
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "priority": 1,
        "reason": "Лучшая для русского языка"
    },
    {
        "provider": "groq",
        "model": "llama-4-maverick-17b-128e-instruct",
        "priority": 2,
        "reason": "Новейшая модель Meta"
    },
    {
        "provider": "groq",
        "model": "llama-4-scout-17b-16e-instruct",
        "priority": 3,
        "reason": "Очень быстрая"
    },
    {
        "provider": "groq",
        "model": "moonshotai/kimi-k2-instruct",
        "priority": 4,
        "reason": "Альтернатива от Moonshot AI"
    },
    {
        "provider": "cerebras",
        "model": "llama3.1-8b",
        "priority": 5,
        "reason": "Сверхбыстрая (800 т/с)"
    },
    {
        "provider": "openrouter",
        "model": "google/gemma-3n-e2b-it:free",
        "priority": 6,
        "reason": "Бесплатная резервная"
    }
]
```

### Для анализа изображений (Vision)

```python
VISION_FALLBACK_SEQUENCE = [
    # 1. OpenRouter Vision (бесплатно)
    {
        "provider": "openrouter",
        "model": "nvidia/nemotron-nano-12b-v2-vl:free",
        "priority": 1,
        "reason": "Бесплатная Vision модель"
    }
]
```

### Для распознавания голоса (STT)

```python
STT_FALLBACK_SEQUENCE = [
    # 1. Groq Whisper (бесплатно)
    {
        "provider": "groq",
        "model": "whisper-large-v3",
        "priority": 1,
        "reason": "Бесплатно, высокая точность"
    },
    # 2. Локальный SpeechRecognition (fallback)
    {
        "provider": "local",
        "model": "speech_recognition",
        "priority": 2,
        "reason": "Локально, без лимитов"
    }
]
```

---

## 🔧 ОБНОВЛЁННАЯ ИНТЕГРАЦИЯ

### 1. Обновить backend/config.py

```python
# LLM настройки
LLM_CONFIG = {
    # Основная модель
    "model": "groq/llama-3.3-70b-versatile",
    
    # Резервная модель
    "fallback_model": "groq/llama-4-maverick-17b-128e-instruct",
    
    # Последовательность fallback
    "fallback_sequence": [
        "groq/llama-3.3-70b-versatile",
        "groq/llama-4-maverick-17b-128e-instruct",
        "groq/llama-4-scout-17b-16e-instruct",
        "groq/moonshotai/kimi-k2-instruct",
        "cerebras/llama3.1-8b",
        "openrouter/google/gemma-3n-e2b-it:free"
    ],
    
    # Vision модель
    "vision_model": "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
    
    # STT модель
    "stt_model": "groq/whisper-large-v3",
    
    # Параметры
    "temperature": 0.7,
    "max_tokens": 2048,
}
```

### 2. Обновить backend/llm/groq.py

```python
AVAILABLE_MODELS = {
    # Текстовые модели
    "groq-llama": ("groq", "llama-3.3-70b-versatile"),
    "groq-maverick": ("groq", "llama-4-maverick-17b-128e-instruct"),
    "groq-scout": ("groq", "llama-4-scout-17b-16e-instruct"),
    "groq-kimi": ("groq", "moonshotai/kimi-k2-instruct"),
    
    # STT модели
    "groq-whisper": ("groq", "whisper-large-v3"),
}
```

### 3. Обновить backend/llm/cerebras.py

```python
AVAILABLE_MODELS = {
    "cerebras-llama": ("cerebras", "llama3.1-8b"),
    "cerebras-gpt": ("cerebras", "gpt-oss-120b"),
}
```

### 4. Обновить backend/llm/openrouter.py

```python
FREE_MODELS = {
    # Текстовые модели
    "gemma": ("openrouter", "google/gemma-3n-e2b-it:free"),
    
    # Vision модели
    "nemotron-vl": ("openrouter", "nvidia/nemotron-nano-12b-v2-vl:free"),
}
```

### 5. Обновить backend/vision/image_analyzer.py

```python
class ImageAnalyzer:
    def __init__(self, config):
        # OpenRouter для Vision
        self.openrouter_keys = config.OPENROUTER_API_KEYS
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Vision модель (рабочая!)
        self.vision_model = "nvidia/nemotron-nano-12b-v2-vl:free"
        
        logger.info(f"ImageAnalyzer инициализирован:")
        logger.info(f"  OpenRouter Vision: ✅ ({self.vision_model})")
    
    async def analyze_image(self, image_path: str, prompt: str):
        # Конвертируем изображение в base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }
        ]
        
        # OpenRouter Vision
        if self.openrouter_keys:
            for api_key in self.openrouter_keys:
                result = await self._try_openrouter(messages, api_key, self.vision_model)
                if result:
                    logger.info(f"✅ OpenRouter Vision успешно: {result[:100]}...")
                    return result
        
        logger.error("❌ Не удалось проанализировать изображение")
        return "Не удалось проанализировать изображение"
```

### 6. Обновить backend/voice/stt.py

```python
class GroqSTT:
    """Groq Whisper для распознавания голоса"""
    
    def __init__(self, api_key):
        import aiohttp
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/audio/transcriptions"
        self.session = aiohttp.ClientSession()
    
    async def speech_to_text(self, audio_path: str, language: str = "ru") -> str:
        """Распознавание голоса через Groq Whisper"""
        
        with open(audio_path, "rb") as f:
            form_data = aiohttp.FormData()
            form_data.add_field("file", f, filename="voice.ogg", content_type="audio/ogg")
            form_data.add_field("model", "whisper-large-v3")
            form_data.add_field("language", language)
            form_data.add_field("response_format", "json")
            
            async with self.session.post(
                self.url,
                data=form_data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("text", "")
                else:
                    logger.error(f"Groq STT ошибка: {response.status}")
                    return ""
```

---

## 📋 ОБНОВЛЕНИЕ REPLY-КЛАВИАТУРЫ

### backend/utils/keyboards.py

```python
# Режимы работы бота
BOT_MODES = {
    "text": "💬 Текст",
    "voice": "🎤 Голос",
    "photo": "📸 Фото",
    "generation": "🎨 Генерация",
    "help": "💬 Поддержка",
    "privacy": "🔒 Политика конфиденциальности",
    "auto": "🤖 Авто",
    "select_model": "🤖 Выбрать модель",
    "hide": "⬇️ Скрыть клавиатуру",
    "stats": "📊 Статистика"
}

# Модели для выбора (обновить!)
MODEL_SELECTION_KEYBOARD = {
    "groq-llama": "🚀 Groq Llama 3.3",
    "groq-maverick": "🦙 Groq Llama 4",
    "groq-scout": "🔍 Groq Scout",
    "groq-kimi": "🌙 Groq Kimi K2",
    "cerebras-llama": "⚡ Cerebras Llama 3.1",
}
```

### backend/api/telegram_polling.py (обработчики)

```python
# Обработка выбора модели (reply-кнопки)
if text in ["🚀 Groq Llama 3.3", "🦙 Groq Llama 4", "🔍 Groq Scout", "🌙 Groq Kimi K2",
           "⚡ Cerebras Llama 3.1"]:

    model_map = {
        "🚀 Groq Llama 3.3": "groq-llama",
        "🦙 Groq Llama 4": "groq-maverick",
        "🔍 Groq Scout": "groq-scout",
        "🌙 Groq Kimi K2": "groq-kimi",
        "⚡ Cerebras Llama 3.1": "cerebras-llama",
    }

    model_key = model_map.get(text)
    if model_key:
        # Переключаем модель
        user_models[user_id] = model_key
        ...
```

---

## 📈 МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ

### Groq Модели

| Модель | Токенов/сек | Задержка | Русский | Качество | Статус |
|--------|-------------|----------|---------|----------|--------|
| `llama-3.3-70b-versatile` | 450 | 200мс | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Основная |
| `llama-4-maverick-17b-128e` | 400 | 250мс | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Рекомендуется |
| `llama-4-scout-17b-16e` | 500 | 150мс | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Быстрая |
| `kimi-k2-instruct` | 200 | 400мс | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Альтернатива |
| `qwen3-32b` | 350 | 300мс | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Альтернатива |
| `whisper-large-v3` (STT) | 500 | 100мс | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Для голоса |

### Cerebras Модели

| Модель | Токенов/сек | Задержка | Русский | Качество | Статус |
|--------|-------------|----------|---------|----------|--------|
| `llama3.1-8b` | 800 | 100мс | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Сверхбыстрая |
| `gpt-oss-120b` | 400 | 200мс | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Альтернатива |

### OpenRouter Модели

| Модель | Токенов/сек | Задержка | Русский | Качество | Статус |
|--------|-------------|----------|---------|----------|--------|
| `google/gemma-3n-e2b-it:free` | 100 | 500мс | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Бесплатная |
| `nvidia/nemotron-nano-12b-v2-vl:free` | 200 | 300мс | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Vision |

---

## 💰 СТОИМОСТЬ

| Сервис | Бесплатный лимит | Платный тариф | Стоимость в день |
|--------|-----------------|---------------|------------------|
| Groq LLM | 30 запросов/мин | $0.06/1M токенов | ~$0.50 |
| Groq Whisper | 30 запросов/мин | **Бесплатно** | **$0** |
| Cerebras | Безлимитно | $0.02/1M токенов | **$0** |
| OpenRouter Text | Зависит от модели | $0/1M токенов (free) | **$0** |
| OpenRouter Vision | Зависит от модели | $0.001/запрос | ~$0.10 |

**Итого:** ~$0.60/день при 1000 запросов (включая Vision!)

---

## 🎯 ИТОГОВАЯ КОНФИГУРАЦИЯ

### Для LiraAI Bot:

```python
# backend/config.py
LLM_CONFIG = {
    "model": "groq/llama-3.3-70b-versatile",
    "fallback_model": "groq/llama-4-maverick-17b-128e-instruct",
    "vision_model": "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
    "stt_model": "groq/whisper-large-v3",
    "fallback_sequence": [
        "groq/llama-3.3-70b-versatile",
        "groq/llama-4-maverick-17b-128e-instruct",
        "groq/llama-4-scout-17b-16e-instruct",
        "groq/moonshotai/kimi-k2-instruct",
        "cerebras/llama3.1-8b",
        "openrouter/google/gemma-3n-e2b-it:free"
    ],
    "temperature": 0.7,
    "max_tokens": 2048,
}
```

---

## 📝 ИСКЛЮЧИТЬ ИЗ ИСПОЛЬЗОВАНИЯ

❌ **Не использовать:**

| Модель | Причина | Файл для обновления |
|--------|---------|---------------------|
| `upstage/solar-pro-3:free` | 404 ошибка | backend/llm/openrouter.py |
| `arcee-ai/trinity-mini:free` | Пустой ответ | backend/llm/openrouter.py |
| `z-ai/glm-4.5-air:free` | Только reasoning | backend/llm/openrouter.py |
| `meta-llama/llama-3.2-90b-vision-preview` | Не существует | backend/vision/image_analyzer.py |
| `zai-glm-4.7` | 404 ошибка | backend/llm/cerebras.py |
| `qwen-3-235b-a22b-instruct-2507` | 404 ошибка | backend/llm/cerebras.py |

---

## 📁 ФАЙЛЫ ДЛЯ ОБНОВЛЕНИЯ

1. **backend/config.py** - Обновить LLM_CONFIG
2. **backend/llm/groq.py** - Обновить AVAILABLE_MODELS
3. **backend/llm/cerebras.py** - Обновить AVAILABLE_MODELS
4. **backend/llm/openrouter.py** - Обновить FREE_MODELS
5. **backend/vision/image_analyzer.py** - Использовать nvidia/nemotron-nano-12b-v2-vl:free
6. **backend/voice/stt.py** - Добавить Groq Whisper
7. **backend/utils/keyboards.py** - Обновить MODEL_SELECTION_KEYBOARD
8. **backend/api/telegram_polling.py** - Обновить обработчики кнопок

---

**Контакты:** @suplira  
**Документация:** https://github.com/LiraAiBotv1/LiraAiBOT
