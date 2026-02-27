"""
Модуль для обработки фото с кнопками выбора режима распознавания.
"""
import logging
import asyncio
import os
from typing import Dict, Any, Optional
from pathlib import Path

from backend.api.telegram_core import (
    send_telegram_message_with_buttons,
    send_telegram_message,
    delete_telegram_message
)
from backend.vision.image_analyzer import ImageAnalyzer
from backend.config import Config

logger = logging.getLogger("bot.telegram.photo_handler")

# Простое хранилище для фото (вместо БД)
_pending_photos: Dict[str, Dict[int, Dict[str, Any]]] = {}


def save_pending_photo(chat_id: str, message_id: int, photo_message: Dict[str, Any]):
    """Сохраняет сообщение с фото для последующей обработки"""
    if chat_id not in _pending_photos:
        _pending_photos[chat_id] = {}
    _pending_photos[chat_id][message_id] = photo_message
    logger.debug(f"Сохранено фото: chat_id={chat_id}, message_id={message_id}")


def get_pending_photo(chat_id: str, message_id: int) -> Optional[Dict[str, Any]]:
    """Получает сохраненное сообщение с фото"""
    if chat_id in _pending_photos and message_id in _pending_photos[chat_id]:
        return _pending_photos[chat_id][message_id]
    return None


def delete_pending_photo(chat_id: str, message_id: int):
    """Удаляет сохраненное сообщение с фото"""
    if chat_id in _pending_photos and message_id in _pending_photos[chat_id]:
        del _pending_photos[chat_id][message_id]
        logger.debug(f"Удалено фото: chat_id={chat_id}, message_id={message_id}")


async def send_photo_recognition_buttons(chat_id: str, message_id: int):
    """Отправляет две кнопки для распознавания фото: как изображение и как текст."""
    buttons = [
        [{"text": "Распознать как изображение", "callback_data": f"photo_img_{message_id}"}],
        [{"text": "Распознать как текст", "callback_data": f"photo_text_{message_id}"}]
    ]
    sent_msg_id = await send_telegram_message_with_buttons(
        chat_id,
        "Что сделать с этим фото?",
        buttons
    )
    # Планируем авто-удаление подсказки через 10 секунд
    if isinstance(sent_msg_id, int):
        async def _auto_delete():
            try:
                await asyncio.sleep(10)
                await delete_telegram_message(chat_id, sent_msg_id)
                logger.debug(f"Авто-удаление кнопок: chat_id={chat_id}, message_id={sent_msg_id}")
            except Exception as e:
                # Тихо игнорируем любые ошибки удаления
                logger.debug(f"Ошибка авто-удаления кнопок (игнорируем): {e}")
        asyncio.create_task(_auto_delete())


async def handle_photo_callback(
    callback_query: Dict[str, Any],
    callback_data: str,
    chat_id: str,
    message_id: int,
    user_id: str,
    temp_dir: Path,
    download_telegram_file_func,
    config: Config
) -> bool:
    """
    Обрабатывает callback-кнопки для фото: как изображение и как текст.
    message_id должен браться только из callback_data (photo_img_12345), а не из callback_query['message']['message_id']!
    """
    # Получаем message_id из callback_data (например, photo_text_10996)
    if callback_data.startswith("photo_img_"):
        real_message_id = int(callback_data.replace("photo_img_", ""))
        logger.info(f"[PHOTO CALLBACK] Распознать как изображение: chat_id={chat_id}, message_id={real_message_id}")
        
        photo_message = get_pending_photo(chat_id, real_message_id)
        if photo_message:
            photos = photo_message.get("photo", [])
            if not photos:
                await send_telegram_message(chat_id, "❌ Не удалось найти фото для анализа.")
                return True
            
            photo = photos[-1]
            file_id = photo.get("file_id")
            if not file_id:
                await send_telegram_message(chat_id, "❌ Не удалось получить file_id фото.")
                return True
            
            await send_telegram_message(chat_id, "🔍 Анализирую изображение...")
            
            # Скачиваем фото
            local_path = temp_dir / f"photo_img_{os.getpid()}.jpg"
            downloaded_path = await download_telegram_file_func(file_id, local_path)
            
            if not downloaded_path:
                await send_telegram_message(chat_id, "❌ Не удалось скачать фото для анализа.")
                return True
            
            # Анализируем изображение (просто описание, БЕЗ FeedbackBot)
            analyzer = ImageAnalyzer(config)
            chat_type = photo_message.get("chat", {}).get("type", "private")
            if chat_type in ("group", "supergroup"):
                prompt = "Что на этом изображении? Опиши подробно, но кратко. Используй русский язык."
            else:
                prompt = "Что на этом изображении? Опиши подробно, обращая внимание на детали. Используй русский язык."
            
            description = await analyzer.analyze_image(downloaded_path, prompt)
            
            # Удаляем временный файл
            try:
                os.remove(downloaded_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
            
            if description:
                await send_telegram_message(chat_id, f"👁️ <b>Я вижу на изображении:</b>\n\n{description}", "HTML")
            else:
                await send_telegram_message(chat_id, "❌ Не удалось проанализировать изображение.")
            
            delete_pending_photo(chat_id, real_message_id)
        else:
            await send_telegram_message(chat_id, "⚠️ Сообщение с фото не найдено или устарело")
        return True
        
    elif callback_data.startswith("photo_text_"):
        real_message_id = int(callback_data.replace("photo_text_", ""))
        logger.info(f"[PHOTO CALLBACK] Распознать как текст: chat_id={chat_id}, message_id={real_message_id}")
        
        photo_message = get_pending_photo(chat_id, real_message_id)
        if photo_message:
            photos = photo_message.get("photo", [])
            if not photos:
                await send_telegram_message(chat_id, "❌ Не удалось найти фото для распознавания текста.")
                return True
            
            photo = photos[-1]
            file_id = photo.get("file_id")
            if not file_id:
                await send_telegram_message(chat_id, "❌ Не удалось получить file_id фото.")
                return True
            
            await send_telegram_message(chat_id, "🔍 Распознаю текст на изображении...")
            
            # Скачиваем фото
            local_path = temp_dir / f"photo_text_{os.getpid()}.jpg"
            downloaded_path = await download_telegram_file_func(file_id, local_path)
            
            if not downloaded_path:
                await send_telegram_message(chat_id, "❌ Не удалось скачать фото для распознавания текста.")
                return True
            
            # Анализируем изображение для извлечения текста
            analyzer = ImageAnalyzer(config)
            prompt = "Найди и выпиши весь текст, который есть на этом изображении. Ответь строго в формате JSON: {\"text\": \"...\"}"
            result = await analyzer.analyze_image(downloaded_path, prompt)
            
            # Удаляем временный файл
            try:
                os.remove(downloaded_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
            
            text = None
            if result:
                try:
                    import re
                    import json
                    
                    # Предварительная обработка ответа модели
                    processed_result = result.strip()
                    
                    # СУПЕР ПРОСТОЙ ПОДХОД: берем весь текст между первой и последней кавычкой
                    if '"text":' in processed_result:
                        # Ищем первую кавычку после "text":
                        text_pos = processed_result.find('"text":')
                        if text_pos != -1:
                            # Ищем открывающую кавычку после "text":
                            start_quote = processed_result.find('"', text_pos + 7)
                            if start_quote != -1:
                                # Берем ВЕСЬ текст от открывающей кавычки до КОНЦА ответа
                                raw_text = processed_result[start_quote + 1:].strip()
                                
                                # Если текст заканчивается кавычкой - убираем ее
                                if raw_text.endswith('"'):
                                    raw_text = raw_text[:-1]
                                
                                # Обрабатываем escaped символы
                                text = raw_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                                
                                # Убираем возможные завершающие символы (}, ``` и т.д.)
                                text = text.split('}')[0].split('```')[0].strip()
                                
                                logger.info(f"[PHOTO TEXT] Найден текст длиной {len(text)} символов")
                    
                    # Пытаемся напрямую распарсить JSON
                    if not text:
                        try:
                            if processed_result.strip().startswith('{'):
                                direct_json = json.loads(processed_result.strip())
                                if isinstance(direct_json, dict) and "text" in direct_json:
                                    text = direct_json["text"].strip()
                                    logger.info(f"[PHOTO TEXT] Прямой парсинг сработал!")
                        except Exception:
                            pass
                    
                    # Fallback: regex
                    if not text:
                        text_match = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', processed_result, re.DOTALL)
                        if text_match:
                            text = text_match.group(1).strip()
                            text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                            logger.info(f"[PHOTO TEXT] Regex fallback сработал!")
                    
                except Exception as e:
                    logger.error(f"[PHOTO TEXT] Ошибка парсинга JSON: {e}. Ответ модели: {result[:200]}...")
            
            if text and text.strip():
                await send_telegram_message(chat_id, f"📝 <b>Распознанный текст:</b>\n\n{text}", "HTML")
            else:
                await send_telegram_message(chat_id, "❌ Не удалось корректно распознать текст на изображении.")
            
            delete_pending_photo(chat_id, real_message_id)
        else:
            await send_telegram_message(chat_id, "⚠️ Сообщение с фото не найдено или устарело")
        return True
    
    return False

