"""
Модуль для анализа изображений через мультимодальные модели OpenRouter.
Поддерживает анализ изображений и извлечение текста.
"""
import asyncio
import logging
import os
import base64
import aiohttp
from typing import Optional, List, Dict, Any
from pathlib import Path

from backend.config import Config

logger = logging.getLogger("bot.vision")


class ImageAnalyzer:
    """
    Класс для анализа изображений с помощью мультимодальных моделей через OpenRouter.
    Использует модель qwen/qwen2.5-vl-32b-instruct для анализа изображений и извлечения текста.
    """
    
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config()
        self.config = config
        self.api_keys = config.OPENROUTER_API_KEYS.copy()
        # Убираем пустые ключи
        self.api_keys = [key for key in self.api_keys if key and key != "your_openrouter_api_key"]
        
        # Приоритет платному ключу (если есть)
        paid_key = os.environ.get("OPENROUTER_API_KEY_PAID", "")
        if paid_key and paid_key in self.api_keys:
            self.api_keys.remove(paid_key)
            self.api_keys.insert(0, paid_key)  # Платный ключ в начало списка
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        # Пробуем сначала платную модель, потом бесплатную
        self.model = "qwen/qwen2.5-vl-32b-instruct"  # Платная версия
        self.fallback_model = "qwen/qwen2.5-vl-32b-instruct:free"  # Бесплатная версия
        
        if not self.api_keys:
            logger.warning("API ключи для OpenRouter не указаны!")
        else:
            logger.info(f"ImageAnalyzer инициализирован с {len(self.api_keys)} ключами, модель: {self.model}")
    
    async def analyze_image(self, image_path: str, prompt: str = "Что на этом изображении? Опиши подробно.") -> Optional[str]:
        """
        Анализирует изображение по пути с помощью мультимодальной модели.
        
        Args:
            image_path: Путь к изображению (локальный файл)
            prompt: Текстовый запрос для модели
            
        Returns:
            Текстовое описание изображения или None в случае ошибки
        """
        if not self.api_keys:
            logger.error("Нет доступных API ключей для анализа изображения")
            return None
        
        # Конвертируем изображение в base64
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                
            # Формируем сообщения для модели с base64
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
            
            # Пробуем сначала платную модель
            logger.info(f"Пробуем платную модель: {self.model}")
            for api_key in self.api_keys:
                result = await self._try_analyze_with_key(messages, api_key, self.model)
                if result:
                    return result
            
            # Пробуем бесплатную модель как fallback
            logger.info(f"Пробуем бесплатную модель: {self.fallback_model}")
            for api_key in self.api_keys:
                result = await self._try_analyze_with_key(messages, api_key, self.fallback_model)
                if result:
                    return result
            
            logger.error("Не удалось проанализировать изображение со всеми доступными методами")
            return "Не удалось проанализировать изображение. Возможно, превышен лимит запросов или формат изображения не поддерживается."
            
        except Exception as e:
            logger.error(f"Ошибка при подготовке изображения: {e}")
            return f"Ошибка при анализе изображения: {str(e)}"
    
    async def _try_analyze_with_key(self, messages: List[Dict[str, Any]], api_key: str, model: str) -> Optional[str]:
        """
        Пробует проанализировать изображение с конкретным API ключом и моделью.
        
        Args:
            messages: Сообщения для модели
            api_key: API ключ OpenRouter
            model: Название модели для использования
            
        Returns:
            Текстовое описание изображения или None в случае ошибки
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/liraai-multiassistent",
            "X-Title": "LiraAI MultiAssistent",
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 2000  # Увеличиваем для более подробных описаний
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(f"Ключ {api_key[:8]}... недоступен ({response.status}), пробуем следующий: {error_text[:200]}")
                        return None
                    
                    result = await response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        logger.info(f"Успешно проанализировано изображение с моделью {model}: {content[:100]}...")
                        return content
                    
                    logger.error(f"Неожиданный формат ответа от OpenRouter: {result}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при запросе к модели {model}")
            return None
        except Exception as e:
            logger.error(f"Исключение при анализе изображения с моделью {model}: {e}")
            return None

