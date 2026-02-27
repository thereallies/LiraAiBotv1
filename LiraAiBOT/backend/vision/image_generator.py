"""
Модуль для генерации изображений через различные сервисы.
"""
import asyncio
import logging
import aiohttp
import os
import urllib.parse
import re
from typing import Optional, Dict, Any

from backend.config import Config

logger = logging.getLogger("bot.vision")

# Pollinations.ai конфигурация
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"
POLLINATIONS_DEFAULT_MODEL = "flux"

# Hugging Face API конфигурация
HF_BASE_URL = "https://api-inference.huggingface.co/models"
HF_DEFAULT_MODEL = "stabilityai/stable-diffusion-3-medium-diffusers"

# Stable Horde (бесплатно, без ключа)
HORDE_BASE_URL = "https://stablehorde.net/api/v2"

# PolyAI (бесплатно, без ключа)
POLYAI_BASE_URL = "https://poly.ai/api/v1"

# Транслитерация для кириллицы
CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    ' ': '-', '_': '',
}

def transliterate(text: str) -> str:
    """Преобразует кириллицу в латиницу для URL"""
    result = []
    for char in text.lower():
        result.append(CYRILLIC_TO_LATIN.get(char, char))
    return ''.join(result)


class ImageGenerator:
    """Класс для генерации изображений"""
    
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config()
        self.config = config
        self.hf_api_key = config.HF_API_KEY
        
        logger.info("ImageGenerator инициализирован")
    
    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        **kwargs
    ) -> Optional[bytes]:
        """
        Генерирует изображение по текстовому описанию.
        Пробует несколько провайдеров по порядку.

        Args:
            prompt: Текстовое описание изображения
            model: Модель для генерации
            width: Ширина изображения
            height: Высота изображения

        Returns:
            Байты изображения или None
        """
        # 1. Пробуем PolyAI (бесплатно, быстро)
        logger.info(f"🎨 Попытка 1: PolyAI: {prompt}")
        result = await self._generate_polyai(prompt, width, height)
        if result:
            logger.info("✅ PolyAI сработал!")
            return result
        
        # 2. Пробуем Stable Horde (бесплатно, стабильно)
        logger.info(f"🎨 Попытка 2: Stable Horde: {prompt}")
        result = await self._generate_horde(prompt, width, height)
        if result:
            logger.info("✅ Stable Horde сработал!")
            return result
        
        # 3. Пробуем Hugging Face (если есть ключ)
        if self.hf_api_key:
            logger.info(f"🎨 Попытка 3: Hugging Face: {prompt}")
            result = await self._generate_huggingface(prompt, model, width, height)
            if result:
                logger.info("✅ Hugging Face сработал!")
                return result
        
        # 4. Fallback на Pollinations
        logger.info(f"🎨 Попытка 4: Pollinations: {prompt}")
        return await self._generate_pollinations(prompt, width, height)
    
    async def _generate_horde(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512,
        timeout: int = 120
    ) -> Optional[bytes]:
        """Генерация через Stable Horde (бесплатно, без ключа)"""
        try:
            # Транслитерируем промпт в английский
            prompt_en = transliterate(prompt)
            prompt_en = re.sub(r'[^a-z0-9 ]', '', prompt_en).strip()
            
            logger.info(f"🎨 Horde: Оригинал: {prompt}, EN: {prompt_en}")
            
            async with aiohttp.ClientSession() as session:
                # 1. Отправляем запрос на генерацию
                gen_url = f"{HORDE_BASE_URL}/generate/async"
                headers = {
                    "Content-Type": "application/json",
                    "apikey": "0000000000",  # Анонимный ключ
                }
                payload = {
                    "prompt": prompt_en if prompt_en else "beautiful landscape",
                    "params": {
                        "n": 1,
                        "steps": 20,
                        "width": width,
                        "height": height,
                    }
                }
                
                async with session.post(gen_url, json=payload, headers=headers) as response:
                    if response.status != 202:
                        logger.error(f"Horde generation error: {response.status}")
                        return None
                    
                    gen_data = await response.json()
                    job_id = gen_data.get("id")
                    if not job_id:
                        logger.error("Horde: нет job_id")
                        return None
                
                logger.info(f"🎨 Horde: Job ID: {job_id}, ждем завершения...")
                
                # 2. Ждем завершения (опрос)
                for attempt in range(timeout // 2):  # Проверяем каждые 2 секунды
                    await asyncio.sleep(2)
                    
                    check_url = f"{HORDE_BASE_URL}/generate/check/{job_id}"
                    async with session.get(check_url) as check_response:
                        if check_response.status == 200:
                            check_data = await check_response.json()
                            if check_data.get("done", False):
                                logger.info("✅ Horde: Генерация завершена!")
                                break
                
                # 3. Получаем результат
                pop_url = f"{HORDE_BASE_URL}/generate/pop"
                async with session.post(pop_url, json={"id": job_id}) as pop_response:
                    if pop_response.status == 200:
                        pop_data = await pop_response.json()
                        generations = pop_data.get("generations", [])
                        if generations:
                            img_url = generations[0].get("img")
                            if img_url:
                                logger.info(f"🎨 Horde: Загружаем изображение: {img_url}")
                                async with session.get(img_url) as img_response:
                                    if img_response.status == 200:
                                        image_data = await img_response.read()
                                        return image_data
                
                logger.error("❌ Horde: Не удалось получить изображение")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка Horde: {e}", exc_info=True)
            return None
    
    async def _generate_polyai(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512
    ) -> Optional[bytes]:
        """Генерация через PolyAI/Pollinations (бесплатно, без ключа)"""
        try:
            # Транслитерируем промпт
            prompt_en = transliterate(prompt)
            prompt_en = re.sub(r'[^a-z0-9 ]', '', prompt_en).strip()
            if not prompt_en:
                prompt_en = "beautiful landscape"
            
            logger.info(f"🎨 PolyAI: Оригинал: {prompt}, EN: {prompt_en}")
            
            async with aiohttp.ClientSession() as session:
                # Используем Pollinations с правильными параметрами
                url = f"https://image.pollinations.ai/prompt/{prompt_en}?width={width}&height={height}&seed=42&model=flux&nologo=true"
                logger.info(f"🎨 PolyAI URL: {url}")
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
                }
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    logger.info(f"🎨 PolyAI Status: {response.status}, Content-Type: {response.content_type}")
                    if response.status == 200 and 'image' in response.content_type:
                        image_data = await response.read()
                        logger.info(f"✅ PolyAI: Изображение получено ({len(image_data)} байт)")
                        return image_data
                    
                    error_text = await response.text()
                    logger.error(f"❌ PolyAI error {response.status}: {error_text[:200]}")
                    return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка PolyAI: {e}", exc_info=True)
            return None

    async def _generate_pollinations(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024
    ) -> Optional[bytes]:
        """Генерация через Pollinations.ai (бесплатно)"""
        try:
            # Транслитерируем кириллицу в латиницу
            prompt_latin = transliterate(prompt)
            # Удаляем лишние символы, оставляем только буквы и дефисы
            prompt_clean = re.sub(r'[^a-z0-9-]', '', prompt_latin)
            # Ограничиваем длину
            prompt_clean = prompt_clean[:80]
            
            logger.info(f"🎨 Pollinations: Оригинал: {prompt}")
            logger.info(f"🎨 Pollinations: Транслит: {prompt_clean}")
            
            # Формируем URL - Pollinations требует простой формат
            url = f"https://image.pollinations.ai/prompt/{prompt_clean}"
            logger.info(f"URL: {url}")

            async with aiohttp.ClientSession() as session:
                # Пробуем с разными заголовками
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    logger.info(f"Status: {response.status}, Content-Type: {response.content_type}")
                    if response.status == 200:
                        image_data = await response.read()
                        logger.info(f"✅ Изображение сгенерировано через Pollinations ({len(image_data)} байт)")
                        return image_data
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Pollinations error {response.status}: {error_text[:200]}")
                        return None

        except Exception as e:
            logger.error(f"❌ Ошибка генерации через Pollinations: {e}", exc_info=True)
            return None
    
    async def _generate_huggingface(
        self,
        prompt: str,
        model: Optional[str] = None,
        width: int = 512,
        height: int = 512
    ) -> Optional[bytes]:
        """Генерация через Hugging Face API"""
        try:
            model = model or HF_DEFAULT_MODEL
            url = f"{HF_BASE_URL}/{model}"
            
            headers = {}
            if self.hf_api_key:
                headers["Authorization"] = f"Bearer {self.hf_api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "width": width,
                    "height": height,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.info(f"Изображение сгенерировано через HuggingFace ({len(image_data)} байт)")
                        return image_data
                    elif response.status == 503:
                        # Модель загружается, ждем
                        logger.info("Модель загружается, ждем...")
                        await asyncio.sleep(10)
                        return await self._generate_huggingface(prompt, model, width, height)
                    else:
                        error = await response.text()
                        logger.error(f"HuggingFace error {response.status}: {error}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка генерации через HuggingFace: {e}")
            return None


# Глобальный экземпляр генератора
_image_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """Получает или создает экземпляр генератора изображений"""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator

