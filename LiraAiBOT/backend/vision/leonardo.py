"""
Leonardo.ai API клиент для генерации изображений.
Бесплатно: 150 токенов в день (~75 изображений 512x512)
"""
import asyncio
import logging
import os
import time
import aiohttp
from typing import Optional
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

logger = logging.getLogger("bot.vision.leonardo")


class LeonardoAIClient:
    """Клиент для работы с Leonardo.ai API"""

    def __init__(self):
        self.api_key = os.getenv("LEONARDO_API_KEY", "")
        # Правильный API endpoint Leonardo.ai
        self.base_url = "https://cloud.leonardo.ai/api/rest/v1"
        
        # Модель Leonardo Phoenix 0.9 (из списка поддерживаемых)
        # Используем правильный ID модели
        self.default_model = "6bef9f1b-29cb-40c7-b9df-32b51c1f67dd"  # Leonardo Phoenix
        
        if self.api_key:
            logger.info(f"✅ Leonardo.ai клиент инициализирован")
        else:
            logger.warning("❌ LEONARDO_API_KEY не настроен")

    async def generate_image(
        self,
        prompt: str,
        model_id: str = None,
        width: int = 512,
        height: int = 512,
        timeout: int = 60
    ) -> Optional[bytes]:
        """
        Генерирует изображение через Leonardo.ai

        Args:
            prompt: Описание изображения
            model_id: ID модели (по умолчанию Leonardo Phoenix)
            width: Ширина
            height: Высота
            timeout: Таймаут в секундах

        Returns:
            Байты изображения или None
        """
        if not self.api_key:
            logger.error("❌ Leonardo.ai API ключ не настроен")
            return None

        model_id = model_id or self.default_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                # 1. Создаем задачу генерации
                gen_url = f"{self.base_url}/generations"
                payload = {
                    "prompt": prompt,
                    "modelId": model_id,
                    "width": width,
                    "height": height,
                    "num_images": 1,
                    "scheduler": "EULER_DISCRETE",
                    "presetStyle": "LEONARDO",
                }

                logger.info(f"🎨 Leonardo.ai запрос: {prompt[:50]}...")

                async with session.post(gen_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"❌ Leonardo.ai ошибка создания: {response.status} - {error}")
                        return None

                    gen_data = await response.json()
                    generation_id = gen_data.get("sdGenerationJob", {}).get("generationId")

                    if not generation_id:
                        logger.error("❌ Не получен generationId")
                        return None

                    logger.info(f"🎨 Leonardo.ai Generation ID: {generation_id}")

                # 2. Ждем завершения генерации (опрос)
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(2)

                    check_url = f"{self.base_url}/generations/{generation_id}"
                    async with session.get(check_url, headers=headers) as check_response:
                        if check_response.status == 200:
                            check_data = await check_response.json()
                            generated_images = check_data.get("generations_by_pk", {}).get("generated_images", [])

                            if generated_images:
                                img_url = generated_images[0].get("url")
                                if img_url:
                                    logger.info(f"✅ Leonardo.ai изображение готово: {img_url}")

                                    # 3. Скачиваем изображение
                                    async with session.get(img_url) as img_response:
                                        if img_response.status == 200:
                                            image_data = await img_response.read()
                                            logger.info(f"✅ Leonardo.ai получено {len(image_data)} байт")
                                            return image_data

                                logger.error("❌ Не получен URL изображения")
                                return None
                        else:
                            logger.warning(f"⚠️ Leonardo.ai статус проверки: {check_response.status}")

                logger.error(f"❌ Leonardo.ai таймаут ({timeout}с)")
                return None

        except Exception as e:
            logger.error(f"❌ Leonardo.ai ошибка: {e}", exc_info=True)
            return None


# Глобальный экземпляр
_leonardo_client: Optional[LeonardoAIClient] = None


def get_leonardo_client() -> LeonardoAIClient:
    """Получает или создает клиент Leonardo.ai"""
    global _leonardo_client
    if _leonardo_client is None:
        _leonardo_client = LeonardoAIClient()
    return _leonardo_client
