"""
Модуль для преобразования текста в речь (Text-to-Speech).
"""
import os
import logging
import tempfile
from typing import Optional
from pathlib import Path

logger = logging.getLogger("bot.tts")


class TextToSpeech:
    """Класс для преобразования текста в речь"""
    
    def __init__(self):
        """Инициализирует TTS движок"""
        self.use_gtts = False
        self.use_elevenlabs = False
        
        # Создаем папку для временных файлов
        self.temp_dir = Path(__file__).parent.parent.parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Проверяем ElevenLabs (поддержка нескольких ключей)
        self.eleven_api_keys = []
        # Собираем все ключи
        key1 = os.getenv("ELEVEN_API_KEY") or os.getenv("ELEVEN_API")
        if key1:
            self.eleven_api_keys.append(key1)
        for i in range(2, 5):
            key = os.getenv(f"ELEVEN_API{i}")
            if key:
                self.eleven_api_keys.append(key)
        
        eleven_voice_id = os.getenv("ELEVEN_VOICE_ID")
        if self.eleven_api_keys and eleven_voice_id:
            self.eleven_api_key = self.eleven_api_keys[0]  # Текущий ключ
            self.eleven_key_index = 0
            self.eleven_voice_id = eleven_voice_id
            self.eleven_model_id = os.getenv("ELEVEN_MODEL_ID", "eleven_multilingual_v2")
            self.use_elevenlabs = True
            logger.info(f"ElevenLabs TTS инициализирован с {len(self.eleven_api_keys)} ключами")
        
        # Fallback на gTTS
        if not self.use_elevenlabs:
            try:
                from gtts import gTTS
                self.use_gtts = True
                logger.info("gTTS инициализирован как fallback")
            except ImportError:
                logger.warning("gTTS не установлен")
    
    async def text_to_speech(self, text: str, language: str = "ru") -> Optional[str]:
        """
        Преобразует текст в речь.
        
        Args:
            text: Текст для озвучивания
            language: Язык (ru, en, etc.)
            
        Returns:
            Путь к аудиофайлу или None
        """
        try:
            # Используем ElevenLabs если доступен
            if self.use_elevenlabs:
                return await self._elevenlabs_tts(text)
            
            # Fallback на gTTS
            if self.use_gtts:
                return self._gtts_tts(text, language)
            
            logger.error("Нет доступных TTS движков")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при TTS: {e}")
            return None
    
    def _rotate_eleven_key(self):
        """Ротация ElevenLabs ключей"""
        if len(self.eleven_api_keys) > 1:
            self.eleven_key_index = (self.eleven_key_index + 1) % len(self.eleven_api_keys)
            self.eleven_api_key = self.eleven_api_keys[self.eleven_key_index]
            logger.debug(f"Переключение на ElevenLabs ключ #{self.eleven_key_index + 1}")
    
    async def _elevenlabs_tts(self, text: str) -> Optional[str]:
        """Генерация речи через ElevenLabs"""
        try:
            import aiohttp
            
            max_attempts = len(self.eleven_api_keys) if self.eleven_api_keys else 1
            for attempt in range(max_attempts):
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.eleven_voice_id}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.eleven_api_key
                }
                data = {
                    "text": text,
                    "model_id": self.eleven_model_id,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5
                    }
                }
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=data, headers=headers) as response:
                            if response.status == 200:
                                audio_data = await response.read()
                                output_path = self.temp_dir / f"tts_{os.getpid()}.mp3"
                                with open(output_path, "wb") as f:
                                    f.write(audio_data)
                                return str(output_path)
                            elif response.status == 401 or response.status == 429:
                                # Ошибка авторизации или rate limit - пробуем другой ключ
                                if attempt < max_attempts - 1:
                                    self._rotate_eleven_key()
                                    continue
                                else:
                                    error = await response.text()
                                    logger.error(f"ElevenLabs error: {error}")
                                    return None
                            else:
                                error = await response.text()
                                logger.error(f"ElevenLabs error {response.status}: {error}")
                                return None
                except Exception as e:
                    if attempt < max_attempts - 1:
                        self._rotate_eleven_key()
                        continue
                    raise
            
            return None
                        
        except Exception as e:
            logger.error(f"Ошибка ElevenLabs TTS: {e}")
            return None
    
    def _gtts_tts(self, text: str, language: str) -> Optional[str]:
        """Генерация речи через gTTS"""
        try:
            from gtts import gTTS
            
            output_path = self.temp_dir / f"tts_{os.getpid()}.mp3"
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(output_path))
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Ошибка gTTS: {e}")
            return None

