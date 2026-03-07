"""
Модуль для преобразования речи в текст через Groq Whisper.
"""
import logging
import os
from pathlib import Path
from typing import Optional

import aiohttp

logger = logging.getLogger("bot.stt")


class SpeechToText:
    """Класс для преобразования речи в текст через Groq STT."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.default_model = "whisper-large-v3-turbo"
        self.fallback_model = "whisper-large-v3"

        self.temp_dir = Path(__file__).parent.parent.parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)

        if self.api_key:
            logger.info("✅ Groq Whisper STT инициализирован")
        else:
            logger.warning("❌ GROQ_API_KEY не настроен для STT")

    async def speech_to_text(self, audio_path: str, language: str = "ru") -> str:
        """
        Преобразует речь в текст через Groq Whisper.
        """
        if not self.api_key:
            logger.error("STT не доступен - GROQ_API_KEY не настроен")
            return ""

        if not os.path.exists(audio_path):
            logger.error(f"Аудиофайл не найден: {audio_path}")
            return ""

        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            logger.error("Аудиофайл пустой")
            return ""

        logger.info(f"🎤 Groq STT обрабатывает {audio_path} ({file_size} байт)")

        for model in (self.default_model, self.fallback_model):
            text = await self._transcribe_with_model(audio_path, model, language)
            if text:
                return text

        return ""

    async def _transcribe_with_model(self, audio_path: str, model: str, language: str) -> str:
        """Один запрос на транскрибацию через выбранную модель."""
        url = f"{self.base_url}/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with aiohttp.ClientSession() as session:
                with open(audio_path, "rb") as audio_file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("model", model)
                    form_data.add_field("language", language)
                    form_data.add_field("response_format", "json")
                    form_data.add_field(
                        "file",
                        audio_file,
                        filename=Path(audio_path).name,
                        content_type="audio/ogg"
                    )

                    async with session.post(
                        url,
                        headers=headers,
                        data=form_data,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.warning(f"⚠️ Groq STT {model} ошибка {response.status}: {error_text[:200]}")
                            return ""

                        payload = await response.json()
                        text = (payload.get("text") or "").strip()
                        if text:
                            logger.info(f"✅ Groq STT {model}: {text[:120]}")
                        return text
        except Exception as e:
            logger.error(f"❌ Ошибка Groq STT ({model}): {e}")
            return ""

    async def process_voice_message(self, file_path: str) -> str:
        """Совместимый helper для старых вызовов."""
        return await self.speech_to_text(file_path)
