"""
Replicate API клиент для генерации изображений.
Используем бесплатные модели: Google Nano Banana 2
"""
import asyncio
import logging
import os
import time
import aiohttp
from typing import Optional

logger = logging.getLogger("bot.vision.replicate")


class ReplicateClient:
    """Клиент для работы с Replicate API"""

    def __init__(self):
        self.api_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.base_url = "https://api.replicate.com/v1"

        # Google Nano Banana 2 - бесплатная модель!
        self.model = "google/nano-banana-2"

        if self.api_token:
            logger.info(f"✅ Replicate клиент инициализирован (Google Nano Banana 2)")
        else:
            logger.warning("❌ REPLICATE_API_TOKEN не настроен")

    async def generate_image(
        self,
        prompt: str,
        timeout: int = 90
    ) -> Optional[bytes]:
        """
        Генерирует изображение через Replicate API (Google Nano Banana 2)
        """
        if not self.api_token:
            logger.error("❌ Replicate API токен не настроен")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Prefer": "wait"  # Ждем завершения
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Создаем предсказание через правильный endpoint
                pred_url = f"{self.base_url}/models/{self.model}/predictions"
                payload = {
                    "input": {
                        "prompt": prompt,
                        "aspect_ratio": "1:1",
                        "output_format": "jpg"
                    }
                }

                logger.info(f"🎨 Replicate Nano Banana 2 запрос: {prompt[:50]}...")

                async with session.post(pred_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 201:
                        error = await response.text()
                        logger.error(f"❌ Replicate ошибка: {response.status} - {error}")
                        return None

                    pred_data = await response.json()
                    pred_id = pred_data.get("id")

                    if not pred_id:
                        logger.error("❌ Не получен prediction ID")
                        return None

                    logger.info(f"🎨 Replicate Prediction ID: {pred_id}")

                    # Ждем завершения (опрос)
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        await asyncio.sleep(2)

                        check_url = f"{self.base_url}/predictions/{pred_id}"
                        async with session.get(check_url, headers=headers) as check_response:
                            if check_response.status == 200:
                                check_data = await check_response.json()
                                status = check_data.get("status")

                                if status == "succeeded":
                                    output_url = check_data.get("output")
                                    if output_url:
                                        logger.info(f"✅ Replicate изображение готово: {output_url}")

                                        async with session.get(output_url) as img_response:
                                            if img_response.status == 200:
                                                image_data = await img_response.read()
                                                logger.info(f"✅ Replicate получено {len(image_data)} байт")
                                                return image_data

                                    logger.error("❌ Не получен URL")
                                    return None
                                elif status in ["failed", "canceled"]:
                                    logger.error(f"❌ Replicate ошибка: {status}")
                                    return None
                            else:
                                logger.warning(f"⚠️ Статус проверки: {check_response.status}")

                    logger.error(f"❌ Replicate таймаут")
                    return None

        except asyncio.TimeoutError:
            logger.error("❌ Replicate таймаут")
            return None
        except Exception as e:
            logger.error(f"❌ Replicate ошибка: {e}", exc_info=True)
            return None


# Глобальный экземпляр
_replicate_client: Optional[ReplicateClient] = None


def get_replicate_client() -> ReplicateClient:
    """Получает или создает клиент Replicate"""
    global _replicate_client
    if _replicate_client is None:
        _replicate_client = ReplicateClient()
    return _replicate_client
