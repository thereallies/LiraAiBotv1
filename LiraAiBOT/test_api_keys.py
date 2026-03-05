#!/usr/bin/env python3
"""
Тестирование API ключей и доступных моделей
LiraAI MultiAssistant - API Key Testing Suite
"""
import os
import sys
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

# Добавляем backend в path
sys.path.insert(0, str(Path.cwd() / 'backend'))

# Результаты тестов
test_results = []

def log_result(service, status, message, models=None):
    """Логирование результата теста"""
    result = {
        "service": service,
        "status": status,  # ✅ / ❌ / ⚠️
        "message": message,
        "models": models or [],
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    print(f"{status} {service}: {message}")
    if models:
        print(f"   Доступные модели: {len(models)}")
        for model in models[:5]:
            print(f"   • {model}")
        if len(models) > 5:
            print(f"   ... и ещё {len(models) - 5}")
    print()


# ============================================
# 1. OPENROUTER API TEST
# ============================================
async def test_openrouter():
    """Тестирование OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    if not api_key:
        log_result("OpenRouter", "❌", "API ключ не найден")
        return
    
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            # Получаем список моделей
            async with session.get("https://openrouter.ai/api/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    
                    # Фильтруем бесплатные модели
                    free_models = []
                    for model in models:
                        pricing = model.get("pricing", {})
                        if pricing.get("prompt", "0") == "0":
                            free_models.append({
                                "id": model.get("id"),
                                "name": model.get("name"),
                                "context_length": model.get("context_length")
                            })
                    
                    log_result(
                        "OpenRouter",
                        "✅",
                        f"API ключ действителен. Найдено {len(free_models)} бесплатных моделей",
                        [m["id"] for m in free_models[:20]]
                    )
                    return free_models
                else:
                    error = await response.text()
                    log_result("OpenRouter", "❌", f"Ошибка {response.status}: {error[:200]}")
    except Exception as e:
        log_result("OpenRouter", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# 2. GROQ API TEST
# ============================================
async def test_groq():
    """Тестирование Groq API"""
    api_key = os.getenv("GROQ_API_KEY", "")
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    
    if not api_key:
        log_result("Groq", "❌", "API ключ не найден")
        return
    
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            # Получаем список моделей
            async with session.get(f"{base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    model_ids = [m.get("id") for m in models]
                    
                    log_result(
                        "Groq",
                        "✅",
                        f"API ключ действителен. Найдено {len(models)} моделей",
                        model_ids
                    )
                    return model_ids
                else:
                    error = await response.text()
                    log_result("Groq", "❌", f"Ошибка {response.status}: {error[:200]}")
    except Exception as e:
        log_result("Groq", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# 3. CEREBRAS API TEST
# ============================================
async def test_cerebras():
    """Тестирование Cerebras API"""
    api_key = os.getenv("CEREBRAS_API_KEY", "")
    
    if not api_key:
        log_result("Cerebras", "❌", "API ключ не найден")
        return
    
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            # Получаем список моделей
            async with session.get("https://api.cerebras.ai/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    model_ids = [m.get("id") for m in models]
                    
                    log_result(
                        "Cerebras",
                        "✅",
                        f"API ключ действителен. Найдено {len(models)} моделей",
                        model_ids
                    )
                    return model_ids
                else:
                    error = await response.text()
                    log_result("Cerebras", "❌", f"Ошибка {response.status}: {error[:200]}")
    except Exception as e:
        log_result("Cerebras", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# 4. GOOGLE GEMINI API TEST
# ============================================
async def test_gemini():
    """Тестирование Google Gemini API"""
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key or api_key.startswith("AIza"):
        log_result("Google Gemini", "❌", "API ключ не найден или недействителен")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем список моделей
            async with session.get(
                f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    model_names = [m.get("name") for m in models]
                    
                    log_result(
                        "Google Gemini",
                        "✅",
                        f"API ключ действителен. Найдено {len(models)} моделей",
                        model_names
                    )
                    return model_names
                else:
                    error = await response.text()
                    log_result("Google Gemini", "❌", f"Ошибка {response.status}: {error[:200]}")
    except Exception as e:
        log_result("Google Gemini", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# 5. POLZA.AI API TEST
# ============================================
async def test_polza():
    """Тестирование Polza.ai API"""
    api_key = os.getenv("POLZA_API_KEY", "")
    
    if not api_key:
        log_result("Polza.ai", "❌", "API ключ не найден")
        return
    
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            # Тестовый запрос к API
            async with session.get("https://api.polza.ai/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    model_ids = [m.get("id") for m in models]
                    
                    log_result(
                        "Polza.ai",
                        "✅",
                        f"API ключ действителен. Найдено {len(models)} моделей",
                        model_ids
                    )
                    return model_ids
                else:
                    error = await response.text()
                    log_result("Polza.ai", "⚠️", f"API ключ есть, но ошибка {response.status}")
    except Exception as e:
        log_result("Polza.ai", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# 6. REPLICATE API TEST
# ============================================
async def test_replicate():
    """Тестирование Replicate API"""
    api_token = os.getenv("REPLICATE_API_TOKEN", "")
    
    if not api_token:
        log_result("Replicate", "❌", "API токен не найден")
        return
    
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Token {api_token}"}
        ) as session:
            # Получаем информацию о пользователе
            async with session.get("https://api.replicate.com/v1/account") as response:
                if response.status == 200:
                    data = await response.json()
                    username = data.get("username", "unknown")
                    log_result("Replicate", "✅", f"API токен действителен (пользователь: {username})")
                    return True
                else:
                    error = await response.text()
                    log_result("Replicate", "❌", f"Ошибка {response.status}: {error[:200]}")
    except Exception as e:
        log_result("Replicate", "❌", f"Ошибка подключения: {e}")
    
    return False


# ============================================
# 7. SILICONFLOW API TEST
# ============================================
async def test_siliconflow():
    """Тестирование SiliconFlow API"""
    api_key = os.getenv("SILICONFLOW_API_KEY", "")
    base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    
    if not api_key:
        log_result("SiliconFlow", "❌", "API ключ не найден")
        return
    
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            # Получаем список моделей
            async with session.get(f"{base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    model_ids = [m.get("id") for m in models]
                    
                    log_result(
                        "SiliconFlow",
                        "✅",
                        f"API ключ действителен. Найдено {len(models)} моделей",
                        model_ids[:20]
                    )
                    return model_ids
                else:
                    error = await response.text()
                    log_result("SiliconFlow", "❌", f"Ошибка {response.status}: {error[:200]}")
    except Exception as e:
        log_result("SiliconFlow", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# 8. POLLINATIONS API TEST
# ============================================
async def test_pollinations():
    """Тестирование Pollinations API"""
    api_key = os.getenv("POLLINATIONS_GEN_API_KEY", "")
    base_url = os.getenv("POLLINATIONS_GEN_BASE_URL", "https://gen.pollinations.ai")
    
    if not api_key:
        log_result("Pollinations", "❌", "API ключ не найден")
        return
    
    try:
        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"}
        ) as session:
            # Тестовый запрос
            async with session.get(f"{base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data if isinstance(data, list) else []
                    model_ids = [m.get("id", str(m)) for m in models] if models else ["default"]
                    
                    log_result(
                        "Pollinations",
                        "✅",
                        f"API ключ действителен. Найдено {len(model_ids)} моделей",
                        model_ids
                    )
                    return model_ids
                else:
                    log_result("Pollinations", "⚠️", f"API ключ есть, но endpoint недоступен")
    except Exception as e:
        log_result("Pollinations", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# 9. KIE.AI API TEST
# ============================================
async def test_kie():
    """Тестирование KIE.AI API"""
    api_key = os.getenv("KIE_API_KEY", "")
    
    if not api_key:
        log_result("KIE.AI", "❌", "API ключ не найден")
        return
    
    try:
        # KIE.AI использует простой API ключ в заголовке
        async with aiohttp.ClientSession(
            headers={"X-API-Key": api_key}
        ) as session:
            # Тестовый запрос (предполагаемый endpoint)
            async with session.get("https://api.kie.ai/v1/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("data", [])
                    model_ids = [m.get("id") for m in models]
                    
                    log_result(
                        "KIE.AI",
                        "✅",
                        f"API ключ действителен. Найдено {len(models)} моделей",
                        model_ids
                    )
                    return model_ids
                else:
                    log_result("KIE.AI", "⚠️", f"API ключ есть, но endpoint недоступен ({response.status})")
    except Exception as e:
        log_result("KIE.AI", "❌", f"Ошибка подключения: {e}")
    
    return []


# ============================================
# MAIN
# ============================================
async def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("🔑 LiraAI API Key Testing Suite")
    print("=" * 60)
    print()
    
    # Загружаем .env
    from dotenv import load_dotenv
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл: {env_path}")
    else:
        print(f"❌ .env файл не найден: {env_path}")
        return
    
    print()
    print("-" * 60)
    print("🧪 Запуск тестов API ключей...")
    print("-" * 60)
    print()
    
    # Запускаем все тесты
    await test_openrouter()
    await test_groq()
    await test_cerebras()
    await test_gemini()
    await test_polza()
    await test_replicate()
    await test_siliconflow()
    await test_pollinations()
    await test_kie()
    
    # Генерируем отчёт
    print()
    print("=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 60)
    
    # Считаем статистику
    total = len(test_results)
    success = sum(1 for r in test_results if r["status"] == "✅")
    warning = sum(1 for r in test_results if r["status"] == "⚠️")
    failed = sum(1 for r in test_results if r["status"] == "❌")
    
    print(f"\nВсего сервисов: {total}")
    print(f"✅ Работают: {success}")
    print(f"⚠️ Частично: {warning}")
    print(f"❌ Не работают: {failed}")
    
    # Рекомендации
    print("\n" + "=" * 60)
    print("💡 РЕКОМЕНДАЦИИ")
    print("=" * 60)
    
    # Собираем все бесплатные модели
    all_free_models = []
    for result in test_results:
        if result["status"] == "✅" and result.get("models"):
            all_free_models.extend(result["models"])
    
    print(f"\n📚 Всего доступно моделей: {len(all_free_models)}")
    
    # Топ рекомендаций
    print("\n🏆 Топ рекомендаций:")
    print("1. Groq - самые быстрые бесплатные модели (Llama 3.3, Llama 4)")
    print("2. Cerebras - сверхбыстрые модели (Llama 3.1 8B)")
    print("3. OpenRouter - много бесплатных моделей (Solar, Trinity, GLM)")
    print("4. Polza.ai - бесплатная генерация изображений (Z-Image)")
    
    # Сохраняем отчёт
    report_path = Path.cwd() / "API_TEST_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 🔑 LiraAI API Key Test Report\n\n")
        f.write(f"**Дата:** {datetime.now().isoformat()}\n\n")
        f.write("## 📊 Статистика\n\n")
        f.write(f"- Всего сервисов: {total}\n")
        f.write(f"- ✅ Работают: {success}\n")
        f.write(f"- ⚠️ Частично: {warning}\n")
        f.write(f"- ❌ Не работают: {failed}\n\n")
        
        f.write("## 🧪 Результаты тестов\n\n")
        for result in test_results:
            f.write(f"### {result['service']}\n\n")
            f.write(f"**Статус:** {result['status']}\n\n")
            f.write(f"**Сообщение:** {result['message']}\n\n")
            if result.get("models"):
                f.write(f"**Модели:**\n")
                for model in result["models"]:
                    f.write(f"- `{model}`\n")
            f.write("\n---\n\n")
        
        f.write("## 💡 Рекомендации\n\n")
        f.write("1. **Groq** - самые быстрые бесплатные модели\n")
        f.write("2. **Cerebras** - сверхбыстрые модели\n")
        f.write("3. **OpenRouter** - много бесплатных моделей\n")
        f.write("4. **Polza.ai** - бесплатная генерация изображений\n")
    
    print(f"\n📄 Отчёт сохранён: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
