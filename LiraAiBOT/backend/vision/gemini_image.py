"""
Google Gemini/Imagen API клиент для генерации изображений.
"""
import logging
import os
from typing import Optional, Any
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Загружаем .env
load_dotenv()

logger = logging.getLogger("bot.vision")


class GeminiImageClient:
    """Клиент для работы с Google Gemini/Imagen API"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        
        # Модели для генерации изображений с уровнями доступа
        # Используем gemini-2.0-flash-exp как основную (поддерживает image generation)
        self.image_models = {
            # Основная модель для всех
            "gemini-flash": {
                "model": "gemini-2.5-flash",
                "level": "user",
                "description": "Gemini 2.5 Flash"
            },
        }
        
        # Модели по уровням доступа
        self.models_by_level = {
            "admin": [
                "gemini-flash"
            ],
            "subscriber": [
                "gemini-flash"
            ],
            "user": [
                "gemini-flash"
            ]
        }

        if self.api_key:
            logger.info(f"✅ Gemini Image клиент инициализирован")
            logger.info(f"   Доступно моделей: {len(self.image_models)}")
        else:
            logger.warning("❌ GEMINI_API_KEY не настроен")

    def get_models_for_user(self, access_level: str) -> dict:
        """
        Получает доступные модели для уровня доступа пользователя
        
        Args:
            access_level: Уровень доступа (admin, subscriber, user)
        
        Returns:
            Dict с моделями
        """
        level = access_level if access_level in self.models_by_level else "user"
        model_keys = self.models_by_level[level]
        
        return {k: v for k, v in self.image_models.items() if k in model_keys}

    async def generate_image(
        self,
        prompt: str,
        model_key: str = "imagen-4.0-generate",
        timeout: int = 90
    ) -> Optional[bytes]:
        """
        Генерирует изображение по промпту
        
        Args:
            prompt: Описание изображения
            model_key: Ключ модели из self.image_models
            timeout: Таймаут в секундах
        
        Returns:
            Bytes изображения или None
        """
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY не настроен")
            return None
        
        if model_key not in self.image_models:
            logger.error(f"❌ Модель {model_key} не найдена")
            return None
        
        model_name = self.image_models[model_key]["model"]
        
        try:
            client = genai.Client(api_key=self.api_key)
            
            logger.info(f"🎨 Gemini запрос: {model_name}, промпт: {prompt[:50]}...")
            
            # Генерация изображения с конфигурацией для image generation
            from google.genai import types
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['image', 'text']
                )
            )
            
            # Проверяем есть ли изображение в ответе
            image_data = None
            
            # Способ 1: Проверяем candidates -> parts -> inline_data
            try:
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                # Проверяем inline_data (изображение)
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    image_data = part.inline_data.data
                                    logger.info(f"✅ Gemini: найдено изображение в inline_data: {len(image_data)} байт")
                                    break
                                # Проверяем blob
                                if hasattr(part, 'blob') and part.blob:
                                    image_data = part.blob.data if hasattr(part.blob, 'data') else part.blob
                                    logger.info(f"✅ Gemini: найдено изображение в blob: {len(image_data)} байт")
                                    break
            except Exception as e:
                logger.debug(f"Способ 1 не сработал: {e}")
            
            # Способ 2: Проверяем response.text (base64)
            if not image_data:
                try:
                    if hasattr(response, 'text') and response.text:
                        import base64
                        text = response.text.strip()
                        # Пробуем декодировать base64
                        if ',' in text:
                            text = text.split(',')[1]
                        image_data = base64.b64decode(text)
                        logger.info(f"✅ Gemini: найдено base64 изображение: {len(image_data)} байт")
                except Exception as e:
                    logger.debug(f"Способ 2 (base64) не сработал: {e}")
            
            if image_data and len(image_data) > 1000:
                return image_data
            else:
                logger.error(f"❌ Gemini не вернул изображение. Response: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка Gemini: {e}")
            return None


# Глобальный экземпляр
_gemini_image_client: Optional[GeminiImageClient] = None


def get_gemini_image_client() -> GeminiImageClient:
    """Получает или создает клиент Gemini Image"""
    global _gemini_image_client
    if _gemini_image_client is None:
        _gemini_image_client = GeminiImageClient()
    return _gemini_image_client
