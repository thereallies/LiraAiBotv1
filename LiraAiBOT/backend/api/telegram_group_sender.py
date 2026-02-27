"""
Модуль для отправки сообщений в группы Telegram.
"""
import logging
from typing import List, Optional
import aiohttp

from backend.config import TELEGRAM_CONFIG
from backend.utils.group_manager import get_all_group_ids
from backend.api.telegram_core import send_telegram_message, send_telegram_photo, send_telegram_audio

logger = logging.getLogger("bot.telegram.group_sender")

TELEGRAM_API_URL = "https://api.telegram.org/bot"


async def send_message_to_all_groups(text: str, token: Optional[str] = None) -> dict:
    """
    Отправляет сообщение во все зарегистрированные группы.
    
    Args:
        text: Текст сообщения
        token: Токен бота (если не указан, используется первый доступный)
        
    Returns:
        Словарь с результатами: {"success": [group_ids], "failed": [group_ids]}
    """
    group_ids = get_all_group_ids()
    
    if not group_ids:
        logger.warning("Нет зарегистрированных групп для отправки сообщений")
        return {"success": [], "failed": []}
    
    # Получаем токен
    if not token:
        tokens = TELEGRAM_CONFIG.get("tokens", [])
        if not tokens:
            token = TELEGRAM_CONFIG.get("token")
        else:
            token = tokens[0]
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return {"success": [], "failed": group_ids}
    
    success = []
    failed = []
    
    for group_id in group_ids:
        try:
            result = await send_telegram_message(group_id, text, token=token)
            if result:
                success.append(group_id)
                logger.info(f"✅ Сообщение отправлено в группу {group_id}")
            else:
                failed.append(group_id)
                logger.warning(f"❌ Не удалось отправить сообщение в группу {group_id}")
        except Exception as e:
            failed.append(group_id)
            logger.error(f"❌ Ошибка при отправке в группу {group_id}: {e}")
    
    logger.info(f"📤 Отправка завершена: {len(success)} успешно, {len(failed)} ошибок")
    return {"success": success, "failed": failed}


async def send_message_to_group(group_id: str, text: str, token: Optional[str] = None) -> bool:
    """
    Отправляет сообщение в конкретную группу.
    
    Args:
        group_id: ID группы
        text: Текст сообщения
        token: Токен бота (если не указан, используется первый доступный)
        
    Returns:
        True если успешно, False иначе
    """
    return await send_telegram_message(group_id, text, token=token)


async def send_photo_to_all_groups(photo_path: str, caption: Optional[str] = None, token: Optional[str] = None) -> dict:
    """
    Отправляет фото во все зарегистрированные группы.
    
    Args:
        photo_path: Путь к файлу фото
        caption: Подпись к фото
        token: Токен бота (если не указан, используется первый доступный)
        
    Returns:
        Словарь с результатами: {"success": [group_ids], "failed": [group_ids]}
    """
    group_ids = get_all_group_ids()
    
    if not group_ids:
        logger.warning("Нет зарегистрированных групп для отправки фото")
        return {"success": [], "failed": []}
    
    # Получаем токен
    if not token:
        tokens = TELEGRAM_CONFIG.get("tokens", [])
        if not tokens:
            token = TELEGRAM_CONFIG.get("token")
        else:
            token = tokens[0]
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не настроен")
        return {"success": [], "failed": group_ids}
    
    success = []
    failed = []
    
    for group_id in group_ids:
        try:
            result = await send_telegram_photo(group_id, photo_path, caption, token=token)
            if result:
                success.append(group_id)
                logger.info(f"✅ Фото отправлено в группу {group_id}")
            else:
                failed.append(group_id)
                logger.warning(f"❌ Не удалось отправить фото в группу {group_id}")
        except Exception as e:
            failed.append(group_id)
            logger.error(f"❌ Ошибка при отправке фото в группу {group_id}: {e}")
    
    return {"success": success, "failed": failed}

