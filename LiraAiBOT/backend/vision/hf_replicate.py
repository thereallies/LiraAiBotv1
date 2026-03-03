"""
Polza.ai API клиент для генерации изображений.
Использует Z-Image через Polza.ai API
"""
import logging
import os
import asyncio
from typing import Optional, Dict, Any
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
                "model": "tongyi-mai/z-image",
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
        Используем формат из документации Polza.ai
        """
        if not self.api_key:
            logger.error("❌ POLZA_API_KEY не настроен")
            return None

        if model_key not in self.models:
            logger.error(f"❌ Модель {model_key} не найдена")
            return None

        model_info = self.models[model_key]

        # Обрезаем промпт до 1000 символов (лимит Polza.ai Z-Image)
        max_prompt_length = 1000
        if len(prompt) > max_prompt_length:
            prompt = prompt[:max_prompt_length-3] + "..."
            logger.info(f"✂️ Промпт обрезан до {max_prompt_length} символов")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            logger.info(f"🎨 Polza.ai запрос ({model_key}): {prompt[:50]}...")

            async with aiohttp.ClientSession() as session:
                # Используем /media endpoint из документации Polza.ai
                create_url = f"{self.base_url}/media"
                
                # Формат запроса согласно документации Polza.ai
                payload = {
                    "model": model_info["model"],
                    "input": {
                        "prompt": prompt,
                        "aspect_ratio": "1:1",
                        "images": []  # Пустой массив для text-to-image
                    }
                }

                logger.debug(f"📤 Payload: {payload}")

                async with session.post(create_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    response_text = await response.text()
                    logger.debug(f"📥 Response status: {response.status}, body: {response_text[:500]}")
                    
                    if response.status != 200:
                        logger.error(f"❌ Polza.ai ошибка {response.status}: {response_text}")
                        return None

                    data = await response.json()
                    logger.debug(f"📥 Parsed data: {data}")
                    
                    # Получаем изображение из ответа
                    # Polza.ai может вернуть по-разному
                    if "url" in data:
                        img_url = data["url"]
                        logger.info(f"✅ Polza.ai изображение готово: {img_url}")
                        
                        # Скачиваем изображение
                        async with session.get(img_url) as img_response:
                            if img_response.status == 200:
                                image_data = await img_response.read()
                                logger.info(f"✅ Polza.ai получено {len(image_data)} байт")
                                return image_data
                    
                    elif "data" in data and len(data["data"]) > 0:
                        img_data = data["data"][0]
                        
                        if "url" in img_data:
                            img_url = img_data["url"]
                            logger.info(f"✅ Polza.ai изображение готово: {img_url}")
                            
                            # Скачиваем изображение
                            async with session.get(img_url) as img_response:
                                if img_response.status == 200:
                                    image_data = await img_response.read()
                                    logger.info(f"✅ Polza.ai получено {len(image_data)} байт")
                                    return image_data
                        
                        elif "b64_json" in img_data:
                            # Base64 изображение
                            import base64
                            image_data = base64.b64decode(img_data["b64_json"])
                            logger.info(f"✅ Polza.ai получено {len(image_data)} байт (base64)")
                            return image_data
                    
                    logger.error(f"❌ Polza.ai не вернул изображение: {data}")
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
