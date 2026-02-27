#!/usr/bin/env python3
"""
Тест Perplexity Sonar с веб-поиском через OpenRouter с платным ключом.
Проверяем что модель работает и возвращает актуальную информацию с ссылками.
"""

import os
import json
import re
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

# Загружаем .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Загружен .env файл: {env_path}")
except ImportError:
    print("⚠️ python-dotenv не установлен")
except Exception as e:
    print(f"⚠️ Ошибка загрузки .env: {e}")

def extract_urls(text: str):
    """Извлекает URL из текста"""
    return re.findall(r"https?://\S+", text or "")

async def perplexity_web_search(query: str, model: str = "perplexity/sonar"):
    """Асинхронный запрос к Perplexity через OpenRouter"""
    
    # Используем платный ключ
    api_key = os.getenv("OPENROUTER_API_KEY_PAID") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {
            "text": "",
            "urls": [],
            "error": "no_api_key",
            "success": False
        }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://liraai-multiassistent.local",
        "X-Title": "LiraAI MultiAssistent",
    }
    
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": query}]}
        ],
        "temperature": 0.0,
        "metadata": {"cache": True},
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    return {
                        "text": "",
                        "urls": [],
                        "error": f"http_{resp.status}: {error_text[:200]}",
                        "success": False
                    }
                
                data = await resp.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                urls = extract_urls(text)
                
                return {
                    "text": text,
                    "urls": urls,
                    "error": None,
                    "success": True
                }
    except Exception as e:
        return {
            "text": "",
            "urls": [],
            "error": str(e),
            "success": False
        }

async def test_perplexity():
    """Тестирует Perplexity с разными запросами"""
    
    print("=" * 70)
    print("🧪 ТЕСТ PERPLEXITY SONAR С ВЕБ-ПОИСКОМ")
    print("=" * 70)
    print()
    
    # Проверяем ключ
    paid_key = os.getenv("OPENROUTER_API_KEY_PAID")
    regular_key = os.getenv("OPENROUTER_API_KEY")
    
    if paid_key:
        print(f"✅ Найден платный ключ: {paid_key[:20]}...")
        used_key = "OPENROUTER_API_KEY_PAID"
    elif regular_key:
        print(f"⚠️ Платный ключ не найден, используем обычный: {regular_key[:20]}...")
        used_key = "OPENROUTER_API_KEY"
    else:
        print("❌ Нет ни одного ключа OpenRouter в .env!")
        return
    
    print(f"Используемый ключ: {used_key}")
    print()
    
    # Тестовые запросы
    tests = [
        {
            "name": "Текущая дата",
            "query": "Скажи текущую дату в формате YYYY-MM-DD. Укажи источники со ссылками.",
            "check_urls": True
        },
        {
            "name": "Погода сейчас",
            "query": "Какая сейчас погода в Москве? Приведи источники со ссылками и время обновления.",
            "check_urls": True
        },
        {
            "name": "Последние новости",
            "query": "Топ-3 новости России за сегодня. Дай краткие сводки и источники со ссылками.",
            "check_urls": True
        },
        {
            "name": "Технологические новости",
            "query": "Какие последние новости об искусственном интеллекте? Приведи источники.",
            "check_urls": True
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*70}")
        print(f"📋 ТЕСТ {i}/{len(tests)}: {test['name']}")
        print(f"{'='*70}")
        print(f"Запрос: {test['query']}")
        print()
        
        result = await perplexity_web_search(test['query'])
        
        if result['success']:
            print("✅ Успешно получен ответ")
            print()
            print("Ответ:")
            print("-" * 70)
            print(result['text'][:500] + ("..." if len(result['text']) > 500 else ""))
            print("-" * 70)
            
            if result['urls']:
                print(f"\n🔗 Найдено ссылок: {len(result['urls'])}")
                for url in result['urls'][:5]:  # Показываем первые 5
                    print(f"  • {url}")
                if len(result['urls']) > 5:
                    print(f"  ... и еще {len(result['urls']) - 5}")
            else:
                print("\n⚠️ Ссылки не найдены в ответе")
            
            results.append({
                "test": test['name'],
                "success": True,
                "has_urls": len(result['urls']) > 0,
                "urls_count": len(result['urls'])
            })
        else:
            print(f"❌ Ошибка: {result['error']}")
            results.append({
                "test": test['name'],
                "success": False,
                "error": result['error']
            })
        
        print()
        await asyncio.sleep(2)  # Пауза между запросами
    
    # Итоговая статистика
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    
    successful = sum(1 for r in results if r.get('success'))
    with_urls = sum(1 for r in results if r.get('has_urls'))
    
    print(f"✅ Успешных запросов: {successful}/{len(results)}")
    print(f"🔗 Запросов со ссылками: {with_urls}/{successful if successful > 0 else 0}")
    
    if successful == len(results) and with_urls == successful:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Perplexity работает с веб-поиском!")
    elif successful == len(results):
        print("\n⚠️ Все запросы успешны, но не все содержат ссылки")
    else:
        print("\n❌ Есть проблемы с запросами")

if __name__ == "__main__":
    asyncio.run(test_perplexity())

