"""
Groq API клиент.
Быстрые бесплатные модели.
"""
import asyncio
import logging
import os
from typing import Optional, Any
import aiohttp

logger = logging.getLogger("bot.llm")


class GroqClient:
    """Клиент для работы с Groq API"""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        
        # Параметры по умолчанию
        self.default_model = "meta-llama/llama-3.3-70b-versatile"
        self.max_tokens = 2048
        self.temperature = 0.7

        if self.api_key:
            logger.info(f"✅ Groq клиент инициализирован: {self.base_url}")
        else:
            logger.warning("❌ GROQ_API_KEY не настроен")

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

        logger.info(f"🚀 Groq запрос: {model}, max_tokens={max_tokens}")

        # Прокси для обхода блокировок (если настроен)
        groq_proxy = os.getenv("GROQ_PROXY", "")
        proxy = groq_proxy if groq_proxy else None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                    proxy=proxy
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        logger.info(f"✅ Groq ответ получен: {len(content)} символов")
                        return content
                    elif response.status == 403:
                        error_text = await response.text()
                        logger.error(f"❌ Groq 403 Forbidden: {error_text}")
                        logger.error("⚠️ Возможно, ваш IP заблокирован. Используйте прокси (GROQ_PROXY)")
                        raise Exception(f"Groq error 403: {error_text}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Groq error {response.status}: {error_text}")
                        raise Exception(f"Groq error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к Groq: {e}")
            raise


# Глобальный экземпляр
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Получает или создает клиент Groq"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
