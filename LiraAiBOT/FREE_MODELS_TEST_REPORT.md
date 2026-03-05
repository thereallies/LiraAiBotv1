# 🆓 LiraAI Free Models Test Report

**Дата:** 2026-03-05T17:55:29.801560

## 📊 Статистика

- Всего тестов: 32
- ✅ Прошло: 11
- ❌ Не прошло: 21
- ⚠️ Пропущено: 0

## 🏆 Работающие модели

### Текстовый чат

- `qwen/qwen3-32b`
- `llama-3.1-8b-instant`
- `groq/compound`
- `moonshotai/kimi-k2-instruct-0905`
- `meta-llama/llama-4-maverick-17b-128e-instruct`
- `meta-llama/llama-4-scout-17b-16e-instruct`
- `openai/gpt-oss-20b`
- `groq/compound-mini`
- `allam-2-7b`
- `gpt-oss-120b`
- `llama3.1-8b`

### Анализ изображений


## 💡 Рекомендации

```python
FALLBACK_SEQUENCE = [
    {"provider": "groq", "model": "qwen/qwen3-32b"},
    {"provider": "groq", "model": "llama-3.1-8b-instant"},
    {"provider": "openrouter", "model": "groq/compound"},
]
```
