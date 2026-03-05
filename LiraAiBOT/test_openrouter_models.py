#!/usr/bin/env python3
import aiohttp
import asyncio
import os
from dotenv import load_dotenv
load_dotenv(override=True)

async def test_models():
    api_key = os.getenv('OPENROUTER_API_KEY', '')
    
    models_to_test = [
        'arcee-ai/trinity-mini:free',
        'nvidia/nemotron-nano-9b-v2:free',
        'google/gemma-3n-e2b-it:free',
    ]
    
    async with aiohttp.ClientSession(
        headers={
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://github.com/LiraAiBotv1/LiraAiBOT',
            'X-Title': 'LiraAI Bot'
        }
    ) as session:
        for model in models_to_test:
            print(f"\n📍 Тест: {model}")
            try:
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    json={
                        'model': model,
                        'messages': [{'role': 'user', 'content': 'Привет! Как тебя зовут?'}],
                        'max_tokens': 100
                    }
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        if content:
                            print(f"✅ Ответ: {content[:80]}...")
                        else:
                            print(f"⚠️ Пустой ответ")
                    else:
                        print(f"❌ Ошибка: {resp.status}")
            except Exception as e:
                print(f"❌ Исключение: {e}")

asyncio.run(test_models())
