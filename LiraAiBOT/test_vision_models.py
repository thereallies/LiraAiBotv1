#!/usr/bin/env python3
"""
Тестирование Vision моделей для ImageAnalyzer:
1. Groq Vision
2. Cerebras Vision
3. OpenRouter Vision
"""
import os
import sys
import asyncio
import aiohttp
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Результаты тестов
test_results = []

def log_result(service, model, status, message, response_time=None):
    """Логирование результата теста"""
    result = {
        "service": service,
        "model": model,
        "status": status,
        "message": message,
        "response_time": response_time,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    time_str = f" ({response_time:.2f}s)" if response_time else ""
    print(f"  {status_icon} {model}: {message}{time_str}")


async def test_groq_vision(api_key, image_base64):
    """Тест Groq Vision API"""
    if not api_key:
        log_result("Groq Vision", "meta-llama/llama-3.2-90b-vision-preview", "SKIP", "Нет API ключа")
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
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
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
                        log_result("Groq Vision", "meta-llama/llama-3.2-90b-vision-preview", "PASS", f"Ответ: {content[:60]}...", elapsed)
                        return True
                    else:
                        log_result("Groq Vision", "meta-llama/llama-3.2-90b-vision-preview", "FAIL", "Пустой ответ", elapsed)
                else:
                    error = await response.text()
                    log_result("Groq Vision", "meta-llama/llama-3.2-90b-vision-preview", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("Groq Vision", "meta-llama/llama-3.2-90b-vision-preview", "FAIL", f"Исключение: {e}")
    
    return False


async def test_cerebras_vision(api_key, image_base64):
    """Тест Cerebras Vision API"""
    if not api_key:
        log_result("Cerebras Vision", "llama-3.3-70b-instruct", "SKIP", "Нет API ключа")
        return False
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            async with session.post(
                "https://api.cerebras.ai/v1/chat/completions",
                json={
                    "model": "llama-3.3-70b-instruct",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Что изображено на этой картинке? Ответь на русском."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
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
                        log_result("Cerebras Vision", "llama-3.3-70b-instruct", "PASS", f"Ответ: {content[:60]}...", elapsed)
                        return True
                    else:
                        log_result("Cerebras Vision", "llama-3.3-70b-instruct", "FAIL", "Пустой ответ", elapsed)
                else:
                    error = await response.text()
                    log_result("Cerebras Vision", "llama-3.3-70b-instruct", "FAIL", f"Ошибка {response.status}: {error[:100]}", elapsed)
    except Exception as e:
        log_result("Cerebras Vision", "llama-3.3-70b-instruct", "FAIL", f"Исключение: {e}")
    
    return False


async def test_openrouter_vision(api_key, image_base64):
    """Тест OpenRouter Vision API"""
    if not api_key:
        log_result("OpenRouter Vision", "Несколько моделей", "SKIP", "Нет API ключа")
        return False
    
    # Vision модели на OpenRouter
    vision_models = [
        "nvidia/nemotron-nano-12b-v2-vl:free",
        "qwen/qwen3-vl-30b-a3b-thinking:free",
        "qwen/qwen3-vl-235b-a22b-thinking:free",
        "google/gemma-3n-e2b-it:free",
    ]
    
    async with aiohttp.ClientSession(
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/LiraAiBotv1/LiraAiBOT",
            "X-Title": "LiraAI Bot"
        }
    ) as session:
        for model in vision_models:
            try:
                start_time = asyncio.get_event_loop().time()
                
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Что изображено на этой картинке? Ответь на русском."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
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
                            log_result("OpenRouter Vision", model, "PASS", f"Ответ: {content[:60]}...", elapsed)
                            return True
                        else:
                            log_result("OpenRouter Vision", model, "FAIL", "Пустой ответ", elapsed)
                    else:
                        error = await response.text()
                        log_result("OpenRouter Vision", model, "FAIL", f"Ошибка {response.status}: {error[:80]}", elapsed)
            except Exception as e:
                log_result("OpenRouter Vision", model, "FAIL", f"Исключение: {e}")
    
    return False


async def main():
    """Запуск всех тестов"""
    print("=" * 70)
    print("👁️ LiraAI Vision Models Testing Suite")
    print("   ImageAnalyzer - Groq • Cerebras • OpenRouter")
    print("=" * 70)
    print()
    
    # API ключи
    groq_key = os.getenv("GROQ_API_KEY", "")
    cerebras_key = os.getenv("CEREBRAS_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    
    print("-" * 70)
    print("📋 API Ключи:")
    print(f"   Groq: {'✅' if groq_key else '❌'}")
    print(f"   Cerebras: {'✅' if cerebras_key else '❌'}")
    print(f"   OpenRouter: {'✅' if openrouter_key else '❌'}")
    print("-" * 70)
    print()
    
    # Загружаем тестовое изображение
    test_image_url = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400"
    
    print("📥 Загрузка тестового изображения...")
    try:
        async with aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0"}
        ) as session:
            async with session.get(test_image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_base64 = base64.b64encode(image_data).decode()
                    print(f"✅ Изображение загружено: {len(image_data)} байт")
                else:
                    print(f"❌ Не удалось загрузить изображение: {response.status}")
                    return
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return
    
    print()
    print("-" * 70)
    print("🧪 ТЕСТ: Анализ изображений (Vision)")
    print("-" * 70)
    print()
    
    # Запускаем тесты
    await test_groq_vision(groq_key, image_base64)
    await test_cerebras_vision(cerebras_key, image_base64)
    await test_openrouter_vision(openrouter_key, image_base64)
    
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
    print("💡 РЕКОМЕНДАЦИИ ДЛЯ ImageAnalyzer")
    print("=" * 70)
    
    vision_passed = [r for r in test_results if r["status"] == "PASS"]
    if vision_passed:
        print(f"\n✅ Рабочие Vision модели ({len(vision_passed)}):")
        for r in vision_passed:
            print(f"   • {r['service']}: {r['model']}")
    else:
        print(f"\n❌ Vision модели не работают")
    
    # Сохраняем отчёт
    report_path = Path.cwd() / "VISION_TEST_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 👁️ LiraAI Vision Models Test Report\n\n")
        f.write(f"**Дата:** {datetime.now().isoformat()}\n\n")
        f.write("## 📊 Статистика\n\n")
        f.write(f"- Всего тестов: {total}\n")
        f.write(f"- ✅ Прошло: {passed}\n")
        f.write(f"- ❌ Не прошло: {failed}\n")
        f.write(f"- ⚠️ Пропущено: {skipped}\n\n")
        
        f.write("## 📋 Результаты\n\n")
        for r in test_results:
            status_icon = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⚠️"
            f.write(f"### {status_icon} {r['service']} - {r['model']}\n\n")
            f.write(f"**Статус:** {r['status']}\n\n")
            f.write(f"**Сообщение:** {r['message']}\n")
            if r.get("response_time"):
                f.write(f"**Время:** {r['response_time']:.2f}s\n")
            f.write("\n---\n\n")
        
        f.write("## 💡 Рекомендации для ImageAnalyzer\n\n")
        f.write("### Текущая конфигурация\n\n")
        f.write("```python\n")
        f.write("# backend/vision/image_analyzer.py\n")
        f.write("self.groq_model = \"meta-llama/llama-3.2-90b-vision-preview\"\n")
        f.write("self.cerebras_model = \"llama-3.3-70b-instruct\"\n")
        f.write("self.openrouter_models = [\n")
        f.write("    \"nvidia/nemotron-nano-12b-v2-vl:free\",\n")
        f.write("    \"qwen/qwen3-vl-30b-a3b-thinking:free\",\n")
        f.write("    \"qwen/qwen3-vl-235b-a22b-thinking:free\",\n")
        f.write("]\n")
        f.write("```\n\n")
        
        if vision_passed:
            f.write("### ✅ Рабочие модели\n\n")
            for r in vision_passed:
                f.write(f"- **{r['service']}**: `{r['model']}`\n")
            f.write("\n### 🔧 Обновлённая конфигурация\n\n")
            f.write("```python\n")
            f.write("# Обновить backend/vision/image_analyzer.py\n")
            f.write("self.groq_model = \"groq/llama-3.2-90b-vision-preview\"  # Проверить наличие\n")
            f.write("self.openrouter_models = [\n")
            for r in vision_passed:
                if "OpenRouter" in r["service"]:
                    f.write(f"    \"{r['model']}\",  # ✅ Работает\n")
            f.write("]\n")
            f.write("```\n")
        else:
            f.write("### ❌ Нет рабочих моделей\n\n")
            f.write("**Рекомендация:** Использовать Gemini Vision через Polza.ai или напрямую\n")
    
    print(f"\n📄 Полный отчёт: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
