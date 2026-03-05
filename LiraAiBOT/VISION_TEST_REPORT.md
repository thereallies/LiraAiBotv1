# 👁️ LiraAI Vision Models Test Report

**Дата:** 2026-03-05T19:46:54.420982

## 📊 Статистика

- Всего тестов: 6
- ✅ Прошло: 0
- ❌ Не прошло: 6
- ⚠️ Пропущено: 0

## 📋 Результаты

### ❌ Groq Vision - meta-llama/llama-3.2-90b-vision-preview

**Статус:** FAIL

**Сообщение:** Ошибка 404: {"error":{"message":"The model `meta-llama/llama-3.2-90b-vision-preview` does not exist or you do no
**Время:** 0.36s

---

### ❌ Cerebras Vision - llama-3.3-70b-instruct

**Статус:** FAIL

**Сообщение:** Ошибка 404: {"message":"Model llama-3.3-70b-instruct does not exist or you do not have access to it.","type":"no
**Время:** 0.52s

---

### ❌ OpenRouter Vision - nvidia/nemotron-nano-12b-v2-vl:free

**Статус:** FAIL

**Сообщение:** Пустой ответ
**Время:** 1.13s

---

### ❌ OpenRouter Vision - qwen/qwen3-vl-30b-a3b-thinking:free

**Статус:** FAIL

**Сообщение:** Ошибка 404: {"error":{"message":"No endpoints found for qwen/qwen3-vl-30b-a3b-thinking:free.
**Время:** 0.06s

---

### ❌ OpenRouter Vision - qwen/qwen3-vl-235b-a22b-thinking:free

**Статус:** FAIL

**Сообщение:** Ошибка 404: {"error":{"message":"No endpoints found for qwen/qwen3-vl-235b-a22b-thinking:fre
**Время:** 0.06s

---

### ❌ OpenRouter Vision - google/gemma-3n-e2b-it:free

**Статус:** FAIL

**Сообщение:** Ошибка 404: {"error":{"message":"No endpoints found that support image input","code":404}}
**Время:** 0.06s

---

## 💡 Рекомендации для ImageAnalyzer

### Текущая конфигурация

```python
# backend/vision/image_analyzer.py
self.groq_model = "meta-llama/llama-3.2-90b-vision-preview"
self.cerebras_model = "llama-3.3-70b-instruct"
self.openrouter_models = [
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "qwen/qwen3-vl-30b-a3b-thinking:free",
    "qwen/qwen3-vl-235b-a22b-thinking:free",
]
```

### ❌ Нет рабочих моделей

**Рекомендация:** Использовать Gemini Vision через Polza.ai или напрямую
