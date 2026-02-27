import os
import json
import re
from typing import Dict, Any

import aiohttp

from .cache import WebCache


def _extract_urls(text: str):
    return re.findall(r"https?://\S+", text or "")


async def web_search(query: str, intent: str = "general", ttl_sec: int = 3600, require_fresh: bool = False) -> Dict[str, Any]:
    """Асинхронный запрос к Perplexity Sonar через OpenRouter. Возвращает текст и URL.

    Кэширование: простой SQLite-кэш поверх. Также пробрасываем metadata: {cache: true}.
    """
    cache = WebCache()
    cache_key = f"sonar::{intent}::{query.strip().lower()}"
    if ttl_sec > 0:
        cached = cache.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                data['cache_hit'] = True
                return data
            except Exception:
                pass

    # Используем платный ключ для Perplexity
    api_key = os.getenv("OPENROUTER_API_KEY_PAID") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"text": "", "urls": [], "error": "no_api_key", "cache_hit": False}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://liraai-multiassistent.local",
        "X-Title": "LiraAI MultiAssistent",
    }
    body = {
        "model": "perplexity/sonar",
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
            data=json.dumps(body),
            timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    return {"text": "", "urls": [], "error": f"http_{resp.status}", "cache_hit": False}
                data = await resp.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                urls = _extract_urls(text)
                result = {"text": text, "urls": urls, "error": None, "cache_hit": False}
                if ttl_sec > 0 and not require_fresh:
                    try:
                        cache.set(cache_key, json.dumps(result, ensure_ascii=False), ttl_sec)
                    except Exception:
                        pass
                return result
    except Exception as e:
        return {"text": "", "urls": [], "error": str(e), "cache_hit": False}

