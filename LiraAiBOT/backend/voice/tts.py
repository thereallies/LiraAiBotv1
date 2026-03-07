"""
Модуль для преобразования текста в речь через gTTS.
"""
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("bot.tts")


class TextToSpeech:
    """Бесплатный TTS через gTTS."""

    def __init__(self):
        self.temp_dir = Path(__file__).parent.parent.parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        try:
            from gtts import gTTS  # noqa: F401
            self.available = True
            logger.info("✅ gTTS инициализирован для voice reply")
        except ImportError:
            self.available = False
            logger.warning("❌ gTTS не установлен")

    async def text_to_speech(self, text: str, language: str = "ru") -> Optional[str]:
        """Озвучивает текст через gTTS и возвращает путь к mp3."""
        if not self.available:
            return None

        try:
            from gtts import gTTS

            output_path = self.temp_dir / f"tts_{os.getpid()}.mp3"
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(output_path))
            return str(output_path)
        except Exception as e:
            logger.error(f"Ошибка gTTS: {e}")
            return None
