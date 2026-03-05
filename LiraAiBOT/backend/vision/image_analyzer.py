"""
Модуль для анализа изображений через мультимодальные модели.
Поддерживает: Groq, Cerebras, OpenRouter (fallback)
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
    Класс для анализа изображений с помощью мультимодальных моделей.
    Приоритет: Groq → Cerebras → OpenRouter (fallback)
    """

    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config()
        self.config = config
        
        # API ключи
        self.openrouter_keys = config.OPENROUTER_API_KEYS.copy()
        self.openrouter_keys = [k for k in self.openrouter_keys if k and k != "your_openrouter_api_key"]
        
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        
        self.cerebras_key = os.environ.get("CEREBRAS_API_KEY", "")
        self.cerebras_url = "https://api.cerebras.ai/v1/chat/completions"
        
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Модели для анализа
        # Groq Vision не существует - исключаем
        # Cerebras Vision не поддерживает - исключаем
        self.openrouter_models = [
            "nvidia/nemotron-nano-12b-v2-vl:free",  # ✅ Работает!
        ]

        logger.info(f"ImageAnalyzer инициализирован:")
        logger.info(f"  Groq Vision: ❌ (модель не существует)")
        logger.info(f"  Cerebras Vision: ❌ (не поддерживает)")
        logger.info(f"  OpenRouter Vision: ✅ ({len(self.openrouter_models)} моделей)")

    async def analyze_image(self, image_path: str, prompt: str = "Что на этом изображении? Опиши подробно.") -> Optional[str]:
        """
        Анализирует изображение по пути с помощью мультимодальной модели.
        Приоритет: Groq → Cerebras → OpenRouter

        Args:
            image_path: Путь к изображению (локальный файл)
            prompt: Текстовый запрос для модели

        Returns:
            Текстовое описание изображения или None в случае ошибки
        """
        # Конвертируем изображение в base64
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"} }
                    ]
                }
            ]

            # 1. Пробуем OpenRouter Vision (единственный рабочий вариант)
            if self.openrouter_keys:
                for model in self.openrouter_models:
                    logger.info(f"🔍 Пробуем OpenRouter Vision: {model}")
                    for api_key in self.openrouter_keys:
                        result = await self._try_openrouter(messages, api_key, model)
                        if result:
                            logger.info(f"✅ OpenRouter Vision успешно ({model}): {result[:100]}...")
                            return result

            logger.error("❌ Не удалось проанализировать изображение со всеми методами")
            return "Не удалось проанализировать изображение. Возможно, превышен лимит запросов или формат изображения не поддерживается."

        except Exception as e:
            logger.error(f"Ошибка при подготовке изображения: {e}", exc_info=True)
            return f"Ошибка при анализе изображения: {str(e)}"

    async def _try_groq(self, messages: List[Dict[str, Any]], api_key: str) -> Optional[str]:
        """Анализ через Groq API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.groq_model,
            "messages": messages,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.groq_url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.warning(f"Groq ошибка ({response.status}): {error[:200]}")
                        return None
                    
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    return None
        except Exception as e:
            logger.error(f"Groq исключение: {e}")
            return None

    async def _try_cerebras(self, messages: List[Dict[str, Any]], api_key: str) -> Optional[str]:
        """Анализ через Cerebras API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.cerebras_model,
            "messages": messages,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.cerebras_url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.warning(f"Cerebras ошибка ({response.status}): {error[:200]}")
                        return None
                    
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    return None
        except Exception as e:
            logger.error(f"Cerebras исключение: {e}")
            return None

    async def _try_openrouter(self, messages: List[Dict[str, Any]], api_key: str, model: str) -> Optional[str]:
        """Анализ через OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/liraai-multiassistent",
            "X-Title": "LiraAI MultiAssistent",
        }
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.openrouter_url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.warning(f"OpenRouter ошибка ({response.status}): {error[:200]}")
                        return None
                    
                    result = await response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    return None
        except Exception as e:
            logger.error(f"OpenRouter исключение: {e}")
            return None
