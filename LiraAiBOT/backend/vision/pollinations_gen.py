"""
Pollinations Gen API клиент для генерации изображений.
Модели: nanobannana-pro, gptimage-large
"""
import asyncio
import logging
import os
import aiohttp
from typing import Optional
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

logger = logging.getLogger("bot.vision.pollinations_gen")


class PollinationsGenClient:
    """Клиент для работы с Pollinations Gen API"""

    def __init__(self):
        self.api_key = os.getenv("POLLINATIONS_GEN_API_KEY", "")
        self.base_url = os.getenv("POLLINATIONS_GEN_BASE_URL", "https://gen.pollinations.ai")

        # Доступные модели
        self.models = ["nanobannana-pro", "gptimage-large"]
        self.default_model = "nanobannana-pro"

        if self.api_key:
            logger.info(f"✅ Pollinations Gen клиент инициализирован")
        else:
            logger.warning("❌ POLLINATIONS_GEN_API_KEY не настроен")

    async def generate_image(
        self,
        prompt: str,
        model: str = None,
        timeout: int = 90
    ) -> Optional[bytes]:
        """
        Генерирует изображение через Pollinations Gen API
        """
        if not self.api_key:
            logger.error("❌ Pollinations Gen API ключ не настроен")
            return None

        model = model or self.default_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Пробуем разные endpoint'ы
        endpoints = [
            f"{self.base_url}/v1/images/generations",
            f"{self.base_url}/generate",
            f"{self.base_url}/api/v1/generate",
            f"{self.base_url}/image",
        ]

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        for endpoint in endpoints:
            try:
                logger.info(f"🎨 Pollinations Gen запрос к {endpoint}...")

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        result = await response.json()

                        if response.status == 200 and result.get("success"):
                            # Получаем URL изображения
                            image_url = result.get("data", [{}])[0].get("url")
                            if image_url:
                                logger.info(f"✅ Pollinations Gen изображение готово: {image_url}")

                                async with session.get(image_url) as img_response:
                                    if img_response.status == 200:
                                        image_data = await img_response.read()
                                        logger.info(f"✅ Pollinations Gen получено {len(image_data)} байт")
                                        return image_data

                            logger.error(f"❌ Pollinations Gen не получен URL: {result}")
                            return None
                        else:
                            error_msg = result.get("error", {}).get("message", str(result))
                            logger.warning(f"⚠️ Pollinations Gen ошибка {endpoint}: {error_msg}")
                            continue

            except Exception as e:
                logger.warning(f"⚠️ Pollinations Gen ошибка {endpoint}: {e}")
                continue

        logger.error("❌ Pollinations Gen все endpoint'ы не сработали")
        return None


# Глобальный экземпляр
_pollinations_gen_client: Optional[PollinationsGenClient] = None


def get_pollinations_gen_client() -> PollinationsGenClient:
    """Получает или создает клиент Pollinations Gen"""
    global _pollinations_gen_client
    if _pollinations_gen_client is None:
        _pollinations_gen_client = PollinationsGenClient()
    return _pollinations_gen_client
