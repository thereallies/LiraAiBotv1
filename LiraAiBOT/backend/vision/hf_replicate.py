"""
Hugging Face API клиент для генерации изображений.
Использует Stable Diffusion 3 Medium через Hugging Face Inference API
"""
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

logger = logging.getLogger("bot.vision")


class HFReplicateClient:
    """Клиент для работы с Hugging Face Inference API (Stable Diffusion 3)"""

    def __init__(self):
        # Используем HF_TOKEN из .env
        self.api_key = os.getenv("HF_TOKEN", "") or os.getenv("HUGGINGFACE_API_KEY", "")
        
        # Модели для генерации изображений с уровнями доступа
        self.models = {
            "hf-sd3-medium": {
                "model": "stabilityai/stable-diffusion-3-medium-diffusers",
                "level": "user",
                "description": "Stable Diffusion 3 Medium"
            },
        }
        
        # Модели по уровням доступа
        self.models_by_level = {
            "admin": ["hf-sd3-medium"],
            "subscriber": ["hf-sd3-medium"],
            "user": ["hf-sd3-medium"],
        }
        
        self.client = None

        if self.api_key:
            try:
                from huggingface_hub import InferenceClient
                self.client = InferenceClient(
                    provider="auto",
                    api_key=self.api_key,
                )
                logger.info("✅ HF клиент инициализирован (Stable Diffusion 3)")
                logger.info(f"   Доступно моделей: {len(self.models)}")
            except ImportError:
                logger.warning("⚠️ huggingface_hub не установлен")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации HF: {e}")
        else:
            logger.warning("❌ HF_TOKEN/HUGGINGFACE_API_KEY не настроен")

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
        model_key: str = "hf-sd3-medium",
        timeout: int = 60
    ) -> Optional[bytes]:
        """
        Генерирует изображение через HF Inference API
        """
        if not self.api_key or not self.client:
            logger.error("❌ HF_TOKEN не настроен или клиент не инициализирован")
            return None

        if model_key not in self.models:
            logger.error(f"❌ Модель {model_key} не найдена")
            return None

        model_name = self.models[model_key]["model"]

        try:
            logger.info(f"🎨 HF запрос ({model_key}): {prompt[:50]}...")

            # Генерация изображения
            image = self.client.text_to_image(
                prompt,
                model=model_name,
            )

            # Конвертируем PIL.Image в bytes
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            image_data = buffer.getvalue()

            if image_data and len(image_data) > 1000:
                logger.info(f"✅ HF успешно: {len(image_data)} байт")
                return image_data
            else:
                logger.error("❌ HF вернул пустое изображение")
                return None

        except Exception as e:
            logger.error(f"❌ Ошибка HF: {e}", exc_info=True)
            return None


# Глобальный экземпляр
_hf_replicate_client: Optional[HFReplicateClient] = None


def get_hf_replicate_client() -> HFReplicateClient:
    """Получает или создает клиент HF"""
    global _hf_replicate_client
    if _hf_replicate_client is None:
        _hf_replicate_client = HFReplicateClient()
    return _hf_replicate_client
