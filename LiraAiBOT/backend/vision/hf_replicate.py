"""
Hugging Face + Replicate API клиент для генерации изображений.
Использует FLUX.1-dev через Replicate provider.
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
    """Клиент для работы с Hugging Face + Replicate (FLUX.1)"""

    def __init__(self):
        self.api_key = os.getenv("HF_TOKEN", "") or os.getenv("HUGGINGFACE_API_KEY", "")
        
        # Модели для генерации изображений с уровнями доступа
        self.models = {
            "hf-flux-dev": {
                "model": "black-forest-labs/FLUX.1-dev",
                "level": "user",
                "description": "FLUX.1 Dev (Replicate)"
            },
            "hf-flux-pro": {
                "model": "black-forest-labs/FLUX.1-pro",
                "level": "subscriber",
                "description": "FLUX.1 Pro (Replicate)"
            },
        }
        
        # Модели по уровням доступа
        self.models_by_level = {
            "admin": ["hf-flux-dev", "hf-flux-pro"],
            "subscriber": ["hf-flux-dev", "hf-flux-pro"],
            "user": ["hf-flux-dev"],
        }
        
        self.client = None

        if self.api_key:
            try:
                from huggingface_hub import InferenceClient
                self.client = InferenceClient(
                    provider="replicate",
                    api_key=self.api_key,
                )
                logger.info("✅ HF+Replicate клиент инициализирован")
                logger.info(f"   Доступно моделей: {len(self.models)}")
            except ImportError:
                logger.warning("⚠️ huggingface_hub не установлен")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации HF+Replicate: {e}")
        else:
            logger.warning("❌ HF_TOKEN/HUGGINGFACE_API_KEY не настроен")

    def get_models_for_user(self, access_level: str) -> Dict[str, Any]:
        """
        Получает доступные модели для уровня доступа пользователя

        Args:
            access_level: Уровень доступа (admin, subscriber, user)

        Returns:
            Dict с моделями
        """
        level = access_level if access_level in self.models_by_level else "user"
        model_keys = self.models_by_level[level]

        return {k: v for k, v in self.models.items() if k in model_keys}

    async def generate_image(
        self,
        prompt: str,
        model_key: str = "hf-flux-dev",
        timeout: int = 60
    ) -> Optional[bytes]:
        """
        Генерирует изображение через HF+Replicate (FLUX.1)

        Args:
            prompt: Текстовое описание изображения
            model_key: Ключ модели из self.models
            timeout: Таймаут в секундах

        Returns:
            Bytes изображения или None
        """
        if not self.api_key or not self.client:
            logger.error("❌ HF_TOKEN не настроен или клиент не инициализирован")
            return None

        if model_key not in self.models:
            logger.error(f"❌ Модель {model_key} не найдена")
            return None

        model_name = self.models[model_key]["model"]

        try:
            logger.info(f"🎨 HF+Replicate запрос ({model_key}): {prompt[:50]}...")

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
                logger.info(f"✅ HF+Replicate успешно: {len(image_data)} байт")
                return image_data
            else:
                logger.error("❌ HF+Replicate вернул пустое изображение")
                return None

        except Exception as e:
            logger.error(f"❌ Ошибка HF+Replicate: {e}")
            return None


# Глобальный экземпляр
_hf_replicate_client: Optional[HFReplicateClient] = None


def get_hf_replicate_client() -> HFReplicateClient:
    """Получает или создает клиент HF+Replicate"""
    global _hf_replicate_client
    if _hf_replicate_client is None:
        _hf_replicate_client = HFReplicateClient()
    return _hf_replicate_client
