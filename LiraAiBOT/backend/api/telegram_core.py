"""
Модуль для базовой интеграции с Telegram.
"""
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from pathlib import Path

from backend.config import TELEGRAM_CONFIG, TELEGRAM_BOT_TOKENS

logger = logging.getLogger("bot.telegram")

TELEGRAM_API_URL = "https://api.telegram.org/bot"

# Глобальное хранилище для связи chat_id -> token
_chat_to_token = {}


def get_token_for_chat(chat_id: str) -> str:
    """Получает токен для чата (использует первый доступный, если не установлен)"""
    if chat_id in _chat_to_token:
        return _chat_to_token[chat_id]
    
    # По умолчанию используем первый токен
    tokens = TELEGRAM_CONFIG.get("tokens", [])
    if not tokens:
        token = TELEGRAM_CONFIG.get("token")
        if token:
            return token
    return tokens[0] if tokens else ""


def set_token_for_chat(chat_id: str, token: str):
    """Устанавливает токен для конкретного чата"""
    _chat_to_token[chat_id] = token


def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """
    Разбивает длинное сообщение на части для отправки в Telegram.
    Telegram лимит: 4096 символов, используем 4000 для безопасности.
    
    Args:
        text: Текст для разбивки
        max_length: Максимальная длина одной части
        
    Returns:
        Список частей сообщения
    """
    text_len = len(text)
    if text_len <= max_length:
        logger.debug(f"Сообщение не требует разбивки: {text_len} символов")
        return [text]
    
    logger.info(f"Разбиваю длинное сообщение: {text_len} символов на части по {max_length}")
    
    parts = []
    current_part = ""
    
    # Разбиваем по абзацам (двойной перенос строки)
    paragraphs = text.split("\n\n")
    
    for paragraph in paragraphs:
        # Если текущая часть + новый абзац помещается
        if len(current_part) + len(paragraph) + 2 <= max_length:
            if current_part:
                current_part += "\n\n" + paragraph
            else:
                current_part = paragraph
        else:
            # Если текущая часть не пуста, сохраняем её
            if current_part:
                parts.append(current_part)
            
            # Если сам абзац длиннее лимита, разбиваем по строкам
            if len(paragraph) > max_length:
                lines = paragraph.split("\n")
                current_part = ""
                for line in lines:
                    if len(current_part) + len(line) + 1 <= max_length:
                        if current_part:
                            current_part += "\n" + line
                        else:
                            current_part = line
                    else:
                        if current_part:
                            parts.append(current_part)
                        # Если строка сама длиннее лимита, обрезаем
                        while len(line) > max_length:
                            parts.append(line[:max_length])
                            line = line[max_length:]
                        current_part = line
            else:
                current_part = paragraph
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part)
    
    result = parts if parts else [text[:max_length]]
    logger.info(f"Сообщение разбито на {len(result)} частей: {[len(p) for p in result]} символов каждая")
    return result


async def send_telegram_message(
    chat_id: str,
    text: str,
    parse_mode: Optional[str] = None,
    reply_to_message_id: Optional[int] = None,
    token: Optional[str] = None,
    reply_markup: Optional[Dict] = None
) -> bool:
    """
    Отправляет текстовое сообщение в Telegram.
    Автоматически разбивает длинные сообщения на части.

    Args:
        chat_id: ID чата
        text: Текст сообщения
        parse_mode: Режим парсинга (HTML, Markdown)
        reply_to_message_id: ID сообщения для ответа
        token: Токен бота (если не указан, используется токен для чата)
        reply_markup: Клавиатура (reply или inline)

    Returns:
        True если успешно, False иначе
    """
    if not token:
        token = get_token_for_chat(chat_id)
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    # Разбиваем длинное сообщение на части
    message_parts = split_long_message(text)
    
    logger.info(f"Отправляю сообщение в чат {chat_id}: {len(message_parts)} частей, общая длина {len(text)} символов")
    
    url = f"{TELEGRAM_API_URL}{token}/sendMessage"
    
    success = True
    for i, part in enumerate(message_parts):
        logger.debug(f"Отправка части {i+1}/{len(message_parts)}: {len(part)} символов")
        
        payload = {
            "chat_id": chat_id,
            "text": part,
        }

        if parse_mode:
            payload["parse_mode"] = parse_mode

        # Ответ только на первое сообщение
        if i == 0 and reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
            logger.debug(f"Ответ на сообщение {reply_to_message_id}")
        
        # Добавляем клавиатуру если есть
        if reply_markup and i == 0:
            payload["reply_markup"] = reply_markup
            logger.debug(f"Добавлена клавиатура: {reply_markup.get('keyboard', [[]])}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        logger.info(f"✅ Часть {i+1}/{len(message_parts)} успешно отправлена в чат {chat_id}")
                        # Небольшая задержка между частями
                        if i < len(message_parts) - 1:
                            import asyncio
                            await asyncio.sleep(0.3)
                            logger.debug(f"Задержка перед отправкой части {i+2}")
                    else:
                        error = await response.text()
                        logger.error(f"❌ Ошибка отправки сообщения (часть {i+1}/{len(message_parts)}): {error}")
                        success = False
        except Exception as e:
            logger.error(f"❌ Исключение при отправке сообщения (часть {i+1}/{len(message_parts)}): {e}")
            success = False
    
    if success:
        logger.info(f"✅ Все {len(message_parts)} частей сообщения успешно отправлены в чат {chat_id}")
    else:
        logger.warning(f"⚠️ Не все части сообщения отправлены в чат {chat_id}")
    
    return success




async def send_telegram_message_with_buttons(
    chat_id: str,
    text: str,
    buttons: List[List[Dict[str, str]]],
    token: Optional[str] = None
) -> Optional[int]:
    """
    Отправляет сообщение с inline кнопками и возвращает message_id при успехе.
    Поддерживает два типа кнопок:
    - callback_data: для callback кнопок
    - url: для кнопок со ссылками

    Args:
        chat_id: ID чата
        text: Текст сообщения
        buttons: Список списков кнопок [[{"text": "...", "callback_data": "..."}] или [{"text": "...", "url": "..."}]]
        token: Токен бота (если не указан, используется токен для чата)

    Returns:
        message_id отправленного сообщения или None при ошибке
    """
    if not token:
        token = get_token_for_chat(chat_id)

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return None

    # Преобразуем кнопки в формат Telegram
    keyboard = {"inline_keyboard": []}
    for row in buttons:
        new_row = []
        for btn in row:
            if "url" in btn:
                # Кнопка со ссылкой
                new_row.append({"text": btn["text"], "url": btn["url"]})
            else:
                # Callback кнопка
                new_row.append({"text": btn["text"], "callback_data": btn["callback_data"]})
        keyboard["inline_keyboard"].append(new_row)

    url = f"{TELEGRAM_API_URL}{token}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard,
        "parse_mode": "Markdown"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    resp_json = await response.json()
                    message_id = resp_json.get("result", {}).get("message_id")
                    logger.info(f"✅ Сообщение с кнопками отправлено в чат {chat_id}, message_id: {message_id}")
                    return message_id
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка отправки сообщения с кнопками: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения с кнопками: {e}")
        return None


async def delete_telegram_message(
    chat_id: str,
    message_id: int,
    token: Optional[str] = None
) -> bool:
    """
    Удаляет сообщение в Telegram по chat_id и message_id.
    
    Args:
        chat_id: ID чата
        message_id: ID сообщения для удаления
        token: Токен бота (если не указан, используется токен для чата)
        
    Returns:
        True при успехе, False при ошибке
    """
    if not token:
        token = get_token_for_chat(chat_id)
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    url = f"{TELEGRAM_API_URL}{token}/deleteMessage"
    
    data = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info(f"✅ Сообщение {message_id} удалено из чата {chat_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.warning(f"⚠️ Не удалось удалить сообщение {message_id} в чате {chat_id}: {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при удалении сообщения {message_id} в чате {chat_id}: {e}")
        return False


async def answer_callback_query(
    callback_query_id: str,
    text: Optional[str] = None,
    token: Optional[str] = None
) -> bool:
    """
    Отвечает на callback query (убирает "часики" у кнопки).
    
    Args:
        callback_query_id: ID callback query
        text: Текст ответа (опционально)
        token: Токен бота (если не указан, используется первый доступный)
        
    Returns:
        True при успехе, False при ошибке
    """
    if not token:
        tokens = TELEGRAM_CONFIG.get("tokens", [])
        if not tokens:
            token = TELEGRAM_CONFIG.get("token")
        else:
            token = tokens[0]
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    url = f"{TELEGRAM_API_URL}{token}/answerCallbackQuery"
    
    data = {
        "callback_query_id": callback_query_id
    }
    
    if text:
        data["text"] = text
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.debug(f"✅ Callback query {callback_query_id} обработан")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка ответа на callback query: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Исключение при ответе на callback query: {e}")
        return False


async def edit_message_text(
    chat_id: str,
    message_id: int,
    text: str,
    parse_mode: Optional[str] = "Markdown",
    token: Optional[str] = None,
    buttons: Optional[list] = None
) -> bool:
    """
    Редактирует текст сообщения.

    Args:
        chat_id: ID чата
        message_id: ID сообщения для редактирования
        text: Новый текст сообщения
        parse_mode: Режим парсинга (HTML, Markdown)
        token: Токен бота (если не указан, используется токен для чата)
        buttons: Кнопки инлайн [[{"text": "...", "callback_data": "..."}]]

    Returns:
        True если успешно, False иначе
    """
    if not token:
        token = get_token_for_chat(chat_id)

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False

    url = f"{TELEGRAM_API_URL}{token}/editMessageText"

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode

    # Добавляем кнопки если есть
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"✅ Сообщение {message_id} отредактировано в чате {chat_id}")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Ошибка редактирования сообщения: {error}")
                    return False
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        return False


async def send_telegram_photo(
    chat_id: str,
    photo_path: str,
    caption: Optional[str] = None,
    token: Optional[str] = None
) -> bool:
    """
    Отправляет фото в Telegram.
    
    Args:
        chat_id: ID чата
        photo_path: Путь к файлу фото
        caption: Подпись к фото
        token: Токен бота (если не указан, используется токен для чата)
        
    Returns:
        True если успешно, False иначе
    """
    if not token:
        token = get_token_for_chat(chat_id)
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    url = f"{TELEGRAM_API_URL}{token}/sendPhoto"
    
    try:
        with open(photo_path, "rb") as photo_file:
            form_data = aiohttp.FormData()
            form_data.add_field("chat_id", str(chat_id))
            form_data.add_field("photo", photo_file, filename=Path(photo_path).name)
            if caption:
                form_data.add_field("caption", caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form_data) as response:
                    if response.status == 200:
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Ошибка отправки фото: {error}")
                        return False
    except Exception as e:
        logger.error(f"Ошибка при отправке фото: {e}")
        return False


async def send_telegram_audio(
    chat_id: str,
    audio_path: str,
    caption: Optional[str] = None,
    token: Optional[str] = None
) -> bool:
    """
    Отправляет аудиофайл в Telegram.
    
    Args:
        chat_id: ID чата
        audio_path: Путь к аудиофайлу
        caption: Подпись к аудио
        token: Токен бота (если не указан, используется токен для чата)
        
    Returns:
        True если успешно, False иначе
    """
    if not token:
        token = get_token_for_chat(chat_id)
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    url = f"{TELEGRAM_API_URL}{token}/sendAudio"
    
    try:
        with open(audio_path, "rb") as audio_file:
            form_data = aiohttp.FormData()
            form_data.add_field("chat_id", str(chat_id))
            form_data.add_field("audio", audio_file, filename=Path(audio_path).name)
            if caption:
                form_data.add_field("caption", caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form_data) as response:
                    if response.status == 200:
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Ошибка отправки аудио: {error}")
                        return False
    except Exception as e:
        logger.error(f"Ошибка при отправке аудио: {e}")
        return False


async def send_chat_action(chat_id: str, action: str = "typing", token: Optional[str] = None) -> bool:
    """
    Отправляет статус действия в чат (печатает, отправляет фото и т.д.).
    
    Args:
        chat_id: ID чата
        action: Тип действия (typing, upload_photo, record_video, upload_video, 
                record_voice, upload_voice, upload_document, choose_sticker, find_location)
        token: Токен бота (если не указан, используется токен для чата)
    
    Returns:
        True если успешно, False при ошибке
    """
    if not token:
        token = get_token_for_chat(chat_id)
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return False
    
    url = f"{TELEGRAM_API_URL}{token}/sendChatAction"
    
    data = {
        "chat_id": chat_id,
        "action": action
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.debug(f"✅ Статус '{action}' отправлен в чат {chat_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка отправки статуса действия: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке статуса действия: {e}")
        return False


async def download_telegram_file(file_id: str, save_path: Path, token: Optional[str] = None) -> Optional[str]:
    """
    Скачивает файл из Telegram.
    
    Args:
        file_id: ID файла в Telegram
        save_path: Путь для сохранения файла
        token: Токен бота (если не указан, используется первый доступный)
        
    Returns:
        Путь к скачанному файлу или None
    """
    if not token:
        tokens = TELEGRAM_CONFIG.get("tokens", [])
        if not tokens:
            token = TELEGRAM_CONFIG.get("token")
        else:
            token = tokens[0]
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return None
    
    # Получаем информацию о файле
    get_file_url = f"{TELEGRAM_API_URL}{token}/getFile?file_id={file_id}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(get_file_url) as response:
                if response.status == 200:
                    file_info = await response.json()
                    if file_info.get("ok"):
                        file_path = file_info["result"]["file_path"]
                        
                        # Скачиваем файл
                        download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                        async with session.get(download_url) as download_response:
                            if download_response.status == 200:
                                save_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(save_path, "wb") as f:
                                    async for chunk in download_response.content.iter_chunked(8192):
                                        f.write(chunk)
                                logger.info(f"Файл скачан: {save_path}")
                                return str(save_path)
                            else:
                                logger.error(f"Ошибка скачивания файла: {download_response.status}")
                                return None
                    else:
                        logger.error(f"Ошибка получения информации о файле: {file_info}")
                        return None
                else:
                    error = await response.text()
                    logger.error(f"Ошибка запроса файла: {error}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {e}")
        return None

