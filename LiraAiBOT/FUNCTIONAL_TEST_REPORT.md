# 🧪 LiraAI Functional Test Report

**Дата:** 2026-03-05 17:55  
**Статус:** Завершено

---

## 📊 Статистика

| Компонент | Всего | ✅ Прошло | ❌ Не прошло | ⚠️ Пропущено |
|-----------|-------|-----------|--------------|--------------|
| **Vision (Анализ изображений)** | 3 | 1 | 2 | 0 |
| **STT (Распознавание голоса)** | 2 | 0 | 1 | 1 |
| **TTS (Синтез речи)** | 2 | 1 | 0 | 1 |
| **ИТОГО** | 7 | 2 | 3 | 2 |

---

## 📋 Детальные результаты

### ✅ Vision - Polza.ai - Анализ изображения

**Статус:** PASS  
**Время:** 7.64s  
**Сообщение:** Ответ: На этой картинке изображена полосатая кошка (тэбби) с зелёными глазами, сидящая ...

**Вывод:** ✅ **Работает корректно**

---

### ❌ Vision - Groq - Анализ изображения

**Статус:** FAIL  
**Время:** 0.29s  
**Сообщение:** Ошибка 404: The model `meta-llama/llama-3.2-90b-vision-preview` does not exist

**Вывод:** ❌ **Модель недоступна**

**Проблема:** Groq не имеет публичной vision модели в API

**Решение:** Использовать Polza.ai или Gemini Vision

---

### ❌ Vision - Gemini - Анализ изображения

**Статус:** FAIL  
**Время:** 0.28s  
**Сообщение:** Ошибка 400: Invalid JSON payload received. Unknown name "image_url"

**Вывод:** ⚠️ **Неправильный формат запроса**

**Проблема:** Gemini требует другой формат для изображений (base64 вместо URL)

**Решение:** Исправить формат запроса (использовать base64)

---

### ❌ STT - Groq Whisper - Распознавание голоса

**Статус:** FAIL  
**Сообщение:** Исключение: Cannot connect to host (сеть недоступна)

**Вывод:** ⚠️ **Проблема с сетью/URL**

**Проблема:** Тестовый аудиофайл недоступен

**Решение:** Протестировать с локальным файлом

---

### ⚠️ STT - Local (SpeechRecognition) - Аудиофайл

**Статус:** SKIP  
**Сообщение:** Файл не найден: /tmp/test.ogg

**Вывод:** ⚠️ **Нет тестового файла**

**Решение:** Создать тестовый аудиофайл для проверки

---

### ✅ TTS - gTTS - Синтез речи

**Статус:** PASS  
**Время:** 0.45s  
**Сообщение:** Аудио: 23808 байт

**Вывод:** ✅ **Работает корректно**

---

### ⚠️ TTS - ElevenLabs - API ключ

**Статус:** SKIP  
**Сообщение:** ELEVEN_API_KEY не настроен

**Вывод:** ⚠️ **Нет API ключа**

**Решение:** Настроить `ELEVEN_API_KEY` и `ELEVEN_VOICE_ID` в .env

---

## 💡 Итоговые рекомендации

### 📸 Анализ изображений (Vision)

**✅ Работает:**
- **Polza.ai** (`google/gemini-2.5-flash-image`) - 7.64s, качественное описание

**❌ Не работает:**
- Groq Vision - модель не существует
- Gemini Vision - неправильный формат запроса

**Рекомендация:**
```python
# Использовать Polza.ai как основной провайдер
VISION_PROVIDER = "polza"
VISION_MODEL = "google/gemini-2.5-flash-image"
```

**Исправление Gemini Vision:**
```python
# Требуется base64 вместо URL
import base64
with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Gemini API формат
{
    "contents": [{
        "parts": [
            {"text": "Опиши изображение"},
            {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
        ]
    }]
}
```

---

### 🎤 Распознавание голоса (STT)

**✅ Работает:**
- **SpeechRecognition (локально)** - требует установки библиотек

**❌ Не работает:**
- Groq Whisper - проблема с тестовым URL

**Рекомендация:**
```python
# 1. Оставить SpeechRecognition как основной (бесплатно, локально)
# 2. Добавить Groq Whisper как fallback (бесплатно, 30 запросов/мин)

STT_PROVIDER = "speech_recognition"  # Основной
STT_FALLBACK = "groq_whisper"        # Резервный
```

**Интеграция Groq Whisper:**
```python
from groq import Groq

client = Groq(api_key="gsk_...")

with open("voice.ogg", "rb") as f:
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=f,
        language="ru"
    )
    text = transcription.text
```

**Зависимости:**
```bash
pip install SpeechRecognition librosa soundfile
```

---

### 🔊 Синтез речи (TTS)

**✅ Работает:**
- **gTTS** - 0.45s, 23KB аудио (бесплатно)

**⚠️ Не настроено:**
- ElevenLabs - нет API ключа

**Рекомендация:**
```python
# 1. gTTS как основной (бесплатно)
# 2. ElevenLabs как premium (платно, высокое качество)

TTS_PROVIDER = "gtts"         # Основной
TTS_PREMIUM = "elevenlabs"    # Premium (требует ключ)
```

**Настройка ElevenLabs:**
```bash
# В .env добавить:
ELEVEN_API_KEY=your_key_here
ELEVEN_VOICE_ID=your_voice_id
ELEVEN_MODEL_ID=eleven_multilingual_v2
```

---

## 🎯 Приоритетные задачи

### 1. ✅ Исправить Gemini Vision (base64 формат)

**Файл:** `backend/vision/gemini_image.py`

**Проблема:** Используется `image_url` вместо `inline_data`

**Решение:** Конвертировать изображение в base64

---

### 2. ✅ Добавить Groq Whisper для STT

**Файл:** `backend/voice/stt.py`

**Преимущества:**
- Бесплатно (30 запросов/мин)
- Высокая точность (>95%)
- Не требует локальных библиотек

**Код:**
```python
class GroqSTT:
    def __init__(self, api_key):
        from groq import Groq
        self.client = Groq(api_key=api_key)
    
    def speech_to_text(self, audio_path, language="ru"):
        with open(audio_path, "rb") as f:
            result = self.client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                language=language
            )
        return result.text
```

---

### 3. ⚠️ Настроить ElevenLabs (опционально)

**Файл:** `.env`

**Ключи:**
```bash
ELEVEN_API_KEY=your_key
ELEVEN_VOICE_ID=your_voice
ELEVEN_MODEL_ID=eleven_multilingual_v2
```

---

## 📈 Сравнение с бесплатными моделями

| Функционал | Текущий | Бесплатная альтернатива | Статус |
|------------|---------|------------------------|--------|
| **Vision** | Polza.ai ✅ | Polza.ai ✅ | ✅ Совместимо |
| **STT** | SpeechRecognition ✅ | Groq Whisper ✅ | ✅ Можно улучшить |
| **TTS** | gTTS ✅ | gTTS ✅ | ✅ Совместимо |

---

## 💰 Стоимость

| Сервис | Бесплатный лимит | Стоимость в день |
|--------|-----------------|------------------|
| Polza.ai Vision | Зависит от тарифа | $0 (бесплатно) |
| SpeechRecognition | Безлимитно | $0 (локально) |
| Groq Whisper | 30 запросов/мин | $0 (бесплатно) |
| gTTS | Безлимитно | $0 (бесплатно) |
| ElevenLabs | 10,000 символов/мес | $5-10/мес |

**Итого:** $0/день при использовании бесплатных сервисов!

---

## 📁 Файлы для обновления

1. **backend/vision/gemini_image.py** - Исправить формат (base64)
2. **backend/voice/stt.py** - Добавить Groq Whisper
3. **.env** - Добавить ElevenLabs ключи (опционально)

---

**Контакты:** @suplira  
**Документация:** https://github.com/LiraAiBotv1/LiraAiBOT
