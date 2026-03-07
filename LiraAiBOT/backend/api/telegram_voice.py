"""
Модуль для обработки голосовых сообщений в Telegram боте.
"""
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

from backend.voice.stt import SpeechToText
from backend.voice.tts import TextToSpeech

logger = logging.getLogger("bot.telegram.voice")

# Глобальные экземпляры движков
stt_engine = None
tts_engine = None


def get_stt_engine() -> SpeechToText:
    """Получает экземпляр STT движка"""
    global stt_engine
    if stt_engine is None:
        stt_engine = SpeechToText()
    return stt_engine


def get_tts_engine() -> TextToSpeech:
    """Получает экземпляр TTS движка"""
    global tts_engine
    if tts_engine is None:
        tts_engine = TextToSpeech()
    return tts_engine


async def process_telegram_voice(
    message: Dict[str, Any],
    chat_id: str,
    user_id: str,
    temp_dir: Path,
    download_telegram_file,
    send_telegram_message,
    send_telegram_audio
) -> Optional[str]:
    """
    Обрабатывает голосовое сообщение из Telegram.
    
    Args:
        message: Сообщение из Telegram
        chat_id: ID чата
        user_id: ID пользователя
        temp_dir: Директория для временных файлов
        download_telegram_file: Функция для скачивания файлов из Telegram
        send_telegram_message: Функция для отправки сообщений в Telegram
        send_telegram_audio: Функция для отправки аудио в Telegram
        
    Returns:
        Распознанный текст или None при ошибке
    """
    try:
        # Получаем голосовое сообщение или аудио
        voice = message.get("voice") or message.get("audio")
        if not voice:
            logger.warning(f"Сообщение не содержит голосового сообщения: {message}")
            return None
        
        file_id = voice.get("file_id")
        if not file_id:
            logger.warning(f"Не удалось получить file_id голосового сообщения: {voice}")
            return None
        
        logger.info(f"Получено голосовое сообщение от {chat_id}, file_id: {file_id}")
        
        # Отправляем сообщение о начале обработки
        await send_telegram_message(chat_id, "🎤 Распознаю речь...")
        
        # Скачиваем аудиофайл
        local_path = temp_dir / f"voice_{os.getpid()}.ogg"
        downloaded_path = await download_telegram_file(file_id, local_path)
        
        if not downloaded_path:
            logger.error(f"Не удалось скачать голосовое сообщение: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось скачать голосовое сообщение.")
            return None
        
        # Распознаем речь
        stt = get_stt_engine()
        text = await stt.speech_to_text(downloaded_path, language="ru")
        
        # Удаляем временный файл
        try:
            os.remove(downloaded_path)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
        
        if not text:
            logger.error(f"Не удалось распознать речь: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось распознать речь.")
            return None
        
        # Отправляем распознанный текст
        await send_telegram_message(chat_id, f"🎤 <b>Распознанный текст:</b>\n\n{text}", "HTML")

        # Обрабатываем текст через LLM и даем ответ
        logger.info(f"[VOICE] Распознан текст: {text[:100]}...")

        try:
            # Получаем выбранную пользователем модель из хранилища
            # Импортируем хранилище моделей
            from backend.api.telegram_polling import user_models, AVAILABLE_MODELS
            model_key = user_models.get(user_id, "groq-llama")
            model_info = AVAILABLE_MODELS.get(model_key, ("groq", "openai/gpt-oss-20b"))

            # Извлекаем тип клиента и название модели из кортежа
            client_type, model = model_info

            # Определяем какой клиент использовать
            use_groq = client_type == "groq"

            logger.info(f"[VOICE] Используем модель: {model} (client: {'Groq' if use_groq else 'OpenRouter'}) для пользователя {user_id}")

            # Системный промпт
            system_prompt = "Ты - полезный ассистент LiraAI MultiAssistant. Отвечай на русском языке кратко и по делу."

            # Запрашиваем ответ от LLM
            logger.info(f"[VOICE] Отправляю запрос в LLM: {text[:50]}...")

            # Выбираем правильный клиент
            if use_groq:
                from backend.llm.groq import get_groq_client
                llm_client = get_groq_client()
            else:
                from backend.llm.openrouter import OpenRouterClient
                from backend.config import Config
                config = Config()
                llm_client = OpenRouterClient(config)

            response = await llm_client.chat_completion(
                user_message=text,
                system_prompt=system_prompt,
                chat_history=None,  # Для голосовых не используем историю
                model=model,
                temperature=0.7,
                max_tokens=512
            )

            logger.info(f"[VOICE] Получен ответ от LLM: {len(response)} символов")

            # Отправляем ответ только если он не пустой
            if response and response.strip():
                await send_telegram_message(chat_id, f"💬 <b>Ответ:</b>\n\n{response}", "HTML")

                # Дополнительно озвучиваем ответ через бесплатный gTTS
                try:
                    tts = get_tts_engine()
                    audio_path = await tts.text_to_speech(response, language="ru")
                    if audio_path:
                        await send_telegram_audio(chat_id, audio_path, caption="🔊 Голосовой ответ")
                        try:
                            os.remove(audio_path)
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"[VOICE] Не удалось озвучить ответ через gTTS: {e}")
            else:
                logger.warning("[VOICE] Пустой ответ от LLM")
                await send_telegram_message(chat_id, "⚠️ Пустой ответ от LLM")
            
        except Exception as e:
            logger.error(f"[VOICE] Ошибка при обработке через LLM: {e}", exc_info=True)
            await send_telegram_message(chat_id, f"❌ Ошибка LLM: {str(e)[:100]}")
            # Не показываем ошибку пользователю, так как текст уже отправлен
        
        return text
        
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await send_telegram_message(chat_id, "❌ Произошла ошибка при обработке голосового сообщения.")
        return None
