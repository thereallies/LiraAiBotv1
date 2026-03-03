"""
Polza.ai API клиент для генерации изображений.
Использует Z-Image через Polza.ai API
"""
import logging
import os
import time
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
import aiohttp

# Загружаем .env файл
load_dotenv()

logger = logging.getLogger("bot.vision")


class HFReplicateClient:
    """Клиент для работы с Polza.ai API (Z-Image)"""

    def __init__(self):
        # Используем POLZA_API_KEY из .env
        self.api_key = os.getenv("POLZA_API_KEY", "")
        self.base_url = "https://polza.ai/api/v1"
        
        # Модели для генерации изображений с уровнями доступа
        self.models = {
            "polza-zimage": {
                "model": "z-image",
                "level": "user",
                "description": "Z-Image (Polza.ai)"
            },
        }
        
        # Модели по уровням доступа
        self.models_by_level = {
            "admin": ["polza-zimage"],
            "subscriber": ["polza-zimage"],
            "user": ["polza-zimage"],
        }

        if self.api_key:
            logger.info("✅ Polza.ai клиент инициализирован (Z-Image)")
            logger.info(f"   Доступно моделей: {len(self.models)}")
        else:
            logger.warning("❌ POLZA_API_KEY не настроен")

    def get_models_for_user(self, access_level: str) -> Dict[str, Any]:
        """
        Получает доступные модели для уровня доступа пользователя
        """
        level = access_level if access_level in self.models_by_level else "user"
        model_keys = self.models_by_level[level]

        return {k: v for k, v in self.models.items() if k in model_keys}

    async def generate_image(
        self,
        prompt: str,
        model_key: str = "polza-zimage",
        timeout: int = 90
    ) -> Optional[bytes]:
        """
        Генерирует изображение через Polza.ai API (Z-Image)
        """
        if not self.api_key:
            logger.error("❌ POLZA_API_KEY не настроен")
            return None

        if model_key not in self.models:
            logger.error(f"❌ Модель {model_key} не найдена")
            return None

        model_info = self.models[model_key]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            logger.info(f"🎨 Polza.ai запрос ({model_key}): {prompt[:50]}...")

            async with aiohttp.ClientSession() as session:
                # Создаем задачу генерации
                create_url = f"{self.base_url}/image/generations"
                payload = {
                    "model": model_info["model"],
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                }

                async with session.post(create_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"❌ Polza.ai ошибка создания: {response.status} - {error}")
                        return None

                    create_data = await response.json()
                    
                    # Получаем URL изображения из ответа
                    if "data" in create_data and len(create_data["data"]) > 0:
                        img_url = create_data["data"][0].get("url")
                        if img_url:
                            logger.info(f"✅ Polza.ai изображение готово: {img_url}")
                            
                            # Скачиваем изображение
                            async with session.get(img_url) as img_response:
                                if img_response.status == 200:
                                    image_data = await img_response.read()
                                    logger.info(f"✅ Polza.ai получено {len(image_data)} байт")
                                    return image_data
                    
                    logger.error("❌ Polza.ai не вернул URL изображения")
                    return None

        except Exception as e:
            logger.error(f"❌ Ошибка Polza.ai: {e}", exc_info=True)
            return None


# Глобальный экземпляр
_hf_replicate_client: Optional[HFReplicateClient] = None


def get_hf_replicate_client() -> HFReplicateClient:
    """Получает или создает клиент Polza.ai"""
    global _hf_replicate_client
    if _hf_replicate_client is None:
        _hf_replicate_client = HFReplicateClient()
    return _hf_replicate_client
