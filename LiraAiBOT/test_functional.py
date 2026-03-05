#!/usr/bin/env python3
"""
Тестирование функционала LiraAI:
1. Анализ изображений (Vision)
2. Распознаание голоса (STT)
3. Синтез речи (TTS)
"""
import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

# Добавляем backend в path
sys.path.insert(0, str(Path.cwd() / 'backend'))

# Результаты тестов
test_results = []

def log_result(component, test, status, message, response_time=None):
    """Логирование результата теста"""
    result = {
        "component": component,
        "test": test,
        "status": status,
        "message": message,
        "response_time": response_time,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    time_str = f" ({response_time:.2f}s)" if response_time else ""
    print(f"{status_icon} {component} - {test}: {message}{time_str}")


# ============================================
# ТЕСТ 1: АНАЛИЗ ИЗОБРАЖЕНИЙ (VISION)
# ============================================
async def test_groq_vision(api_key, image_url):
    """Тест Groq Vision API"""
    if not api_key:
        log_result("Vision - Groq", "API ключ", "SKIP", "GROQ_API_KEY не настроен")
        return False
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json={
                    "model": "meta-llama/llama-3.2-90b-vision-preview",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Что изображено на этой картинке? Ответь на русском."},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }],
                    "max_tokens": 300
                }
            ) as response:
                elapsed = asyncio.get_event_loop().time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        log_result("Vision - Groq", "Анализ изображения", "PASS", f"Ответ: {content[:80]}...", elapsed)
                        return True
                    else:
                        log_result("Vision - Groq", "Анализ изображения", "FAIL", "Пустой ответ", elapsed)
                else:
                    error = await response.text()
                    log_result("Vision - Groq", "Анализ изображения", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("Vision - Groq", "Анализ изображения", "FAIL", f"Исключение: {e}")
    
    return False


async def test_gemini_vision(api_key, image_url):
    """Тест Gemini Vision API"""
    if not api_key:
        log_result("Vision - Gemini", "API ключ", "SKIP", "GEMINI_API_KEY не настроен")
        return False
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": "Что изображено на этой картинке? Ответь на русском."},
                            {"image_url": image_url}
                        ]
                    }]
                }
            ) as response:
                elapsed = asyncio.get_event_loop().time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    if content:
                        log_result("Vision - Gemini", "Анализ изображения", "PASS", f"Ответ: {content[:80]}...", elapsed)
                        return True
                    else:
                        log_result("Vision - Gemini", "Анализ изображения", "FAIL", "Пустой ответ", elapsed)
                else:
                    error = await response.text()
                    log_result("Vision - Gemini", "Анализ изображения", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("Vision - Gemini", "Анализ изображения", "FAIL", f"Исключение: {e}")
    
    return False


async def test_polza_vision(api_key, image_url):
    """Тест Polza.ai Vision API"""
    if not api_key:
        log_result("Vision - Polza.ai", "API ключ", "SKIP", "POLZA_API_KEY не настроен")
        return False
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            async with session.post(
                "https://api.polza.ai/v1/chat/completions",
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Что изображено на этой картинке? Ответь на русском."},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }],
                    "max_tokens": 300
                }
            ) as response:
                elapsed = asyncio.get_event_loop().time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        log_result("Vision - Polza.ai", "Анализ изображения", "PASS", f"Ответ: {content[:80]}...", elapsed)
                        return True
                    else:
                        log_result("Vision - Polza.ai", "Анализ изображения", "FAIL", "Пустой ответ", elapsed)
                else:
                    error = await response.text()
                    log_result("Vision - Polza.ai", "Анализ изображения", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("Vision - Polza.ai", "Анализ изображения", "FAIL", f"Исключение: {e}")
    
    return False


# ============================================
# ТЕСТ 2: РАСПОЗНАВАНИЕ ГОЛОСА (STT)
# ============================================
async def test_groq_whisper(api_key, audio_url):
    """Тест Groq Whisper API"""
    if not api_key:
        log_result("STT - Groq Whisper", "API ключ", "SKIP", "GROQ_API_KEY не настроен")
        return False
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Скачиваем аудиофайл
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as audio_response:
                if audio_response.status != 200:
                    log_result("STT - Groq Whisper", "Скачивание аудио", "FAIL", f"Ошибка {audio_response.status}")
                    return False
                
                audio_data = await audio_response.read()
        
        # Отправляем в Groq Whisper
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            form_data = aiohttp.FormData()
            form_data.add_field("file", audio_data, filename="test.ogg", content_type="audio/ogg")
            form_data.add_field("model", "whisper-large-v3")
            form_data.add_field("language", "ru")
            form_data.add_field("response_format", "json")
            
            async with session.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                data=form_data
            ) as response:
                elapsed = asyncio.get_event_loop().time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    text = data.get("text", "")
                    if text:
                        log_result("STT - Groq Whisper", "Распознавание голоса", "PASS", f"Текст: {text[:80]}...", elapsed)
                        return True
                    else:
                        log_result("STT - Groq Whisper", "Распознавание голоса", "FAIL", "Пустой ответ", elapsed)
                else:
                    error = await response.text()
                    log_result("STT - Groq Whisper", "Распознавание голоса", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("STT - Groq Whisper", "Распознавание голоса", "FAIL", f"Исключение: {e}")
    
    return False


async def test_local_stt(audio_path):
    """Тест локального STT (SpeechRecognition)"""
    if not os.path.exists(audio_path):
        log_result("STT - Local (SpeechRecognition)", "Аудиофайл", "SKIP", f"Файл не найден: {audio_path}")
        return False
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        import speech_recognition as sr
        import librosa
        import soundfile as sf
        
        # Конвертируем в WAV
        temp_dir = Path.cwd() / "temp"
        temp_dir.mkdir(exist_ok=True)
        wav_path = temp_dir / "test_stt.wav"
        
        audio_data, sample_rate = librosa.load(audio_path, sr=16000)
        sf.write(str(wav_path), audio_data, sample_rate)
        
        # Распознаём
        recognizer = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            audio = recognizer.record(source)
        
        text = recognizer.recognize_google(audio, language="ru-RU")
        elapsed = asyncio.get_event_loop().time() - start_time
        
        if text:
            log_result("STT - Local (SpeechRecognition)", "Распознавание голоса", "PASS", f"Текст: {text[:80]}...", elapsed)
            return True
        else:
            log_result("STT - Local (SpeechRecognition)", "Распознавание голоса", "FAIL", "Пустой ответ", elapsed)
    except ImportError as e:
        log_result("STT - Local (SpeechRecognition)", "Библиотеки", "FAIL", f"Не установлены: {e}")
    except Exception as e:
        log_result("STT - Local (SpeechRecognition)", "Распознавание голоса", "FAIL", f"Исключение: {e}")
    
    return False


# ============================================
# ТЕСТ 3: СИНТЕЗ РЕЧИ (TTS)
# ============================================
async def test_elevenlabs_tts(api_key, voice_id):
    """Тест ElevenLabs TTS"""
    if not api_key:
        log_result("TTS - ElevenLabs", "API ключ", "SKIP", "ELEVEN_API_KEY не настроен")
        return False
    
    if not voice_id:
        log_result("TTS - ElevenLabs", "Voice ID", "SKIP", "ELEVEN_VOICE_ID не настроен")
        return False
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession(
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
        ) as session:
            async with session.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                json={
                    "text": "Привет! Это тест синтеза речи.",
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                }
            ) as response:
                elapsed = asyncio.get_event_loop().time() - start_time
                
                if response.status == 200:
                    audio_data = await response.read()
                    if len(audio_data) > 0:
                        log_result("TTS - ElevenLabs", "Синтез речи", "PASS", f"Аудио: {len(audio_data)} байт", elapsed)
                        return True
                    else:
                        log_result("TTS - ElevenLabs", "Синтез речи", "FAIL", "Пустой ответ", elapsed)
                else:
                    error = await response.text()
                    log_result("TTS - ElevenLabs", "Синтез речи", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("TTS - ElevenLabs", "Синтез речи", "FAIL", f"Исключение: {e}")
    
    return False


async def test_gtts_tts():
    """Тест gTTS TTS"""
    try:
        from gtts import gTTS
        import tempfile
        
        start_time = asyncio.get_event_loop().time()
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts = gTTS("Привет! Это тест синтеза речи.", lang="ru")
            tts.save(f.name)
            
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if os.path.getsize(f.name) > 0:
                log_result("TTS - gTTS", "Синтез речи", "PASS", f"Аудио: {os.path.getsize(f.name)} байт", elapsed)
                os.unlink(f.name)
                return True
            else:
                log_result("TTS - gTTS", "Синтез речи", "FAIL", "Пустой файл", elapsed)
                os.unlink(f.name)
    except ImportError:
        log_result("TTS - gTTS", "Библиотека", "SKIP", "gTTS не установлен")
    except Exception as e:
        log_result("TTS - gTTS", "Синтез речи", "FAIL", f"Исключение: {e}")
    
    return False


# ============================================
# MAIN
# ============================================
async def main():
    """Запуск всех тестов"""
    print("=" * 70)
    print("🧪 LiraAI Functional Testing Suite")
    print("   Vision • STT • TTS")
    print("=" * 70)
    print()
    
    # Загружаем .env
    from dotenv import load_dotenv
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл")
    else:
        print(f"❌ .env файл не найден")
        return
    
    # Получаем API ключи
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    polza_key = os.getenv("POLZA_API_KEY", "")
    eleven_key = os.getenv("ELEVEN_API_KEY", "")
    eleven_voice = os.getenv("ELEVEN_VOICE_ID", "")
    
    print()
    print("-" * 70)
    print("📋 API Ключи:")
    print(f"   Groq: {'✅' if groq_key else '❌'}")
    print(f"   Gemini: {'✅' if gemini_key else '❌'}")
    print(f"   Polza.ai: {'✅' if polza_key else '❌'}")
    print(f"   ElevenLabs: {'✅' if eleven_key and eleven_voice else '❌'}")
    print("-" * 70)
    print()
    
    # Тестовые данные
    test_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/320px-Cat_November_2010-1a.jpg"
    test_audio_url = "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav"
    test_audio_path = Path.cwd() / "temp" / "test_voice.ogg"
    
    # Запускаем тесты
    print("-" * 70)
    print("🧪 ТЕСТ 1: Анализ изображений (Vision)")
    print("-" * 70)
    print()
    
    await test_groq_vision(groq_key, test_image_url)
    await test_gemini_vision(gemini_key, test_image_url)
    await test_polza_vision(polza_key, test_image_url)
    
    print()
    print("-" * 70)
    print("🧪 ТЕСТ 2: Распознавание голоса (STT)")
    print("-" * 70)
    print()
    
    await test_groq_whisper(groq_key, test_audio_url)
    await test_local_stt(str(test_audio_path) if test_audio_path.exists() else "/tmp/test.ogg")
    
    print()
    print("-" * 70)
    print("🧪 ТЕСТ 3: Синтез речи (TTS)")
    print("-" * 70)
    print()
    
    await test_elevenlabs_tts(eleven_key, eleven_voice)
    await test_gtts_tts()
    
    print()
    print("=" * 70)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 70)
    
    # Считаем статистику
    total = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    skipped = sum(1 for r in test_results if r["status"] == "SKIP")
    
    print(f"\nВсего тестов: {total}")
    print(f"✅ Прошло: {passed}")
    print(f"❌ Не прошло: {failed}")
    print(f"⚠️ Пропущено: {skipped}")
    
    # Рекомендации
    print("\n" + "=" * 70)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 70)
    
    # Vision
    vision_passed = [r for r in test_results if "Vision" in r["component"] and r["status"] == "PASS"]
    if vision_passed:
        print(f"\n📸 Анализ изображений: ✅ Работает ({len(vision_passed)} сервисов)")
        for r in vision_passed:
            print(f"   • {r['component']}: {r['message'][:60]}...")
    else:
        print(f"\n📸 Анализ изображений: ❌ Не работает")
    
    # STT
    stt_passed = [r for r in test_results if "STT" in r["component"] and r["status"] == "PASS"]
    if stt_passed:
        print(f"\n🎤 Распознавание голоса: ✅ Работает ({len(stt_passed)} сервисов)")
        for r in stt_passed:
            print(f"   • {r['component']}: {r['message'][:60]}...")
    else:
        print(f"\n🎤 Распознавание голоса: ❌ Не работает")
    
    # TTS
    tts_passed = [r for r in test_results if "TTS" in r["component"] and r["status"] == "PASS"]
    if tts_passed:
        print(f"\n🔊 Синтез речи: ✅ Работает ({len(tts_passed)} сервисов)")
        for r in tts_passed:
            print(f"   • {r['component']}: {r['message'][:60]}...")
    else:
        print(f"\n🔊 Синтез речи: ❌ Не работает")
    
    # Сохраняем отчёт
    report_path = Path.cwd() / "FUNCTIONAL_TEST_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🧪 LiraAI Functional Test Report\n\n")
        f.write(f"**Дата:** {datetime.now().isoformat()}\n\n")
        f.write("## 📊 Статистика\n\n")
        f.write(f"- Всего тестов: {total}\n")
        f.write(f"- ✅ Прошло: {passed}\n")
        f.write(f"- ❌ Не прошло: {failed}\n")
        f.write(f"- ⚠️ Пропущено: {skipped}\n\n")
        
        f.write("## 📋 Результаты\n\n")
        for r in test_results:
            status_icon = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⚠️"
            f.write(f"### {status_icon} {r['component']} - {r['test']}\n\n")
            f.write(f"**Статус:** {r['status']}\n\n")
            f.write(f"**Сообщение:** {r['message']}\n")
            if r.get("response_time"):
                f.write(f"**Время:** {r['response_time']:.2f}s\n")
            f.write("\n---\n\n")
        
        f.write("## 💡 Рекомендации\n\n")
        if vision_passed:
            f.write("### 📸 Анализ изображений\n\n")
            f.write("**Работает:**\n")
            for r in vision_passed:
                f.write(f"- {r['component']}\n")
            f.write("\n")
        
        if stt_passed:
            f.write("### 🎤 Распознавание голоса\n\n")
            f.write("**Работает:**\n")
            for r in stt_passed:
                f.write(f"- {r['component']}\n")
            f.write("\n")
        
        if tts_passed:
            f.write("### 🔊 Синтез речи\n\n")
            f.write("**Работает:**\n")
            for r in tts_passed:
                f.write(f"- {r['component']}\n")
            f.write("\n")
    
    print(f"\n📄 Полный отчёт: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
