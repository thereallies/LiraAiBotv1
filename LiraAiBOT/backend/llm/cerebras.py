"""
Cerebras API клиент.
Очень быстрый инференс LLM (альтернатива Groq).
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Any
import aiohttp
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

logger = logging.getLogger("bot.llm")


class CerebrasClient:
    """Клиент для работы с Cerebras API"""

    def __init__(self):
        self.api_key = os.getenv("CEREBRAS_API_KEY", "")
        self.base_url = "https://api.cerebras.ai/v1"

        # Параметры по умолчанию
        self.default_model = "llama3.1-8b"
        self.available_models = {
            "cerebras-llama": "llama3.1-8b",
            "cerebras-gpt": "gpt-oss-120b",
        }
        self.max_tokens = 2048
        self.temperature = 0.7

        if self.api_key:
            logger.info(f"✅ Cerebras клиент инициализирован: {self.base_url}")
        else:
            logger.warning("❌ CEREBRAS_API_KEY не настроен")

    async def chat_completion(
        self,
        user_message: str,
        system_prompt: str = "",
        chat_history: Optional[list] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Генерирует ответ через chat completion API"""

        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        # Формируем сообщения
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": user_message})

        # Формируем запрос
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"🚀 Cerebras запрос: {model}, max_tokens={max_tokens}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"✅ Cerebras ответ получен: {len(content)} символов")
                        return content
                    elif response.status == 403:
                        error_text = await response.text()
                        logger.error(f"❌ Cerebras 403 Forbidden: {error_text}")
                        raise Exception(f"Cerebras error 403: {error_text}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Cerebras error {response.status}: {error_text}")
                        raise Exception(f"Cerebras error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к Cerebras: {e}")
            raise


# Глобальный экземпляр
_cerebras_client: Optional[CerebrasClient] = None


def get_cerebras_client() -> CerebrasClient:
    """Получает или создает клиент Cerebras"""
    global _cerebras_client
    if _cerebras_client is None:
        _cerebras_client = CerebrasClient()
    return _cerebras_client
