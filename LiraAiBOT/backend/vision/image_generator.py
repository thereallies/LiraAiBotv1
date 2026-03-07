"""
Единый генератор изображений для API-роутов.
Использует те же провайдеры, что и Telegram-бот: Polza.ai и KIE.ai.
"""
import logging
from typing import Optional

from backend.config import Config
from backend.vision.hf_replicate import get_hf_replicate_client

logger = logging.getLogger("bot.vision")


class ImageGenerator:
    """Генератор изображений через Polza.ai и KIE.ai."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.polza_client = get_hf_replicate_client()
        logger.info("✅ ImageGenerator инициализирован (Polza.ai)")

    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        **kwargs
    ) -> Optional[bytes]:
        """
        Генерирует изображение через основной или запасной провайдер.
        width/height оставлены в сигнатуре для совместимости API.
        """
        model = model or "polza-zimage"
        enhanced_prompt = f"{prompt}, high quality, detailed, artistic, 8k, masterpiece"

        if model.startswith("kie-"):
            if self.polza_client.api_key:
                return await self.polza_client.generate_image(enhanced_prompt, model_key="polza-zimage", timeout=90)
            return None

        if self.polza_client.api_key:
            result = await self.polza_client.generate_image(enhanced_prompt, model_key="polza-zimage", timeout=90)
            if result:
                return result

        return None


_image_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """Получает или создаёт экземпляр генератора изображений."""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator
