#!/usr/bin/env python3
"""
Тестирование бесплатных моделей: Groq, OpenRouter, Cerebras
LiraAI Free Models Testing Suite

Функционал для тестирования:
1. Текстовый чат (русский язык)
2. Генерация изображений (описание)
3. Анализ изображений (описание)
4. Распознавание голоса (транскрипция)
"""
import os
import sys
import asyncio
import aiohttp
import time
from datetime import datetime
from pathlib import Path

# Добавляем backend в path
sys.path.insert(0, str(Path.cwd() / 'backend'))

# Результаты тестов
test_results = []
working_models = {
    "text_chat": [],
    "image_generation": [],
    "image_analysis": [],
    "voice_transcription": []
}

def log_result(service, model, test_type, status, message, response_time=None):
    """Логирование результата теста"""
    result = {
        "service": service,
        "model": model,
        "test_type": test_type,
        "status": status,
        "message": message,
        "response_time": response_time,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    time_str = f" ({response_time:.2f}s)" if response_time else ""
    print(f"  {status_icon} {model}: {message}{time_str}")
    
    if status == "PASS" and test_type in working_models:
        if model not in working_models[test_type]:
            working_models[test_type].append(model)


# ============================================
# ТЕСТ 1: ТЕКСТОВЫЙ ЧАТ (РУССКИЙ ЯЗЫК)
# ============================================
async def test_text_chat_groq(session, model, api_key):
    """Тест текстового чата на Groq"""
    try:
        start_time = time.time()
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."},
                    {"role": "user", "content": "Привет! Как тебя зовут?"}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
        ) as response:
            elapsed = time.time() - start_time
            if response.status == 200:
                data = await response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and len(content) > 10:
                    log_result("Groq", model, "text_chat", "PASS", f"Ответ: {content[:50]}...", elapsed)
                    return True
                else:
                    log_result("Groq", model, "text_chat", "FAIL", "Пустой ответ", elapsed)
            else:
                error = await response.text()
                log_result("Groq", model, "text_chat", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("Groq", model, "text_chat", "FAIL", f"Исключение: {e}")
    return False


async def test_text_chat_openrouter(session, model, api_key):
    """Тест текстового чата на OpenRouter"""
    try:
        start_time = time.time()
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/LiraAiBotv1/LiraAiBOT"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."},
                    {"role": "user", "content": "Привет! Как тебя зовут?"}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
        ) as response:
            elapsed = time.time() - start_time
            if response.status == 200:
                data = await response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and len(content) > 10:
                    log_result("OpenRouter", model, "text_chat", "PASS", f"Ответ: {content[:50]}...", elapsed)
                    return True
                else:
                    log_result("OpenRouter", model, "text_chat", "FAIL", "Пустой ответ", elapsed)
            else:
                error = await response.text()
                log_result("OpenRouter", model, "text_chat", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("OpenRouter", model, "text_chat", "FAIL", f"Исключение: {e}")
    return False


async def test_text_chat_cerebras(session, model, api_key):
    """Тест текстового чата на Cerebras"""
    try:
        start_time = time.time()
        async with session.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."},
                    {"role": "user", "content": "Привет! Как тебя зовут?"}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
        ) as response:
            elapsed = time.time() - start_time
            if response.status == 200:
                data = await response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and len(content) > 10:
                    log_result("Cerebras", model, "text_chat", "PASS", f"Ответ: {content[:50]}...", elapsed)
                    return True
                else:
                    log_result("Cerebras", model, "text_chat", "FAIL", "Пустой ответ", elapsed)
            else:
                error = await response.text()
                log_result("Cerebras", model, "text_chat", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("Cerebras", model, "text_chat", "FAIL", f"Исключение: {e}")
    return False


# ============================================
# ТЕСТ 2: ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ (ОПИСАНИЕ)
# ============================================
async def test_image_generation_openrouter(session, model, api_key):
    """Тест генерации изображений через OpenRouter (если модель поддерживает)"""
    # OpenRouter не поддерживает генерацию изображений напрямую
    log_result("OpenRouter", model, "image_generation", "SKIP", "Не поддерживает генерацию изображений")
    return None


# ============================================
# ТЕСТ 3: АНАЛИЗ ИЗОБРАЖЕНИЙ (VISION)
# ============================================
async def test_vision_openrouter(session, model, api_key):
    """Тест анализа изображений на OpenRouter"""
    # Тестовое изображение (URL)
    test_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/320px-Cat_November_2010-1a.jpg"
    
    try:
        start_time = time.time()
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/LiraAiBotv1/LiraAiBOT"
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Что изображено на этой картинке? Ответь на русском."},
                            {"type": "image_url", "image_url": {"url": test_image_url}}
                        ]
                    }
                ],
                "max_tokens": 200
            }
        ) as response:
            elapsed = time.time() - start_time
            if response.status == 200:
                data = await response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and len(content) > 10:
                    log_result("OpenRouter", model, "image_analysis", "PASS", f"Ответ: {content[:50]}...", elapsed)
                    return True
                else:
                    log_result("OpenRouter", model, "image_analysis", "FAIL", "Пустой ответ", elapsed)
            elif response.status == 400:
                log_result("OpenRouter", model, "image_analysis", "SKIP", "Не поддерживает vision", elapsed)
            else:
                error = await response.text()
                log_result("OpenRouter", model, "image_analysis", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("OpenRouter", model, "image_analysis", "FAIL", f"Исключение: {e}")
    return False


# ============================================
# ТЕСТ 4: РАСПОЗНАВАНИЕ ГОЛОСА (STT)
# ============================================
async def test_stt_groq(session, model, api_key):
    """Тест распознавания голоса на Groq (Whisper)"""
    # Groq поддерживает Whisper для STT
    if "whisper" not in model.lower():
        log_result("Groq", model, "voice_transcription", "SKIP", "Не STT модель")
        return None
    
    # Для полноценного теста нужен аудиофайл, пропускаем
    log_result("Groq", model, "voice_transcription", "SKIP", "Требуется аудиофайл для теста")
    return None


# ============================================
# ПОЛУЧЕНИЕ СПИСКА МОДЕЛЕЙ
# ============================================
async def get_groq_models(api_key):
    """Получение списка моделей Groq"""
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            async with session.get("https://api.groq.com/openai/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    # Фильтруем только текстовые модели (не STT)
                    text_models = [
                        m.get("id") for m in models 
                        if "whisper" not in m.get("id", "").lower()
                        and "guard" not in m.get("id", "").lower()
                    ]
                    return text_models
    except Exception as e:
        print(f"❌ Ошибка получения списка моделей Groq: {e}")
    return []


async def get_openrouter_free_models(api_key):
    """Получение списка бесплатных моделей OpenRouter"""
    try:
        async with aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/LiraAiBotv1/LiraAiBOT"
            }
        ) as session:
            async with session.get("https://openrouter.ai/api/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    # Фильтруем бесплатные модели
                    free_models = []
                    for model in models:
                        pricing = model.get("pricing", {})
                        if pricing.get("prompt", "0") == "0":
                            model_id = model.get("id", "")
                            # Исключаем специализированные модели
                            if not any(x in model_id.lower() for x in ["embedding", "tts", "speech", "image"]):
                                free_models.append(model_id)
                    return free_models
    except Exception as e:
        print(f"❌ Ошибка получения списка моделей OpenRouter: {e}")
    return []


async def get_cerebras_models(api_key):
    """Получение списка моделей Cerebras"""
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            async with session.get("https://api.cerebras.ai/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    model_ids = [m.get("id") for m in models]
                    return model_ids
    except Exception as e:
        print(f"❌ Ошибка получения списка моделей Cerebras: {e}")
    return []


# ============================================
# MAIN
# ============================================
async def main():
    """Запуск всех тестов"""
    print("=" * 70)
    print("🆓 LiraAI Free Models Testing Suite")
    print("   Groq • OpenRouter • Cerebras")
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
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    cerebras_key = os.getenv("CEREBRAS_API_KEY", "")
    
    print()
    print("-" * 70)
    print("📋 API Ключи:")
    print(f"   Groq: {'✅' if groq_key else '❌'}")
    print(f"   OpenRouter: {'✅' if openrouter_key else '❌'}")
    print(f"   Cerebras: {'✅' if cerebras_key else '❌'}")
    print("-" * 70)
    print()
    
    # Получаем списки моделей
    print("🔍 Получение списков моделей...")
    print()
    
    groq_models = await get_groq_models(groq_key) if groq_key else []
    openrouter_models = await get_openrouter_free_models(openrouter_key) if openrouter_key else []
    cerebras_models = await get_cerebras_models(cerebras_key) if cerebras_key else []
    
    print(f"   Groq: {len(groq_models)} моделей")
    print(f"   OpenRouter: {len(openrouter_models)} бесплатных моделей")
    print(f"   Cerebras: {len(cerebras_models)} моделей")
    print()
    
    # Запускаем тесты
    print("-" * 70)
    print("🧪 ТЕСТ 1: Текстовый чат (русский язык)")
    print("-" * 70)
    
    async with aiohttp.ClientSession() as session:
        # Тестируем Groq
        if groq_key and groq_models:
            print("\n📍 Groq модели:")
            for model in groq_models[:10]:  # Ограничиваем количество
                await test_text_chat_groq(session, model, groq_key)
        
        # Тестируем OpenRouter
        if openrouter_key and openrouter_models:
            print("\n📍 OpenRouter модели (бесплатные):")
            for model in openrouter_models[:15]:  # Ограничиваем количество
                await test_text_chat_openrouter(session, model, openrouter_key)
        
        # Тестируем Cerebras
        if cerebras_key and cerebras_models:
            print("\n📍 Cerebras модели:")
            for model in cerebras_models:
                await test_text_chat_cerebras(session, model, cerebras_key)
    
    print()
    print("-" * 70)
    print("🧪 ТЕСТ 2: Анализ изображений (Vision)")
    print("-" * 70)
    
    async with aiohttp.ClientSession() as session:
        # Тестируем OpenRouter vision модели
        if openrouter_key and openrouter_models:
            print("\n📍 OpenRouter модели (vision):")
            vision_models = [m for m in openrouter_models if any(x in m.lower() for x in ["vision", "vl", "4o"])]
            for model in vision_models[:5]:
                await test_vision_openrouter(session, model, openrouter_key)
    
    print()
    print("=" * 70)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 70)
    
    # Считаем статистику
    total_tests = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    skipped = sum(1 for r in test_results if r["status"] == "SKIP")
    
    print(f"\nВсего тестов: {total_tests}")
    print(f"✅ Прошло: {passed}")
    print(f"❌ Не прошло: {failed}")
    print(f"⚠️ Пропущено: {skipped}")
    
    # Топ работающих моделей
    print("\n" + "=" * 70)
    print("🏆 ТОП РАБОТАЮЩИХ МОДЕЛЕЙ (Текстовый чат)")
    print("=" * 70)
    
    if working_models["text_chat"]:
        print("\n📍 Groq:")
        for model in working_models["text_chat"][:5]:
            if model in groq_models:
                print(f"   ✅ {model}")
        
        print("\n📍 OpenRouter (бесплатные):")
        for model in working_models["text_chat"][:10]:
            if model in openrouter_models:
                print(f"   ✅ {model}")
        
        print("\n📍 Cerebras:")
        for model in working_models["text_chat"]:
            if model in cerebras_models:
                print(f"   ✅ {model}")
    
    # Рекомендации
    print("\n" + "=" * 70)
    print("💡 РЕКОМЕНДАЦИИ ДЛЯ LiraAI")
    print("=" * 70)
    
    print("\n🔹 Основная модель (текст):")
    if working_models["text_chat"]:
        # Выбираем первую работающую Groq модель
        for model in working_models["text_chat"]:
            if "llama-3.3-70b" in model:
                print(f"   🥇 Groq: {model}")
                break
        else:
            print(f"   🥇 Groq: {working_models['text_chat'][0]}")
    
    print("\n🔹 Fallback 1 (быстрая):")
    for model in working_models["text_chat"]:
        if "cerebras" in model.lower() or "llama3.1-8b" in model:
            print(f"   🥈 Cerebras: {model}")
            break
    
    print("\n🔹 Fallback 2 (бесплатная):")
    for model in working_models["text_chat"]:
        if ":free" in model or "glm-4.5" in model.lower():
            print(f"   🥉 OpenRouter: {model}")
            break
    
    # Сохраняем отчёт
    report_path = Path.cwd() / "FREE_MODELS_TEST_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🆓 LiraAI Free Models Test Report\n\n")
        f.write(f"**Дата:** {datetime.now().isoformat()}\n\n")
        f.write("## 📊 Статистика\n\n")
        f.write(f"- Всего тестов: {total_tests}\n")
        f.write(f"- ✅ Прошло: {passed}\n")
        f.write(f"- ❌ Не прошло: {failed}\n")
        f.write(f"- ⚠️ Пропущено: {skipped}\n\n")
        
        f.write("## 🏆 Работающие модели\n\n")
        f.write("### Текстовый чат\n\n")
        for model in working_models["text_chat"]:
            f.write(f"- `{model}`\n")
        
        f.write("\n### Анализ изображений\n\n")
        for model in working_models["image_analysis"]:
            f.write(f"- `{model}`\n")
        
        f.write("\n## 💡 Рекомендации\n\n")
        f.write("```python\n")
        f.write("FALLBACK_SEQUENCE = [\n")
        if working_models["text_chat"]:
            f.write(f'    {{"provider": "groq", "model": "{working_models["text_chat"][0]}"}},\n')
            if len(working_models["text_chat"]) > 1:
                f.write(f'    {{"provider": "groq", "model": "{working_models["text_chat"][1]}"}},\n')
            if len(working_models["text_chat"]) > 2:
                f.write(f'    {{"provider": "openrouter", "model": "{working_models["text_chat"][2]}"}},\n')
        f.write("]\n")
        f.write("```\n")
    
    print(f"\n📄 Полный отчёт: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
