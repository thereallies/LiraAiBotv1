"""
OpenRouter API клиент.
"""
import asyncio
import json
import logging
import os
from typing import Dict, Optional, Any
import aiohttp

from backend.config import Config

logger = logging.getLogger("bot.llm")


class OpenRouterClient:
    """Клиент для работы с OpenRouter API"""
    
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config()
        self.config = config
        self.api_keys = config.OPENROUTER_API_KEYS
        self.current_key_index = 0
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Параметры LLM
        llm_cfg = getattr(config, "LLM_CONFIG", {})
        self.default_model = llm_cfg.get("model", "openai/gpt-oss-20b:free")
        self.fallback_model = llm_cfg.get("fallback_model", "deepseek/deepseek-chat-v3.1:free")
        self.max_tokens = llm_cfg.get("max_tokens", 4096)
        self.temperature = llm_cfg.get("temperature", 0.7)
        
        logger.info(f"OpenRouter клиент инициализирован с {len(self.api_keys)} ключами")
    
    def get_current_api_key(self) -> str:
        """Получение текущего API ключа"""
        if not self.api_keys:
            raise ValueError("API ключи OpenRouter не настроены")
        return self.api_keys[self.current_key_index]
    
    def rotate_api_key(self):
        """Ротация API ключей"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Переключение на API ключ #{self.current_key_index + 1}")
    
    async def chat_completion(
        self,
        user_message: str,
        system_prompt: str = "",
        chat_history: Optional[list] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Генерирует ответ через chat completion API"""

        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        # Формируем сообщения
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": user_message})

        # Выбираем API ключ: для DeepSeek используем второй ключ если есть
        api_key = self.get_current_api_key()
        if model.startswith("deepseek/") and len(self.api_keys) > 1:
            api_key = self.api_keys[1]  # Второй ключ для DeepSeek
            logger.debug(f"Используем ключ #{self.api_keys.index(api_key)+1} для {model}")

        # Формируем запрос
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Пробуем все ключи плюс несколько дополнительных попыток
        max_attempts = len(self.api_keys) + 5  # Пробуем все ключи + запас
        for attempt in range(max_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data["choices"][0]["message"]["content"]
                        elif response.status == 429:
                            # Rate limit - пробуем другой ключ
                            if len(self.api_keys) > 1:
                                logger.warning(f"Rate limit на ключе, ротирую ключ...")
                                self.rotate_api_key()
                                headers["Authorization"] = f"Bearer {self.get_current_api_key()}"
                                continue
                            raise Exception("Rate limit exceeded")
                        elif response.status == 402:
                            # Недостаточно кредитов - пробуем другой ключ
                            error_text = await response.text()
                            if len(self.api_keys) > 1:
                                logger.warning(f"Недостаточно кредитов на ключе (402), ротирую ключ...")
                                self.rotate_api_key()
                                headers["Authorization"] = f"Bearer {self.get_current_api_key()}"
                                continue
                            raise Exception(f"Insufficient credits: {error_text}")
                        elif response.status == 401:
                            # Невалидный ключ - пробуем другой ключ
                            error_text = await response.text()
                            if len(self.api_keys) > 1:
                                logger.warning(f"Невалидный ключ (401), ротирую ключ...")
                                self.rotate_api_key()
                                headers["Authorization"] = f"Bearer {self.get_current_api_key()}"
                                continue
                            raise Exception(f"Invalid API key (401): {error_text}")
                        elif response.status == 404:
                            # Ошибка политики данных или модель недоступна - пробуем другой ключ
                            error_text = await response.text()
                            if len(self.api_keys) > 1:
                                logger.warning(f"Ошибка 404 (политика данных или модель недоступна), ротирую ключ...")
                                self.rotate_api_key()
                                headers["Authorization"] = f"Bearer {self.get_current_api_key()}"
                                continue
                            raise Exception(f"Model or policy error (404): {error_text}")
                        else:
                            error_text = await response.text()
                            raise Exception(f"API error {response.status}: {error_text}")
                            
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(f"Ошибка при запросе к OpenRouter: {e}")
                    raise
                await asyncio.sleep(1)
        
        raise Exception("Не удалось получить ответ от LLM")

