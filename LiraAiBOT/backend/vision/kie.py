"""
KIE.ai API клиент для генерации изображений.
Модель: Google Nano Banana 2 - бесплатная!
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

logger = logging.getLogger("bot.vision.kie")


class KIEClient:
    """Клиент для работы с KIE.ai API"""

    def __init__(self):
        self.api_key = os.getenv("KIE_API_KEY", "")
        self.base_url = "https://api.kie.ai/api/v1"

        self.models = {
            "kie-nano-banana-2": {
                "model": "nano-banana-2",
                "level": "user",
                "description": "Nano Banana 2 (KIE.ai)"
            },
        }
        self.models_by_level = {
            "admin": ["kie-nano-banana-2"],
            "subscriber": ["kie-nano-banana-2"],
            "user": ["kie-nano-banana-2"],
        }

        if self.api_key:
            logger.info(f"✅ KIE.ai клиент инициализирован (Nano Banana 2)")
        else:
            logger.warning("❌ KIE_API_KEY не настроен")

    def get_models_for_user(self, access_level: str) -> dict:
        """Получает доступные модели для уровня доступа пользователя."""
        level = access_level if access_level in self.models_by_level else "user"
        model_keys = self.models_by_level[level]
        return {k: v for k, v in self.models.items() if k in model_keys}

    async def generate_image(
        self,
        prompt: str,
        model_key: str = "kie-nano-banana-2",
        timeout: int = 90
    ) -> Optional[bytes]:
        """
        Генерирует изображение через KIE.ai API
        """
        if not self.api_key:
            logger.error("❌ KIE API ключ не настроен")
            return None

        if model_key not in self.models:
            logger.error(f"❌ Модель {model_key} не найдена")
            return None

        model_name = self.models[model_key]["model"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Создаем задачу
                create_url = f"{self.base_url}/jobs/createTask"
                payload = {
                    "model": model_name,
                    "callBackUrl": "",  # Не используем callback
                    "input": {
                        "prompt": prompt,
                        "aspect_ratio": "1:1",
                        "resolution": "1K",
                        "output_format": "jpg"
                    }
                }

                logger.info(f"🎨 KIE.ai запрос ({model_name}): {prompt[:50]}...")

                async with session.post(create_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"❌ KIE.ai ошибка создания: {response.status} - {error}")
                        return None

                    result_data = await response.json()
                    
                    if result_data.get("code") != 200:
                        logger.error(f"❌ KIE.ai ошибка: {result_data}")
                        return None

                    task_id = result_data.get("data", {}).get("taskId")
                    if not task_id:
                        logger.error("❌ Не получен task ID")
                        return None

                    logger.info(f"🎨 KIE.ai Task ID: {task_id}")

                # Ждем завершения (опрос)
                start_time = time.time()
                while time.time() - start_time < timeout:
                    await asyncio.sleep(3)

                    # Проверяем статус
                    status_url = f"{self.base_url}/jobs/recordInfo?taskId={task_id}"
                    async with session.get(status_url, headers=headers) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            
                            if status_data.get("code") == 200:
                                task_status = status_data.get("data", {}).get("state")
                                
                                if task_status == "success":
                                    # Получаем результат
                                    result_json = status_data.get("data", {}).get("resultJson") or "{}"
                                    try:
                                        import json
                                        result_data = json.loads(result_json)
                                    except Exception:
                                        result_data = {}

                                    output_url = (
                                        result_data.get("output", {}).get("image_url")
                                        or result_data.get("outputUrl")
                                        or result_data.get("imageUrl")
                                    )
                                    if output_url:
                                        logger.info(f"✅ KIE.ai изображение готово: {output_url}")

                                        async with session.get(output_url) as img_response:
                                            if img_response.status == 200:
                                                image_data = await img_response.read()
                                                logger.info(f"✅ KIE.ai получено {len(image_data)} байт")
                                                return image_data

                                    logger.error("❌ Не получен URL изображения")
                                    return None
                                elif task_status in ["failed", "cancelled"]:
                                    logger.error(f"❌ KIE.ai ошибка: {task_status}")
                                    return None
                        else:
                            logger.warning(f"⚠️ KIE.ai статус проверки: {status_response.status}")

                logger.error(f"❌ KIE.ai таймаут")
                return None

        except asyncio.TimeoutError:
            logger.error("❌ KIE.ai таймаут")
            return None
        except Exception as e:
            logger.error(f"❌ KIE.ai ошибка: {e}", exc_info=True)
            return None


# Глобальный экземпляр
_kie_client: Optional[KIEClient] = None


def get_kie_client() -> KIEClient:
    """Получает или создает клиент KIE"""
    global _kie_client
    if _kie_client is None:
        _kie_client = KIEClient()
    return _kie_client
