# 👁️ LiraAI Vision Analysis Report

**Дата:** 2026-03-05  
**Статус:** Критическая проблема  
**Версия:** 1.0

---

## 🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА

**ImageAnalyzer НЕ РАБОТАЕТ** - все модели для анализа изображений недоступны!

---

## 📊 Результаты тестирования

### ❌ Все модели не работают (0/6)

| Сервис | Модель | Статус | Ошибка |
|--------|--------|--------|--------|
| **Groq** | `meta-llama/llama-3.2-90b-vision-preview` | ❌ 404 | Модель не существует |
| **Cerebras** | `llama-3.3-70b-instruct` | ❌ 404 | Нет доступа |
| **OpenRouter** | `nvidia/nemotron-nano-12b-v2-vl:free` | ❌ Пустой ответ | Не поддерживает vision |
| **OpenRouter** | `qwen/qwen3-vl-30b-a3b-thinking:free` | ❌ 404 | No endpoints found |
| **OpenRouter** | `qwen/qwen3-vl-235b-a22b-thinking:free` | ❌ 404 | No endpoints found |
| **OpenRouter** | `google/gemma-3n-e2b-it:free` | ❌ 404 | No image input support |

---

## 🔍 Анализ проблемы

### 1. Groq Vision ❌

**Проблема:** Модель `meta-llama/llama-3.2-90b-vision-preview` не существует

**Причина:** Groq **НЕ ПРЕДОСТАВЛЯЕТ** публичные vision модели

**Статус Groq API:**
- ✅ Текстовые модели (Llama, Qwen, Kimi)
- ✅ Whisper (STT)
- ❌ Vision модели (недоступны)

---

### 2. Cerebras Vision ❌

**Проблема:** Модель `llama-3.3-70b-instruct` не поддерживает vision

**Причина:** Cerebras **НЕ ПРЕДОСТАВЛЯЕТ** vision модели

**Статус Cerebras API:**
- ✅ Текстовые модели (Llama 3.1, Qwen, GLM)
- ❌ Vision модели (недоступны)
- ❌ STT/TTS (недоступны)

---

### 3. OpenRouter Vision ❌

**Проблема:** Бесплатные vision модели не работают

**Причины:**
- `nvidia/nemotron-nano-12b-v2-vl:free` - пустой ответ
- `qwen/qwen3-vl-*:free` - нет endpoints
- `google/gemma-3n-e2b-it:free` - не поддерживает image input

**Статус OpenRouter API:**
- ✅ Текстовые модели (бесплатные)
- ❌ Vision модели (требуют платный тариф)

---

## 💡 РЕШЕНИЯ

### Решение 1: Gemini Vision (бесплатно) ✅

**API:** Google Gemini 2.0 Flash  
**Лимит:** 15 запросов/минуту (бесплатно)  
**Качество:** ⭐⭐⭐⭐⭐

**Интеграция:**
```python
# backend/vision/image_analyzer.py
import aiohttp
from google import genai

class GeminiVisionAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
    
    async def analyze_image(self, image_path: str, prompt: str):
        import base64
        
        # Конвертируем в base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # Gemini API
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ]
        )
        
        return response.text
```

**Настройка:**
```bash
# В .env добавить:
GEMINI_API_KEY=AIzaSy...
```

**Преимущества:**
- ✅ Бесплатно (15 запросов/мин)
- ✅ Высокое качество
- ✅ Поддержка русского языка
- ✅ Быстро (< 3 секунд)

---

### Решение 2: Polza.ai (бесплатно) ✅

**API:** Polza.ai (Gemini 2.5 Flash Image)  
**Лимит:** Зависит от тарифа  
**Качество:** ⭐⭐⭐⭐⭐

**Интеграция:**
```python
# backend/vision/image_analyzer.py
import aiohttp

class PolzaVisionAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.polza.ai/v1/chat/completions"
    
    async def analyze_image(self, image_path: str, prompt: str):
        import base64
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        ) as session:
            async with session.post(
                self.url,
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                        ]
                    }],
                    "max_tokens": 300
                }
            ) as response:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
```

**Настройка:**
```bash
# В .env добавить:
POLZA_API_KEY=pza_...
```

**Преимущества:**
- ✅ Бесплатно
- ✅ Высокое качество
- ✅ Поддержка русского языка

---

### Решение 3: OpenRouter (платно)

**API:** OpenRouter Vision модели  
**Стоимость:** $0.001-0.01/запрос  
**Качество:** ⭐⭐⭐⭐⭐

**Рабочие модели:**
- `openai/gpt-4o` - $0.005/запрос
- `anthropic/claude-sonnet-4.5` - $0.003/запрос
- `google/gemini-2.0-flash` - $0.001/запрос

**Интеграция:**
```python
# backend/vision/image_analyzer.py
self.openrouter_models = [
    "google/gemini-2.0-flash",  # $0.001/запрос
    "openai/gpt-4o",            # $0.005/запрос
]
```

---

## 🎯 РЕКОМЕНДАЦИИ

### Приоритет 1: Gemini Vision (бесплатно)

**Файл:** `backend/vision/image_analyzer.py`

**Изменения:**
```python
# Удалить нерабочие модели
self.groq_model = None  # ❌ Не существует
self.cerebras_model = None  # ❌ Не поддерживает vision
self.openrouter_models = []  # ❌ Бесплатные не работают

# Добавить Gemini
self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
self.gemini_model = "gemini-2.0-flash"
```

**Код:**
```python
async def analyze_image(self, image_path: str, prompt: str):
    # 1. Gemini Vision (приоритет)
    if self.gemini_key:
        result = await self._try_gemini(image_path, prompt)
        if result:
            return result
    
    # 2. Polza.ai (fallback)
    if self.polza_key:
        result = await self._try_polza(image_path, prompt)
        if result:
            return result
    
    return "Не удалось проанализировать изображение"
```

---

### Приоритет 2: Polza.ai (fallback)

**Файл:** `backend/vision/image_analyzer.py`

**Изменения:**
```python
self.polza_key = os.environ.get("POLZA_API_KEY", "")
self.polza_model = "google/gemini-2.5-flash-image"
```

---

### Приоритет 3: Удалить нерабочие модели

**Файл:** `backend/vision/image_analyzer.py`

**Удалить:**
```python
# ❌ Удалить:
self.groq_model = "meta-llama/llama-3.2-90b-vision-preview"
self.cerebras_model = "llama-3.3-70b-instruct"
self.openrouter_models = [
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "qwen/qwen3-vl-30b-a3b-thinking:free",
    "qwen/qwen3-vl-235b-a22b-thinking:free",
]
```

---

## 📁 Файлы для обновления

1. **backend/vision/image_analyzer.py** - Полная переработка
2. **backend/config.py** - Добавить Gemini/Polza настройки
3. **.env** - Добавить `GEMINI_API_KEY`

---

## 💰 Стоимость

| Сервис | Бесплатный лимит | Стоимость в день |
|--------|-----------------|------------------|
| Gemini Vision | 15 запросов/мин | **$0 (бесплатно!)** |
| Polza.ai | Зависит от тарифа | **$0 (бесплатно!)** |
| OpenRouter Vision | 0 | $0.50-5.00/день |

**Итого:** $0/день при использовании Gemini Vision!

---

## 📝 Итоговая конфигурация

```python
# backend/vision/image_analyzer.py

class ImageAnalyzer:
    def __init__(self, config):
        # API ключи
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")
        self.polza_key = os.environ.get("POLZA_API_KEY", "")
        
        # Модели
        self.gemini_model = "gemini-2.0-flash"
        self.polza_model = "google/gemini-2.5-flash-image"
        
        # Приоритет: Gemini → Polza
        logger.info(f"ImageAnalyzer инициализирован:")
        logger.info(f"  Gemini: {'✅' if self.gemini_key else '❌'}")
        logger.info(f"  Polza.ai: {'✅' if self.polza_key else '❌'}")
    
    async def analyze_image(self, image_path: str, prompt: str):
        # 1. Gemini Vision (приоритет, бесплатно)
        if self.gemini_key:
            result = await self._try_gemini(image_path, prompt)
            if result:
                return result
        
        # 2. Polza.ai (fallback, бесплатно)
        if self.polza_key:
            result = await self._try_polza(image_path, prompt)
            if result:
                return result
        
        return "Не удалось проанализировать изображение"
```

---

**Контакты:** @suplira  
**Документация:** https://github.com/LiraAiBotv1/LiraAiBOT
