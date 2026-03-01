"""
Модуль для обработки Telegram polling.
"""
import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import aiohttp

from backend.config import TELEGRAM_CONFIG, Config
from backend.api.telegram_core import (
    send_telegram_message,
    send_telegram_photo,
    send_telegram_audio,
    download_telegram_file,
    send_chat_action,
    send_telegram_message_with_buttons,
    delete_telegram_message
)
from backend.api.telegram_vision import process_telegram_photo
from backend.api.telegram_voice import process_telegram_voice
from backend.llm.openrouter import OpenRouterClient
from backend.llm.groq import get_groq_client
from backend.llm.cerebras import get_cerebras_client
from backend.vision.gemini_image import get_gemini_image_client
from backend.vision.hf_replicate import get_hf_replicate_client
from backend.utils.keyboards import (
    create_main_menu_keyboard,
    create_hide_keyboard,
    create_model_selection_keyboard,
    create_image_model_selection_keyboard,
    get_mode_from_button,
    get_model_from_button,
    get_mode_prompt,
    BOT_MODES
)
from backend.utils.mode_manager import get_mode_manager
from backend.utils.group_manager import save_group_id_to_env, get_all_group_ids
from backend.core.feedback_bot import FeedbackBotHandler

logger = logging.getLogger("bot.telegram_polling")

TELEGRAM_API_URL = "https://api.telegram.org/bot"
last_update_id = 0

# Создаем папку для временных файлов
temp_dir = Path(__file__).parent.parent.parent / "temp"
temp_dir.mkdir(exist_ok=True)

# Инициализируем компоненты
config = Config()

# Создаем LLM клиент для OpenRouter (Solar, Trinity, GLM)
llm_client = OpenRouterClient(config)

# Создаем Groq клиент для быстрых моделей
groq_client = get_groq_client()

# Создаем Cerebras клиент для сверхбыстрых моделей
cerebras_client = get_cerebras_client()

# Создаем Gemini Image клиент для генерации изображений
gemini_image_client = get_gemini_image_client()

# Создаем HF+Replicate клиент для генерации изображений через FLUX
hf_replicate_client = get_hf_replicate_client()

# Инициализируем FeedbackBotHandler если включен
feedback_bot_handler = None
if config.FEEDBACK_BOT_ENABLED:
    try:
        feedback_bot_handler = FeedbackBotHandler(config)
        logger.info("FeedbackBotHandler инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации FeedbackBotHandler: {e}")

# Инициализируем менеджер режимов
mode_manager = get_mode_manager()
logger.info("✅ ModeManager инициализирован")

# Хранилище истории диалогов для FeedbackBot (по группам)
feedback_chat_history: Dict[str, List[Dict[str, str]]] = {}

# Хранилище выбранной модели для каждого пользователя
# По умолчанию используем OpenRouter Solar вместо Groq
user_models: Dict[str, str] = {}

# Хранилище выбранной модели генерации изображений
user_image_models: Dict[str, str] = {}

# Хранилище состояния для генерации изображений
user_generating_photo: Dict[str, bool] = {}

# Хранилище состояния для выбора модели
user_selecting_model: Dict[str, bool] = {}

# Глобальная переменная для режима тех.работ
maintenance_mode = {"enabled": False, "until_time": None}

# Хранилище истории диалогов удалено - теперь используется база данных

# Доступные модели для выбора
AVAILABLE_MODELS = {
    # Groq модели
    "groq-llama": ("groq", "llama-3.3-70b-versatile"),  # Groq Llama 3.3
    "groq-maverick": ("groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),  # Groq Llama 4 Maverick
    "groq-scout": ("groq", "meta-llama/llama-4-scout-17b-16e-instruct"),  # Groq Llama 4 Scout
    "groq-kimi": ("groq", "moonshotai/kimi-k2-instruct"),  # Groq Kimi K2
    # Cerebras модели
    "cerebras-llama": ("cerebras", "llama3.1-8b"),  # Cerebras Llama 3.1 8B
    # OpenRouter модели (fallback)
    "solar": ("openrouter", "upstage/solar-pro-3:free"),  # OpenRouter Solar Pro 3
    "trinity": ("openrouter", "arcee-ai/trinity-mini:free"),  # OpenRouter Trinity Mini
    "glm": ("openrouter", "z-ai/glm-4.5-air:free"),  # OpenRouter GLM-4.5
}


async def show_start_menu(chat_id: str):
    """Показывает стартовое меню с кнопками"""
    # Добавляем пользователя в базу
    from backend.database.users_db import get_database
    db = get_database()
    db.add_or_update_user(chat_id)

    buttons = [
        [
            {"text": "🤖 Выбрать модель", "callback_data": "menu_models"},
            {"text": "🎨 Генерировать фото", "callback_data": "gen_photo"},
        ],
        [
            {"text": "📸 Фото", "callback_data": "menu_photo"},
            {"text": "🎤 Голос", "callback_data": "menu_voice"},
        ],
        [
            {"text": "📊 Статистика", "callback_data": "stats"},
            {"text": "📢 Подписаться", "url": "https://t.me/liranexus"},
        ],
        [
            {"text": "ℹ️ Помощь", "callback_data": "help"},
        ]
    ]

    welcome_text = """👋 **Привет! Я LiraAI** 🤖

Я твой персональный AI-ассистент женского пола!

**Что я умею:**
• 💬 Общаться на русском языке
• 🎨 Генерировать изображения (Stable Diffusion 3)
• 🎤 Распознавать голосовые сообщения
• 📸 Анализировать фотографии

🆓 **Все модели БЕСПЛАТНЫЕ!**

⚡ **Groq (очень быстрые):**
• Llama 3.3 70B - лучшая для русского
• Llama 4 Maverick - новейшая от Meta
• Llama 4 Scout - легкая и быстрая
• Kimi K2 - от Moonshot AI

🚀 **Cerebras (сверхбыстрые):**
• Llama 3.1 8B - молниеносная

☁️ **OpenRouter (качественные):**
• Solar Pro 3 - быстрая и качественная
• Trinity Mini - мультимодальная
• GLM-4.5 - полностью бесплатная

🎨 **Генерация изображений:**
• Stable Diffusion 3 - работает ✅
• Gemini Image - в разработке ⚠️

**Обо мне:**
У меня есть один разработчик - Danil Alekseevich.
Познакомиться с ним можно в канале @liranexus (кнопка "📢 Подписаться").

[Подпишитесь](https://t.me/liranexus) чтобы следить за обновлениями!

━━━━━━━━━━━━━━━━━━━━
📱 **Начни с выбора модели** - нажми "🤖 Выбрать модель" ниже!
━━━━━━━━━━━━━━━━━━━━

Выбери команду ниже 👇"""

    await send_telegram_message_with_buttons(chat_id, welcome_text, buttons)


async def get_updates(token: str, offset: int = 0, timeout: int = 30) -> Dict[str, Any]:
    """Получает обновления из Telegram для конкретного токена"""
    if not token:
        logger.error("Токен не передан")
        return []
    
    url = f"{TELEGRAM_API_URL}{token}/getUpdates"
    params = {
        "offset": offset,
        "timeout": timeout,
        "allowed_updates": ["message", "callback_query", "channel_post"]
    }
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=35)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        return data.get("result", [])
                    else:
                        logger.error(f"Ошибка получения обновлений: {data}")
                        return []
                else:
                    error = await response.text()
                    # 502 Bad Gateway - временная ошибка, нужно повторить позже
                    if response.status == 502:
                        logger.warning(f"Telegram API 502 Bad Gateway (временная ошибка), повторю попытку...")
                        # Не логируем как ERROR, это временная проблема
                    else:
                        logger.error(f"HTTP ошибка получения обновлений ({response.status}): {error}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка при получении обновлений: {e}")
        return []


async def process_message(message: Dict[str, Any], bot_token: str):
    """Обрабатывает одно сообщение"""
    try:
        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))
        chat_type = chat.get("type", "private")
        user = message.get("from", {})
        user_id = str(user.get("id", ""))
        text = message.get("text", "")
        message_id = message.get("message_id")
        from_user = message.get("from", {})
        from_user_id = from_user.get("id")

        # Получаем данные пользователя из Telegram
        username = user.get("username", "")  # @username без @
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")

        logger.info(f"[{chat_type.upper()}] Получено сообщение от {user_id} в чате {chat_id}: {text[:50]}")

        # Добавляем/обновляем пользователя в базе с username
        from backend.database.users_db import get_database
        db = get_database()
        db.add_or_update_user(user_id, username=username, first_name=first_name, last_name=last_name)

        # Проверяем режим тех.работ (только для приватных чатов)
        if chat_type == "private":
            maint_status = db.get_maintenance_mode()
            maintenance_mode["enabled"] = maint_status["enabled"]
            maintenance_mode["until_time"] = maint_status["until_time"]
            
            # Проверяем время окончания тех.работ
            if maintenance_mode["enabled"] and maintenance_mode["until_time"]:
                try:
                    from datetime import datetime
                    until = datetime.strptime(maintenance_mode["until_time"], "%H:%M").time()
                    now = datetime.now().time()
                    if now > until:
                        # Время вышло - выключаем тех.работы
                        maintenance_mode["enabled"] = False
                        db.set_maintenance_mode(False)
                        logger.info("⚙️ Режим тех.работ автоматически выключен")
                except Exception as e:
                    logger.error(f"Ошибка проверки времени тех.работ: {e}")
            
            # Если тех.работы включены и пользователь не админ - блокируем
            if maintenance_mode["enabled"]:
                is_admin = db.is_admin(user_id)
                if not is_admin:
                    # Показываем сообщение о тех.работах
                    until_msg = f" до {maintenance_mode['until_time']}" if maintenance_mode["until_time"] else ""
                    await send_telegram_message(
                        chat_id,
                        f"🔧 **Технические работы{until_msg}**\n\nБот временно недоступен. Следите за обновлениями в канале @liranexus"
                    )
                    return  # Прерываем обработку
        
        # === ГРУППОВОЙ ЧАТ ===
        if chat_type in ("group", "supergroup"):
            # Автоматически сохраняем ID группы в .env
            try:
                saved = save_group_id_to_env(chat_id)
                if saved:
                    logger.info(f"🎉 Новая группа обнаружена и сохранена: {chat_id}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении ID группы: {e}")
            
            # Проверяем, является ли это группой для FeedbackBot
            is_feedback_group = (
                feedback_bot_handler is not None and
                config.FEEDBACK_BOT_ENABLED and
                chat_id in config.FEEDBACK_BOT_GROUP_IDS
            )
            
            if is_feedback_group:
                # В группах FeedbackBot обрабатываем ВСЕ текстовые сообщения
                if text:
                    # Извлекаем имя пользователя
                    user_name = None
                    if user:
                        first_name = user.get("first_name", "")
                        last_name = user.get("last_name", "")
                        username = user.get("username", "")
                        if first_name or last_name:
                            user_name = f"{first_name} {last_name}".strip()
                        elif username:
                            user_name = f"@{username}"
                    
                    await handle_feedback_bot_message(chat_id, user_id, text, is_group=True, user_name=user_name)
                    return
                # Для фото в группах FeedbackBot - показываем кнопки выбора режима
                if "photo" in message:
                    message_id = message.get("message_id")
                    if message_id:
                        # Сохраняем фото для последующей обработки
                        from backend.api.telegram_photo_handler import save_pending_photo, send_photo_recognition_buttons
                        save_pending_photo(chat_id, message_id, message)
                        # Показываем кнопки выбора режима
                        await send_photo_recognition_buttons(chat_id, message_id)
                        logger.info(f"[FeedbackBot] 📸 Показаны кнопки выбора режима для фото {message_id}")
                    return
                # Для голосовых в группах FeedbackBot - распознаем и передаем в FeedbackBot
                if "voice" in message or "audio" in message:
                    await handle_feedback_bot_voice(chat_id, user_id, message)
                    return
            
            # Для остальных групп - стандартная логика (только упоминания)
            # В группах реагируем только на упоминания бота или команды
            bot_username = None
            try:
                # Получаем информацию о боте
                import aiohttp
                bot_info_url = f"{TELEGRAM_API_URL}{bot_token}/getMe"
                async with aiohttp.ClientSession() as session:
                    async with session.get(bot_info_url) as response:
                        if response.status == 200:
                            bot_data = await response.json()
                            if bot_data.get("ok"):
                                bot_username = bot_data["result"].get("username")
            except Exception as e:
                logger.error(f"Ошибка получения информации о боте: {e}")
            
            # Проверяем упоминание
            is_mentioned = False
            if bot_username:
                is_mentioned = f"@{bot_username}" in text or text.startswith("/")
            
            # Если бот не упомянут и это не команда - игнорируем
            if not is_mentioned and text:
                return
            
            # Обрабатываем команды в группах
            if text:
                if text.startswith("/generate ") or text.startswith("/рисунок "):
                    prompt = text.replace("/generate ", "").replace("/рисунок ", "")
                    await handle_image_generation(chat_id, prompt)
                    return
                
                # Убираем упоминание бота из текста
                if bot_username and f"@{bot_username}" in text:
                    text = text.replace(f"@{bot_username}", "").strip()
                
                if not text or not text.strip():
                    return
                
                # Обрабатываем текстовое сообщение
                await handle_text_message(chat_id, user_id, text, is_group=True)
                return
            
            # В группах обрабатываем фото и голосовые сообщения только если бот упомянут
            if "photo" in message or "voice" in message or "audio" in message:
                # Для фото и голоса в группах тоже нужна проверка упоминания
                if bot_username and text and f"@{bot_username}" in text:
                    if "photo" in message:
                        await process_telegram_photo(
                            message, chat_id, user_id, temp_dir, download_telegram_file, send_telegram_message
                        )
                    elif "voice" in message or "audio" in message:
                        audio = message.get("voice") or message.get("audio")
                        if audio:
                            await process_telegram_voice(
                                message, chat_id, user_id, temp_dir, download_telegram_file,
                                send_telegram_message, send_telegram_audio
                            )
        
        # === ПРИВАТНЫЙ ЧАТ ===
        else:
            # В приватных чатах обрабатываем все сообщения
            # Проверяем тип контента
            if "photo" in message:
                # Обработка фото
                await process_telegram_photo(
                    message, chat_id, user_id, temp_dir, download_telegram_file, send_telegram_message
                )
                return
            
            if "voice" in message or "audio" in message:
                # Обработка голосового сообщения
                audio = message.get("voice") or message.get("audio")
                if audio:
                    await process_telegram_voice(
                        message, chat_id, user_id, temp_dir, download_telegram_file,
                        send_telegram_message, send_telegram_audio
                    )
                return
            
            # Обработка текстового сообщения
            if text:
                # Проверяем команды
                if text == "/start":
                    await show_start_menu(chat_id)
                    return

                # Команда /menu - показать главную клавиатуру
                if text == "/menu":
                    keyboard = create_main_menu_keyboard()
                    await send_telegram_message(
                        chat_id,
                        "📱 **Главное меню**\n\nВыберите режим работы:",
                        reply_markup=keyboard
                    )
                    return

                # Команда /hide - скрыть клавиатуру
                if text == "/hide":
                    keyboard = create_hide_keyboard()
                    await send_telegram_message(
                        chat_id,
                        "⬇️ Клавиатура скрыта.\n\nИспользуйте /menu чтобы вернуть.",
                        reply_markup=keyboard
                    )
                    return
                
                # Обработка нажатий на кнопки reply-клавиатуры
                if text in BOT_MODES.values():
                    mode = get_mode_from_button(text)

                    # Удаляем сообщение пользователя (нажатие кнопки)
                    if message_id:
                        await delete_telegram_message(chat_id, message_id)

                    # Обработка кнопки "Скрыть клавиатуру"
                    if mode == "hide":
                        keyboard = create_hide_keyboard()
                        await send_telegram_message(
                            chat_id,
                            "⬇️ Клавиатура скрыта.\n\nИспользуйте /menu чтобы вернуть.",
                            reply_markup=keyboard
                        )
                        return

                    # Обработка кнопки "Выбрать модель"
                    if mode == "select_model":
                        user_selecting_model[user_id] = True
                        keyboard = create_model_selection_keyboard()
                        await send_telegram_message(
                            chat_id,
                            "🤖 **Выбор модели**\n\nВыберите модель для общения:\n\n🚀 Llama 3.3 - лучшая для русского\n🦙 Llama 4 - новейшая от Meta\n🔍 Scout - легкая и быстрая\n🌙 Kimi K2 - от Moonshot AI\n☀️ Solar - быстрая и качественная\n🔱 Trinity - мультимодальная\n🤖 GLM-4.5 - полностью бесплатная",
                            reply_markup=keyboard
                        )
                        return

                    # Обработка кнопки "Политика конфиденциальности"
                    if mode == "privacy":
                        privacy_url = "https://telegra.ph/Politika-konfidencialnosti-obshchij-dokument-03-01"
                        privacy_text = f"""🔒 **Политика конфиденциальности**

Мы заботимся о вашей конфиденциальности.

📄 Полный текст политики конфиденциальности доступен по ссылке:
{privacy_url}

**Кратко:**
• Мы храним только историю диалогов для улучшения качества общения
• Ваши данные не передаются третьим лицам
• Вы можете запросить удаление ваших данных через администратора

Нажимая кнопку «🔒 Политика конфиденциальности», вы подтверждаете, что ознакомились с документом."""
                        
                        # Отправляем с кнопкой-ссылкой
                        buttons = [
                            [{"text": "📄 Открыть документ", "url": privacy_url}]
                        ]
                        await send_telegram_message_with_buttons(chat_id, privacy_text, buttons)
                        return

                    mode_manager.set_mode(user_id, mode)

                    # Для режима generation - показываем выбор модели
                    if mode == "generation":
                        db = get_database()
                        user_access_level = db.get_user_access_level(user_id)
                        keyboard = create_image_model_selection_keyboard(user_access_level)
                        await send_telegram_message(
                            chat_id,
                            f"🎨 **Генерация изображений**\n\n"
                            f"📊 Твой уровень доступа: **{user_access_level}**\n\n"
                            f"Выберите модель для генерации:",
                            reply_markup=keyboard
                        )
                        return

                    # Для режима stats сразу показываем статистику
                    if mode == "stats":
                        # Показываем статистику
                        db = get_database()
                        stats = db.get_user_stats(user_id)
                        
                        if stats:
                            level_info = {
                                "admin": "👑 Администратор (безлимит)",
                                "subscriber": "⭐ Подписчик (5 в день)",
                                "user": "👤 Пользователь (3 в день)"
                            }
                            level = stats.get('access_level', 'user')
                            first_name = stats.get('first_name', '')
                            username = stats.get('username', '')
                            
                            name_parts = []
                            if first_name:
                                name_parts.append(first_name)
                            if username:
                                name_parts.append(f"@{username}")
                            
                            name = " ".join(name_parts) if name_parts else f"User {user_id}"
                            
                            stats_text = f"""📊 **Ваша статистика**

👤 {name}
🔑 Уровень: **{level_info.get(level, 'Пользователь')}**

📈 Генерации:
• Сегодня: {stats.get('daily_count', 0)}
• Всего: {stats.get('total_count', 0)}

📅 В боте с: {stats.get('created_at', 'неизвестно')[:10]}"""
                            await send_telegram_message(chat_id, stats_text)
                        else:
                            await send_telegram_message(chat_id, "❌ Не удалось получить статистику")
                        
                        # Сбрасываем режим в auto
                        mode_manager.set_mode(user_id, "auto")
                        return
                    
                    # Отправляем подсказку
                    prompt = get_mode_prompt(mode)
                    keyboard = create_main_menu_keyboard()
                    await send_telegram_message(
                        chat_id,
                        prompt,
                        reply_markup=keyboard
                    )
                    return
                
                # Обработка кнопки "Назад к меню" - ДОЛЖНА БЫТЬ ПЕРВОЙ ПРОВЕРКОЙ
                if text == "◀️ Назад к меню":
                    user_selecting_model[user_id] = False
                    mode_manager.set_mode(user_id, "auto")
                    keyboard = create_main_menu_keyboard()
                    # Удаляем сообщение пользователя (нажатие кнопки)
                    if message_id:
                        await delete_telegram_message(chat_id, message_id)
                    await send_telegram_message(
                        chat_id,
                        "📱 **Главное меню**\n\nВыберите режим работы:",
                        reply_markup=keyboard
                    )
                    return

                # Обработка выбора модели (reply-кнопки)
                if text in ["🚀 Groq Llama 3.3", "🦙 Groq Llama 4", "🔍 Groq Scout", "🌙 Groq Kimi K2",
                           "⚡ Cerebras Llama 3.1", "🧠 Cerebras GPT-oss", "⚡ Cerebras Qwen 3", "🤖 Cerebras GLM-4.7",
                           "☀️ Solar", "🔱 Trinity", "🤖 GLM-4.5"]:

                    model_map = {
                        "🚀 Groq Llama 3.3": "groq-llama",
                        "🦙 Groq Llama 4": "groq-maverick",
                        "🔍 Groq Scout": "groq-scout",
                        "🌙 Groq Kimi K2": "groq-kimi",
                        "⚡ Cerebras Llama 3.1": "cerebras-llama",
                        "☀️ Solar": "solar",
                        "🔱 Trinity": "trinity",
                        "🤖 GLM-4.5": "glm"
                    }

                    model_key = model_map.get(text)
                    if model_key:
                        # Переключаем модель
                        user_models[user_id] = model_key

                        model_names = {
                            "groq-llama": "🚀 Llama 3.3 70B",
                            "groq-maverick": "🦙 Llama 4 Maverick",
                            "groq-scout": "🔍 Llama 4 Scout",
                            "groq-kimi": "🌙 Kimi K2",
                            "cerebras-llama": "⚡ Llama 3.1 8B (Cerebras)",
                            "solar": "☀️ Solar Pro 3",
                            "trinity": "🔱 Trinity Mini",
                            "glm": "🤖 GLM-4.5"
                        }

                        user_selecting_model[user_id] = False

                        # Сбрасываем режим в auto
                        mode_manager.set_mode(user_id, "auto")

                        # Удаляем сообщение пользователя (нажатие кнопки)
                        if message_id:
                            await delete_telegram_message(chat_id, message_id)

                        # Возвращаем главную клавиатуру
                        keyboard = create_main_menu_keyboard()
                        await send_telegram_message(
                            chat_id,
                            f"✅ Модель выбрана: **{model_names.get(model_key, model_key)}**\n\n"
                            f"Теперь я буду использовать эту модель для общения.\n\n"
                            f"Просто напишите сообщение — я отвечу! 👇",
                            reply_markup=keyboard
                        )
                        return

                    model_key = get_model_from_button(text)

                    if model_key:
                        # Переключаем модель - сохраняем КЛЮЧ, а не значение!
                        user_models[user_id] = model_key

                        model_names = {
                            "groq-llama": "🚀 Llama 3.3 70B",
                            "groq-maverick": "🦙 Llama 4 Maverick",
                            "groq-scout": "🔍 Llama 4 Scout",
                            "groq-kimi": "🌙 Kimi K2",
                            "cerebras-llama": "⚡ Llama 3.1 8B (Cerebras)",
                            "solar": "☀️ Solar Pro 3",
                            "trinity": "🔱 Trinity Mini",
                            "glm": "🤖 GLM-4.5"
                        }

                        user_selecting_model[user_id] = False

                        # Сбрасываем режим в auto после выбора модели
                        mode_manager.set_mode(user_id, "auto")

                        # Удаляем сообщение пользователя (нажатие кнопки)
                        if message_id:
                            await delete_telegram_message(chat_id, message_id)

                        # Возвращаем главную клавиатуру (не скрываем)
                        keyboard = create_main_menu_keyboard()
                        await send_telegram_message(
                            chat_id,
                            f"✅ Модель выбрана: **{model_names.get(model_key, model_key)}**\n\n"
                            f"Теперь я буду использовать эту модель для общения.\n\n"
                            f"Просто напишите сообщение — я отвечу! 👇",
                            reply_markup=keyboard
                        )
                        return

                # Если текст не распознан как кнопка модели и не "Назад" - удаляем и сбрасываем режим
                if user_selecting_model.get(user_id, False):
                    user_selecting_model[user_id] = False
                    mode_manager.set_mode(user_id, "auto")
                    # Удаляем сообщение пользователя
                    if message_id:
                        await delete_telegram_message(chat_id, message_id)
                    return

                # Команда /cancel - отмена генерации
                if text == "/cancel":
                    if user_generating_photo.get(user_id, False):
                        user_generating_photo[user_id] = False
                        await send_telegram_message(chat_id, "❌ Генерация изображения отменена.")
                    return
                
                # Команда /clear - очистка истории диалога
                if text == "/clear":
                    db = get_database()
                    db.clear_dialog_history(user_id)
                    await send_telegram_message(chat_id, "🗑️ История диалога очищена.\n\n/start - Главное меню")
                    return
                
                # Команда /model - показать текущую модель
                if text == "/model":
                    current_model = user_models.get(user_id, "groq-llama")
                    model_names = {
                        "groq-llama": "🚀 Groq Llama 3.3",
                        "groq-maverick": "🦙 Groq Llama 4",
                        "groq-scout": "🔍 Groq Scout",
                        "groq-kimi": "🌙 Groq Kimi K2",
                        "cerebras-llama": "⚡ Cerebras Llama 3.1",
                        "solar": "☀️ Solar",
                        "trinity": "🔱 Trinity",
                        "glm": "🤖 GLM-4.5"
                    }
                    await send_telegram_message(
                        chat_id,
                        f"🤖 **Ваша текущая модель:** {model_names.get(current_model, current_model)}\n\n"
                        f"Используйте /menu → Выбрать модель чтобы сменить."
                    )
                    return
                
                # Команда /generate или /рисунок
                if text.startswith("/generate ") or text.startswith("/рисунок "):
                    prompt = text.replace("/generate ", "").replace("/рисунок ", "")
                    await handle_image_generation(chat_id, user_id, prompt)
                    return
                
                # Если пользователь в режиме генерации фото - генерируем изображение
                if user_generating_photo.get(user_id, False):
                    user_generating_photo[user_id] = False  # Сбрасываем флаг
                    await handle_image_generation(chat_id, user_id, text)
                    return
                
                # Если пользователь выбрал модель генерации - генерируем изображение
                if user_image_models.get(user_id):
                    model_key = user_image_models[user_id]
                    # Сбрасываем выбор после генерации
                    del user_image_models[user_id]
                    await handle_image_generation(chat_id, user_id, text, model_key)
                    return
                
                # Команда /models - показать выбор моделей
                if text == "/models":
                    buttons = [
                        [
                            {"text": "🚀 Groq Llama 3.3", "callback_data": "model_groq-llama"},
                            {"text": "🦙 Groq Llama 4 Maverick", "callback_data": "model_groq-maverick"},
                        ],
                        [
                            {"text": "🔍 Groq Llama 4 Scout", "callback_data": "model_groq-scout"},
                            {"text": "🌙 Groq Kimi K2", "callback_data": "model_groq-kimi"},
                        ],
                        [
                            {"text": "☀️ Solar Pro 3", "callback_data": "model_solar"},
                            {"text": "🔱 Trinity Mini", "callback_data": "model_trinity"},
                        ],
                        [
                            {"text": "🤖 GLM-4.5", "callback_data": "model_glm"},
                        ]
                    ]
                    current_model = user_models.get(user_id, "llama-3.3-70b-versatile")
                    model_name = [k for k, v in AVAILABLE_MODELS.items() if v == current_model]
                    model_name = model_name[0] if model_name else "groq-llama"

                    await send_telegram_message_with_buttons(
                        chat_id,
                        f"🔧 Выбор модели\n\nТекущая модель: {model_name}\n\nВыберите модель для общения:",
                        buttons
                    )
                    return
                
                # Команда /help
                if text == "/help":
                    help_text = """📖 Помощь - LiraAI MultiAssistent

Команды:
• /start - Показать главное меню
• /models - Выбор модели для общения
• /generate [описание] - Генерировать изображение
• /рисунок [описание] - Генерировать изображение (рус)
• /clear - Очистить историю диалога
• /cancel - Отменить генерацию изображения

Возможности:
• 💬 Общение на русском языке с памятью
• 🎨 Генерация изображений
• 🎤 Распознавание голоса
• 📸 Анализ фотографий

Модели (все БЕСПЛАТНЫЕ!):
🚀 Groq (очень быстрые):
• Llama 3.3 70B - лучшая для русского
• Llama 4 Maverick - новейшая от Meta
• Llama 4 Scout - легкая и быстрая
• Kimi K2 - от Moonshot AI

☁️ OpenRouter:
• Solar Pro 3 - быстрая, качественная
• Trinity Mini - мультимодальная
• GLM-4.5 - полностью бесплатная

Бот запоминает последние 10 сообщений вашего диалога!

Просто отправьте сообщение или выберите команду в меню!"""
                    await send_telegram_message(chat_id, help_text)
                    return

                # Команда /stats - статистика пользователя
                if text == "/stats":
                    from backend.database.users_db import get_database
                    db = get_database()
                    stats = db.get_user_stats(user_id)
                    
                    if stats:
                        level_info = {
                            "admin": "👑 Администратор (безлимит)",
                            "subscriber": "⭐ Подписчик (5 в день)",
                            "user": "👤 Пользователь (3 в день)"
                        }
                        level = stats.get('access_level', 'user')
                        first_name = stats.get('first_name', '')
                        username = stats.get('username', '')
                        
                        # Формируем имя
                        name_parts = []
                        if first_name:
                            name_parts.append(first_name)
                        if username:
                            name_parts.append(f"@{username}")
                        
                        name = " ".join(name_parts) if name_parts else f"User {user_id}"
                        
                        stats_text = f"""📊 Ваша статистика

👤 {name}
🔑 Уровень: {level_info.get(level, 'Пользователь')}

📈 Генерации:
• Сегодня: {stats.get('daily_count', 0)}
• Всего: {stats.get('total_count', 0)}

📅 В боте с: {stats.get('created_at', 'неизвестно')[:10]}
"""
                        await send_telegram_message(chat_id, stats_text)
                    return

                # Команда /admin - админ панель
                if text == "/admin":
                    from backend.database.users_db import get_database
                    db = get_database()

                    is_admin_user = db.is_admin(user_id)
                    logger.info(f"🔐 Проверка админа {user_id}: {is_admin_user}")
                    
                    if not is_admin_user:
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    admin_text = """👑 Админ панель

📋 Управление пользователями:
• /admin users - Список всех пользователей
• /admin add_user [user_id] - Добавить пользователя
• /admin remove_user [user_id] - Удалить пользователя
• /admin set_level [user_id] [level] - Выдать уровень
• /admin remove_level [user_id] - Снять уровень

📢 Рассылка уведомлений:
• /admin broadcast [сообщение] - Рассылка всем пользователям
• /admin mes [сообщение] - Короткая команда для рассылки

📚 История диалогов (долговременная память):
• /admin history <user_id> [limit] - История сообщений пользователя
• /admin dialog_stats <user_id> - Статистика диалога пользователя
• /admin cleanup_dialogs [days] - Очистка истории старше N дней (по умолчанию 30)

🔧 Тех.работы:
• /admin maintenance [HH:MM] - Включить тех.работы
• /admin maintenance_off - Выключить тех.работы

📊 Статистика:
• /admin stats - Общая статистика бота
• /stats - Ваша личная статистика

🔑 Уровни доступа:
• admin - безлимитная генерация
• subscriber - 5 генераций в день
• user - 3 генерации в день

💡 Примеры:
/admin mes Друзья, Grok недоступен, пользуйтесь OpenRouter
/admin history 1658547011 50
/admin dialog_stats 1658547011
/admin cleanup_dialogs 30
/admin set_level 123456789 subscriber
/admin maintenance 17:00
"""
                    await send_telegram_message(chat_id, admin_text)
                    return

                # Админ команда: maintenance - включить тех.работы
                if text.startswith("/admin maintenance "):
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Парсим время: /admin maintenance HH:MM
                    until_time = text.replace("/admin maintenance ", "").strip()

                    # Проверяем формат времени
                    import re
                    if not re.match(r"^\d{2}:\d{2}$", until_time):
                        await send_telegram_message(chat_id, "❌ Неверный формат времени.\n\nИспользуйте формат HH:MM (например, 17:00)")
                        return

                    # Включаем тех.работы
                    db.set_maintenance_mode(True, until_time)
                    maintenance_mode["enabled"] = True
                    maintenance_mode["until_time"] = until_time

                    await send_telegram_message(
                        chat_id,
                        f"✅ **Режим тех.работ включён**\n\nДо: {until_time}\n\nВсе пользователи (кроме админов) будут получать уведомление."
                    )
                    return  # FIX: Added return to prevent duplicate response

                # Админ команда: maintenance_off - выключить тех.работы
                if text == "/admin maintenance_off":
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Выключаем тех.работы
                    db.set_maintenance_mode(False)
                    maintenance_mode["enabled"] = False
                    maintenance_mode["until_time"] = None

                    # Отправляем уведомление всем пользователям
                    user_ids = db.get_all_users_for_notification()
                    notified = 0
                    for uid in user_ids:
                        try:
                            await send_telegram_message(
                                uid,
                                "✅ **Технические работы завершены**\n\nБот снова доступен в полном режиме.\n\nСпасибо за ожидание!"
                            )
                            notified += 1
                        except Exception:
                            pass  # Игнорируем ошибки (пользователь мог заблокировать бота)

                    await send_telegram_message(
                        chat_id,
                        f"✅ **Режим тех.работ выключен**\n\nУведомлено пользователей: {notified}"
                    )
                    return

                # Админ команда: remove_level
                if text.startswith("/admin remove_level "):
                    from backend.database.users_db import get_database
                    db = get_database()
                    
                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return
                    
                    # Парсим команду: /admin remove_level user_id
                    target_user_id = text.replace("/admin remove_level ", "").strip()
                    
                    if not target_user_id or not target_user_id.isdigit():
                        await send_telegram_message(chat_id, "❌ Использование: /admin remove_level [user_id]")
                        return
                    
                    # Получаем текущий уровень
                    old_level = db.get_user_access_level(target_user_id)
                    
                    # Добавляем пользователя если не существует
                    db.add_or_update_user(target_user_id)
                    
                    if db.set_user_access_level(target_user_id, "user"):
                        await send_telegram_message(chat_id, f"✅ Уровень доступа снят\n\nПользователь: {target_user_id}\nБыло: {old_level}\nСтало: 👤 Пользователь (3 в день)")
                        
                        # Отправляем уведомление пользователю
                        try:
                            await send_telegram_message(target_user_id, f"👤 Ваш уровень доступа изменен.\n\nБыло: {old_level}\nСтало: 3 генерации в день.\n\nСпасибо за использование LiraAI MultiAssistent!")
                        except Exception as e:
                            logger.warning(f"⚠️ Не удалось отправить уведомление пользователю {target_user_id}: {e}")
                    else:
                        await send_telegram_message(chat_id, "❌ Ошибка при снятии уровня")
                    return

                # Админ команда: set_level
                if text.startswith("/admin set_level "):
                    from backend.database.users_db import get_database, ACCESS_LEVELS
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Парсим команду: /admin set_level user_id level
                    parts = text.replace("/admin set_level ", "").strip().split()
                    logger.info(f"🔧 Admin command: {text}, parts: {parts}, len: {len(parts)}")
                    
                    if len(parts) != 2:
                        await send_telegram_message(chat_id, f"❌ Использование: /admin set_level [user_id] [level]\n\nПример:\n/admin set_level 123456789 subscriber")
                        return

                    target_user_id = parts[0]
                    new_level = parts[1]

                    logger.info(f"🔧 Set level: {target_user_id} -> {new_level}")

                    if new_level not in ACCESS_LEVELS:
                        await send_telegram_message(chat_id, f"❌ Недопустимый уровень. Доступные: {', '.join(ACCESS_LEVELS.keys())}")
                        return

                    # Получаем текущий уровень
                    old_level = db.get_user_access_level(target_user_id)
                    
                    # Добавляем пользователя если не существует
                    db.add_or_update_user(target_user_id)

                    if db.set_user_access_level(target_user_id, new_level):
                        level_names = {"admin": "👑 Админ", "subscriber": "⭐ Подписчик", "user": "👤 Пользователь"}
                        await send_telegram_message(chat_id, f"✅ Уровень доступа изменен\n\nПользователь: {target_user_id}\nБыло: {level_names.get(old_level, old_level)}\nСтало: {level_names.get(new_level, new_level)}")
                        
                        # Отправляем уведомление пользователю
                        level_messages = {
                            "admin": "🎉 Поздравляем! Вам предоставлены права администратора.\n\nТеперь у вас безлимитная генерация изображений!\n\nИспользуйте /admin для управления ботом.",
                            "subscriber": "⭐ Ваш уровень доступа повышен!\n\nТеперь у вас 5 генераций изображений в день.\n\nСпасибо за использование LiraAI MultiAssistent!",
                            "user": "👤 Ваш уровень доступа изменен.\n\nТеперь у вас 3 генерации изображений в день.\n\nСпасибо за использование LiraAI MultiAssistent!"
                        }
                        try:
                            await send_telegram_message(target_user_id, level_messages.get(new_level, f"Ваш уровень доступа изменен на {new_level}"))
                        except Exception as e:
                            logger.warning(f"⚠️ Не удалось отправить уведомление пользователю {target_user_id}: {e}")
                    else:
                        await send_telegram_message(chat_id, "❌ Ошибка при установке уровня")
                    return

                # Админ команда: add_user
                if text.startswith("/admin add_user "):
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Парсим команду: /admin add_user user_id
                    target_user_id = text.replace("/admin add_user ", "").strip()
                    
                    if not target_user_id or not target_user_id.isdigit():
                        await send_telegram_message(chat_id, "❌ Использование: /admin add_user [user_id]\n\nПример:\n/admin add_user 123456789")
                        return

                    db.add_or_update_user(target_user_id)
                    await send_telegram_message(chat_id, f"✅ Пользователь {target_user_id} добавлен в базу")
                    return

                # Админ команда: remove_user (удаление пользователя)
                if text.startswith("/admin remove_user "):
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Парсим команду: /admin remove_user user_id
                    target_user_id = text.replace("/admin remove_user ", "").strip()
                    
                    if not target_user_id or not target_user_id.isdigit():
                        await send_telegram_message(chat_id, "❌ Использование: /admin remove_user [user_id]")
                        return

                    if db.remove_user(target_user_id):
                        await send_telegram_message(chat_id, f"✅ Пользователь {target_user_id} удален из базы данных")
                    else:
                        await send_telegram_message(chat_id, f"❌ Ошибка при удалении пользователя {target_user_id}")
                    return

                # Админ команда: users
                if text == "/admin users":
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        return

                    users = db.get_all_users()
                    level_icons = {"admin": "👑", "subscriber": "⭐", "user": "👤"}
                    
                    # Сортировка по уровню доступа: admin → subscriber → user
                    level_priority = {"admin": 0, "subscriber": 1, "user": 2}
                    users_sorted = sorted(users, key=lambda u: level_priority.get(u.get('access_level', 'user'), 3))

                    users_text = "👥 Все пользователи (отсортировано по уровню):\n\n"
                    for u in users_sorted[:20]:  # Показываем первые 20
                        icon = level_icons.get(u.get('access_level', 'user'), '👤')
                        first_name = u.get('first_name', '')
                        username = u.get('username', '')
                        uid = u.get('user_id', 'unknown')
                        daily = u.get('daily_count', 0)

                        # Формируем отображаемое имя с @username
                        name_parts = []
                        if first_name:
                            name_parts.append(first_name)
                        if username:
                            name_parts.append(f"@{username}")

                        name = " ".join(name_parts) if name_parts else f"User {uid}"

                        users_text += f"{icon} {name} ({uid}) - {daily} сегодня\n"

                    if len(users_sorted) > 20:
                        users_text += f"\n... и еще {len(users_sorted) - 20} пользователей"

                    await send_telegram_message(chat_id, users_text)
                    return

                # Админ команда: broadcast / mes - рассылка уведомлений всем пользователям
                if text.startswith("/admin broadcast ") or text.startswith("/admin mes "):
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Парсим команду: /admin broadcast [сообщение] или /admin mes [сообщение]
                    message = text.replace("/admin broadcast ", "").replace("/admin mes ", "").strip()

                    if not message:
                        await send_telegram_message(
                            chat_id,
                            "❌ Использование: /admin broadcast [сообщение]\n\nПример: /admin mes Друзья, Grok сейчас недоступен, пользуйтесь моделями OpenRouter"
                        )
                        return

                    # Получаем всех пользователей
                    all_users = db.get_all_users_for_notification()

                    # Логируем список пользователей для отладки
                    logger.info(f"📢 Рассылка: найдено {len(all_users)} пользователей: {all_users}")

                    # Отправляем сообщение о начале рассылки
                    await send_telegram_message(
                        chat_id,
                        f"📢 Начинаю рассылку уведомления {len(all_users)} пользователям...\n\nСообщение: {message[:100]}{'...' if len(message) > 100 else ''}"
                    )

                    # Рассылаем сообщение всем пользователям
                    success_count = 0
                    fail_count = 0
                    failed_users = []

                    for uid in all_users:
                        try:
                            # Пропускаем самого админа (он уже получил сообщение)
                            if uid == str(user_id):
                                success_count += 1
                                continue

                            await send_telegram_message(
                                uid,
                                f"📢 **Уведомление от администратора**\n\n{message}"
                            )
                            success_count += 1
                            # Небольшая задержка чтобы не заблокировали API
                            await asyncio.sleep(0.1)
                        except Exception as e:
                            logger.error(f"❌ Ошибка отправки уведомления пользователю {uid}: {e}")
                            fail_count += 1
                            failed_users.append(uid)

                    # Формируем отчет
                    report = f"✅ Рассылка завершена!\n\n📊 Результат:\n• Успешно: {success_count}\n• Ошибок: {fail_count}\n• Всего: {len(all_users)}"
                    if failed_users:
                        report += f"\n\n❌ Не удалось отправить:\n" + "\n".join(failed_users[:10])

                    await send_telegram_message(chat_id, report)
                    return

                # Админ команда: stats
                if text == "/admin stats":
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        return

                    total_users = db.get_all_users_count()
                    users = db.get_all_users()

                    admin_count = sum(1 for u in users if u.get('access_level') == 'admin')
                    subscriber_count = sum(1 for u in users if u.get('access_level') == 'subscriber')
                    user_count = sum(1 for u in users if u.get('access_level') == 'user')

                    total_gens = sum(u.get('total_count', 0) for u in users)

                    stats_text = f"""📊 Общая статистика

👥 Пользователей: {total_users}
👑 Админов: {admin_count}
⭐ Подписчиков: {subscriber_count}
👤 Пользователей: {user_count}

🎨 Всего генераций: {total_gens}
"""
                    await send_telegram_message(chat_id, stats_text)
                    return

                # Админ команда: history <user_id> - история диалога пользователя
                if text.startswith("/admin history "):
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # ����арси�������������� user_id
                    parts = text.replace("/admin history ", "").strip().split()
                    target_user_id = parts[0] if parts else None
                    limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 20

                    if not target_user_id:
                        await send_telegram_message(
                            chat_id,
                            "❌ Использование: /admin history <user_id> [limit]\n\nПример: /admin history 1658547011 50"
                        )
                        return

                    # Получаем историю
                    history = db.get_admin_dialog_history(target_user_id, limit=limit)

                    if not history:
                        await send_telegram_message(
                            chat_id,
                            f"❌ История для пользователя {target_user_id} не найдена"
                        )
                        return

                    # Формируем сообщение
                    stats = db.get_user_dialog_stats(target_user_id)
                    
                    history_text = f"""📚 История диалога пользователя {target_user_id}

📊 Статистика:
• Всего сообщений: {stats.get('total_messages', 0)}
• Сообщения пользователя: {stats.get('user_messages', 0)}
• Ответы бота: {stats.get('assistant_messages', 0)}
• 👍 Положительных: {stats.get('positive_feedback', 0)}
• 👎 Отрицательных: {stats.get('negative_feedback', 0)}
• Первое сообщение: {stats.get('first_message', 'Н/Д')[:19] if stats.get('first_message') else 'Н/Д'}
• Последнее сообщение: {stats.get('last_message', 'Н/Д')[:19] if stats.get('last_message') else 'Н/Д'}

📝 Последние {len(history)} сообщени��:
"""
                    for msg in history[-10:]:  # Показываем последние 10
                        role_icon = "👤" if msg["role"] == "user" else "🤖"
                        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                        created = msg["created_at"][:19] if msg.get("created_at") else ""
                        model = f" ({msg['model']})" if msg.get("model") else ""
                        
                        history_text += f"\n{role_icon}{model} [{created}]: {content}"

                    if len(history) > 10:
                        history_text += f"\n\n... и ещё {len(history) - 10} сообщений"

                    await send_telegram_message(chat_id, history_text)
                    return

                # Админ команда: dialog_stats <user_id> - подробная статистика диалога
                if text.startswith("/admin dialog_stats "):
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Парсим user_id
                    target_user_id = text.replace("/admin dialog_stats ", "").strip()

                    if not target_user_id:
                        await send_telegram_message(
                            chat_id,
                            "❌ Использование: /admin dialog_stats <user_id>"
                        )
                        return

                    stats = db.get_user_dialog_stats(target_user_id)

                    if not stats:
                        await send_telegram_message(
                            chat_id,
                            f"❌ Статистика для пользователя {target_user_id} не найдена"
                        )
                        return

                    stats_text = f"""📊 Статистика диалога пользователя {target_user_id}

📈 Сообщения:
• Всего: {stats.get('total_messages', 0)}
• Пользователя: {stats.get('user_messages', 0)}
• Бота: {stats.get('assistant_messages', 0)}

📅 Даты:
• Первое сообщение: {stats.get('first_message', 'Н/Д')}
• Последнее сообщение: {stats.get('last_message', 'Н/Д')}

👍 Feedback:
• Положительных: {stats.get('positive_feedback', 0)}
• Отрицательных: {stats.get('negative_feedback', 0)}
"""
                    await send_telegram_message(chat_id, stats_text)
                    return

                # Админ команда: cleanup_dialogs [days] - очистка старой истории
                if text.startswith("/admin cleanup_dialogs"):
                    from backend.database.users_db import get_database
                    db = get_database()

                    if not db.is_admin(user_id):
                        await send_telegram_message(chat_id, "❌ У вас нет прав администратора")
                        return

                    # Парсим количество дней
                    parts = text.split()
                    days = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 30

                    await send_telegram_message(
                        chat_id,
                        f"🗑️ Запускаю очистку сообщений старше {days} дней...\n\nЭто может занять некоторое время."
                    )

                    deleted_count = db.cleanup_old_dialogs(days)

                    await send_telegram_message(
                        chat_id,
                        f"✅ Очистка завершена!\n\nУдалено сообщений: {deleted_count}"
                    )
                    return

                # Обычный ответ через LLM
                await handle_text_message(chat_id, user_id, text, is_group=False)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")




async def handle_feedback_bot_message(chat_id: str, user_id: str, text: str, is_group: bool = False, user_name: Optional[str] = None):
    """О������рабатывает сообщение через FeedbackBotHandler"""
    try:
        if not text or not text.strip():
            logger.debug(f"[FeedbackBot] Пустое сообщение от {user_id}, пропускаю")
            return
        
        # Формир��ем имя пользователя для отображения
        display_name = user_name if user_name else f"Пользователь {user_id}"
        logger.info(f"[FeedbackBot] 📨 Получено текстовое сообщение от {display_name} ({user_id}) в группе {chat_id}: {len(text)} символов")
        
        if feedback_bot_handler is None:
            logger.warning("[FeedbackBot] ❌ FeedbackBotHandler не инициализирован")
            return
        
        # Получаем или создаем историю диалога для этой группы
        if chat_id not in feedback_chat_history:
            feedback_chat_history[chat_id] = []
            logger.info(f"[FeedbackBot] Создана новая история для группы {chat_id}")
        
        logger.debug(f"[FeedbackBot] История диалога: {len(feedback_chat_history[chat_id])} сообщений")
        
        # Формируем историю в формате для LLM (с именами пользователей)
        chat_history = []
        for msg in feedback_chat_history[chat_id]:
            chat_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        logger.debug(f"[FeedbackBot] Передаю в LLM историю: {len(chat_history)} сообщений")
        
        # Формируем сообщение с именем пользователя для LLM
        user_message_with_name = f"{display_name}: {text}" if user_name else text
        
        # Запускаем постоянное обновление статуса "печатает"
        typing_task = asyncio.create_task(_keep_typing_status(chat_id))
        logger.info(f"[FeedbackBot] ⌨️ Запущено постоянное обновление статуса 'печатает' для чата {chat_id}")
        
        try:
            # Обрабатываем запрос
            logger.info(f"[FeedbackBot] 🤖 Отправляю запрос в FeedbackBotHandler...")
            response = await feedback_bot_handler.process_feedback_query(
                user_message=user_message_with_name,
                chat_history=chat_history if chat_history else None
            )
            logger.info(f"[FeedbackBot] ✅ Получен ответ от FeedbackBot: {len(response)} символов")
        finally:
            # Останавливаем обновление статуса как только ответ готов
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
            logger.info(f"[FeedbackBot] ⏹️ Остановлено обновление статуса 'печатает' для чата {chat_id}")
        
        # Сохраняем сообщение пользователя в историю (с именем)
        feedback_chat_history[chat_id].append({
            "role": "user",
            "content": f"{display_name}: {text}" if user_name else text
        })
        
        # Сохраняем ответ бота в историю
        feedback_chat_history[chat_id].append({
            "role": "assistant",
            "content": response
        })
        
        logger.info(f"[FeedbackBot] 💾 Сохранено в историю: {len(feedback_chat_history[chat_id])} сообщений")
        
        # Ограничиваем размер истории (последние 20 сообщений)
        if len(feedback_chat_history[chat_id]) > 20:
            old_len = len(feedback_chat_history[chat_id])
            feedback_chat_history[chat_id] = feedback_chat_history[chat_id][-20:]
            logger.info(f"[FeedbackBot] ✂️ История обрезана: {old_len} -> {len(feedback_chat_history[chat_id])} сообщений")
        
        # Отправляем ответ
        logger.info(f"[FeedbackBot] 📤 Отправляю ответ в группу {chat_id}...")
        await send_telegram_message(chat_id, response)
        logger.info(f"[FeedbackBot] ✅ Обработка сообщения завершена успешно")
        
    except Exception as e:
        logger.error(f"[FeedbackBot] ❌ Ошибка при обработке сообщения: {e}", exc_info=True)
        await send_telegram_message(chat_id, "Извините, произошла ошибка при обработке вашего сообщения.")


async def _keep_typing_status(chat_id: str):
    """Периодически обновляет статус 'печатает' каждые 4 секунды"""
    try:
        while True:
            await send_chat_action(chat_id, "typing")
            logger.debug(f"[FeedbackBot] ⌨️ Обновлен статус 'печатает' в чат {chat_id}")
            await asyncio.sleep(4)  # Обновляем каждые 4 секунды
            
    except asyncio.CancelledError:
        logger.debug(f"[FeedbackBot] ⏹️ Остановлено обновление статуса 'печатает' для чата {chat_id}")
        raise
    except Exception as e:
        logger.error(f"[FeedbackBot] ❌ Ошибка обновления статуса 'печатает': {e}")


async def handle_feedback_bot_photo(chat_id: str, user_id: str, message: Dict[str, Any]):
    """Обрабатывает фото в FeedbackBot группе - анализирует и передает в FeedbackBot"""
    try:
        if feedback_bot_handler is None:
            logger.warning("FeedbackBotHandler не инициализирован")
            return
        
        # Получаем список фотографий (разные размеры)
        photos = message.get("photo", [])
        if not photos:
            logger.warning(f"Сообщение не содержит фотографий: {message}")
            return
        
        # Берем самую большую фотографию (последнюю в списке)
        photo = photos[-1]
        file_id = photo.get("file_id")
        
        if not file_id:
            logger.warning(f"Не удалось получить file_id фотографии: {photo}")
            return
        
        # Извлекаем имя пользователя
        user = message.get("from", {})
        user_name = None
        if user:
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            username = user.get("username", "")
            if first_name or last_name:
                user_name = f"{first_name} {last_name}".strip()
            elif username:
                user_name = f"@{username}"
        
        display_name = user_name if user_name else f"Пользователь {user_id}"
        logger.info(f"[FeedbackBot] 📸 Получено фото от {display_name} ({user_id}) в группе {chat_id}, file_id: {file_id}")
        
        # Отправляем сообщение о начале ������бработки
        logger.info(f"[FeedbackBot] Отправляю уведомление о начале анализа изображения")
        await send_telegram_message(chat_id, "🔍 Анализирую изображение...")
        
        # Скачиваем фото
        logger.info(f"[FeedbackBot] Скачиваю фото {file_id}...")
        local_path = temp_dir / f"feedback_photo_{os.getpid()}.jpg"
        downloaded_path = await download_telegram_file(file_id, local_path)
        
        if not downloaded_path:
            logger.error(f"[FeedbackBot] ❌ Не удалось скачать фото: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось скачать фот�� для анализа.")
            return
        
        logger.info(f"[FeedbackBot] ✅ Фото скачано: {downloaded_path}")
        
        # Ана��изируем изображение через мультимодальную модель
        logger.info(f"[FeedbackBot] 🔍 Начинаю анализ изображения через мультимодальную модель...")
        from backend.vision.image_analyzer import ImageAnalyzer
        analyzer = ImageAnalyzer(config)
        
        # Промпт для анализа изображения (из IKAR-ASSISTANT)
        prompt = "Что на этом изображении? Опиши подробно, но кратко. Используй русский язык."
        logger.debug(f"[FeedbackBot] Промпт для анализа: {prompt}")
        
        description = await analyzer.analyze_image(downloaded_path, prompt)
        logger.info(f"[FeedbackBot] ✅ Изображение проанализиров��но: {len(description)} символов описания")
        
        # Удаляем временный файл
        try:
            os.remove(downloaded_path)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
        
        if not description:
            logger.error(f"Не удалось проанализировать изображение: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось проанализировать изображение.")
            return
        
        # Извлекаем имя пользователя
        user = message.get("from", {})
        user_name = None
        if user:
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            username = user.get("username", "")
            if first_name or last_name:
                user_name = f"{first_name} {last_name}".strip()
            elif username:
                user_name = f"@{username}"
        
        display_name = user_name if user_name else f"Пользователь {user_id}"
        
        # Формируем сообщение для FeedbackBot с описанием изображения
        # Просто передаем описание, без лишних инструкций - бот сам определит что делать
        user_message = f"{display_name} отправил изображение. Описание: {description}" if user_name else f"Пользователь отправил изображение. Описание: {description}"
        logger.info(f"[FeedbackBot] 📝 Формирую запрос для FeedbackBot: {len(user_message)} символов")
        
        # Получаем или создаем историю диалога для этой группы
        if chat_id not in feedback_chat_history:
            feedback_chat_history[chat_id] = []
            logger.info(f"[FeedbackBot] Создана новая история для группы {chat_id}")
        
        logger.info(f"[FeedbackBot] История диалога: {len(feedback_chat_history[chat_id])} сообщений")
        
        # Формируем историю в формате для LLM
        chat_history = []
        for msg in feedback_chat_history[chat_id]:
            chat_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        logger.debug(f"[FeedbackBot] Передаю в LLM историю: {len(chat_history)} сообщений")
        
        # Запускаем постоянное обновление статуса "печатает"
        typing_task = asyncio.create_task(_keep_typing_status(chat_id))
        logger.info(f"[FeedbackBot] ⌨️ Запущено постоянное обновление статуса 'печатает' для чата {chat_id}")
        
        try:
            # Обрабатываем запрос через FeedbackBot
            logger.info(f"[FeedbackBot] 🤖 Отправляю запрос в FeedbackBotHandler...")
            response = await feedback_bot_handler.process_feedback_query(
                user_message=user_message,
                chat_history=chat_history if chat_history else None
            )
            logger.info(f"[FeedbackBot] ✅ Получен ответ от FeedbackBot: {len(response)} символов")
        finally:
            # Останавливаем обновление статуса как только ответ готов
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
            logger.info(f"[FeedbackBot] ⏹️ Остановлено обновление статуса 'печатает' для чата {chat_id}")
        
        # Сохраняем в историю (с именем)
        feedback_chat_history[chat_id].append({
            "role": "user",
            "content": f"{display_name} [Изображение]: {description}" if user_name else f"[Изображение] {description}"
        })
        
        feedback_chat_history[chat_id].append({
            "role": "assistant",
            "content": response
        })
        
        logger.info(f"[FeedbackBot] 💾 Сохранено в историю: {len(feedback_chat_history[chat_id])} сообщений")
        
        # Ограничиваем размер истории
        if len(feedback_chat_history[chat_id]) > 20:
            old_len = len(feedback_chat_history[chat_id])
            feedback_chat_history[chat_id] = feedback_chat_history[chat_id][-20:]
            logger.info(f"[FeedbackBot] ✂️ История обрезана: {old_len} -> {len(feedback_chat_history[chat_id])} сообщений")
        
        # Отправляем ответ
        logger.info(f"[FeedbackBot] 📤 Отправляю ответ в группу {chat_id}...")
        await send_telegram_message(chat_id, response)
        logger.info(f"[FeedbackBot] ✅ Обработка фото завершена успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке фото FeedbackBot: {e}")
        await send_telegram_message(chat_id, "Извините, произошла ошибка при обработке изображения.")


async def handle_feedback_bot_voice(chat_id: str, user_id: str, message: Dict[str, Any]):
    """Обрабатывает голосовое сообщение в FeedbackBot группе - распознает и передает в FeedbackBot"""
    try:
        if feedback_bot_handler is None:
            logger.warning("FeedbackBotHandler не инициализирован")
            return
        
        # Получаем голосовое сообщение или аудио
        voice = message.get("voice") or message.get("audio")
        if not voice:
            logger.warning(f"Сообщение не содержит голосового сообщения: {message}")
            return
        
        file_id = voice.get("file_id")
        if not file_id:
            logger.warning(f"Не удалось получить file_id голосового сообщения: {voice}")
            return
        
        logger.info(f"[FeedbackBot] 🎤 Получено голосовое сообщение от {user_id} в группе {chat_id}, file_id: {file_id}")
        
        # Отправляем сообщение о начале обработки
        await send_telegram_message(chat_id, "🎤 Распознаю речь...")
        
        # Скачиваем аудиофайл
        temp_dir = Path(__file__).parent.parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        local_path = temp_dir / f"feedback_voice_{os.getpid()}.ogg"
        downloaded_path = await download_telegram_file(file_id, local_path)
        
        if not downloaded_path:
            logger.error(f"[FeedbackBot] ❌ Не удалось скачать голосовое сообщение: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось скачать голосовое сообщение.")
            return
        
        logger.info(f"[FeedbackBot] ✅ Голосовое сообщение скачано: {downloaded_path}")
        
        # Распознаем речь через STT
        logger.info(f"[FeedbackBot] 🎙️ Начинаю распознавание речи...")
        from backend.voice.stt import SpeechToText
        stt = SpeechToText()
        recognized_text = stt.speech_to_text(downloaded_path, language="ru")
        
        # Удаляем временный файл
        try:
            os.remove(downloaded_path)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
        
        if not recognized_text or not recognized_text.strip():
            logger.error(f"[FeedbackBot] ❌ Не удалось распознать речь: {file_id}")
            await send_telegram_message(chat_id, "❌ Не удалось распознать речь.")
            return
        
        logger.info(f"[FeedbackBot] ✅ Речь распознана: {len(recognized_text)} символов")
        
        # Получаем или создаем историю диалога для этой группы
        if chat_id not in feedback_chat_history:
            feedback_chat_history[chat_id] = []
            logger.info(f"[FeedbackBot] Создана новая история для группы {chat_id}")
        
        logger.info(f"[FeedbackBot] История диалога: {len(feedback_chat_history[chat_id])} сообщений")
        
        # Формируем и��торию в формате для LLM
        chat_history = []
        for msg in feedback_chat_history[chat_id]:
            chat_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        logger.debug(f"[FeedbackBot] Передаю в LLM историю: {len(chat_history)} сообщений")
        
        # Извлекаем имя пользователя
        user = message.get("from", {})
        user_name = None
        if user:
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            username = user.get("username", "")
            if first_name or last_name:
                user_name = f"{first_name} {last_name}".strip()
            elif username:
                user_name = f"@{username}"
        display_name = user_name if user_name else f"Пользователь {user_id}"

        # Формируем сообщение с именем пользователя для LLM
        user_message_with_name = f"{display_name} [Голосовое]: {recognized_text}" if user_name else f"[Голосовое] {recognized_text}"
        
        # Запускаем постоянное обновление статуса "печатает"
        typing_task = asyncio.create_task(_keep_typing_status(chat_id))
        logger.info(f"[FeedbackBot] ⌨️ Запущено постоянное обновление статуса 'печатает' для чата {chat_id}")
        
        try:
            # Обрабатываем запрос через FeedbackBot
            logger.info(f"[FeedbackBot] 🤖 Отправляю распознанный текст в FeedbackBotHandler...")
            response = await feedback_bot_handler.process_feedback_query(
                user_message=user_message_with_name,
                chat_history=chat_history if chat_history else None
            )
            logger.info(f"[FeedbackBot] ✅ Получен ответ от FeedbackBot: {len(response)} символо��")
        finally:
            # Останавливаем обновление статуса как только ответ готов
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
            logger.info(f"[FeedbackBot] ⏹️ Остановлено обновление статуса 'печатает' для чата {chat_id}")
        
        # Сохраняем в историю (с именем)
        feedback_chat_history[chat_id].append({
            "role": "user",
            "content": f"{display_name} [Голосовое]: {recognized_text}" if user_name else f"[Голосовое] {recognized_text}"
        })
        
        feedback_chat_history[chat_id].append({
            "role": "assistant",
            "content": response
        })
        
        logger.info(f"[FeedbackBot] 💾 Сохранено в историю: {len(feedback_chat_history[chat_id])} сообщений")
        
        # Ограничиваем размер истории
        if len(feedback_chat_history[chat_id]) > 20:
            old_len = len(feedback_chat_history[chat_id])
            feedback_chat_history[chat_id] = feedback_chat_history[chat_id][-20:]
            logger.info(f"[FeedbackBot] ✂️ История обрезана: {old_len} -> {len(feedback_chat_history[chat_id])} сообщений")
        
        # Отправляем ответ
        logger.info(f"[FeedbackBot] 📤 Отправляю ответ в группу {chat_id}...")
        await send_telegram_message(chat_id, response)
        logger.info(f"[FeedbackBot] ✅ Обработка голосового сообщения завершена успешно")
        
    except Exception as e:
        logger.error(f"[FeedbackBot] ❌ Ошибка при обработке голосового сообщения: {e}", exc_info=True)
        await send_telegram_message(chat_id, "Извините, произошла ошибка при обработке голосового сообщения.")


async def handle_text_message(chat_id: str, user_id: str, text: str, is_group: bool = False):
    """Обрабатывает текстовое сообщение через LLM с учётом режима пользователя"""
    try:
        if not text or not text.strip():
            return

        # Добавляем пользователя в базу
        from backend.database.users_db import get_database
        db = get_database()
        db.add_or_update_user(user_id)

        # Получаем режим пользователя
        mode = mode_manager.get_mode(user_id)
        logger.info(f"📊 Пользователь {user_id} в режиме: {mode}")

        # Обработка в зависимости от режима
        if mode == "privacy":
            # Политика конфиденциальности
            privacy_url = "https://telegra.ph/Politika-konfidencialnosti-obshchij-dokument-03-01"
            privacy_text = f"""🔒 **Политика конфиденциальности**

Мы заботимся о вашей конфиденциальности.

📄 Полный текст политики конфиденциальности доступен по ссылке:
{privacy_url}

**Кратко:**
• Мы храним только историю диалогов для улучшения качества общения
• Ваши данные не передаются третьим лицам
• Вы можете запросить удаление ваших данных через администратора

Нажимая кнопку «🔒 Политика конфиденциальности», вы подтверждаете, что ознакомились с документом."""

            # Отправляем с кнопкой-ссылкой
            buttons = [
                [{"text": "📄 Открыть документ", "url": privacy_url}]
            ]
            await send_telegram_message_with_buttons(chat_id, privacy_text, buttons)
            return

        if mode == "help":
            # В режиме помощи показываем справку
            help_text = """ℹ️ **Помощь - LiraAI MultiAssistant**

**Команды:**
• /start - Главное меню
• /menu - Показать клавиатуру
• /hide - Скрыть клавиатуру
• /models - Выбор модели
• /generate [описание] - Генерация изображения
• /stats - Ваша статистистика

**Возможности:**
• 💬 Общение на русском языке
• 🎨 Генерация изображений
• 🎤 Распознавание голоса
• 📸 Анализ фотографий

**Режимы:**
• 💬 Текст - обычное общение
• 🎤 Голос - распознавание речи
• 📸 Фото - анализ изображений
• 🎨 Генерация - создание изображений

Бот запоминает последние 10 сообщений вашего диалога!"""
            await send_telegram_message(chat_id, help_text)
            return

        elif mode == "stats":
            # В режиме статистики показываем статистику
            from backend.database.users_db import get_database
            db = get_database()
            
            # Принудительно обновляем данные пользователя из БД
            stats = db.get_user_stats(user_id)
            
            if stats:
                level_info = {
                    "admin": "👑 Администратор (безлимит)",
                    "subscriber": "⭐ Подписчик (5 в день)",
                    "user": "👤 Пользователь (3 в день)"
                }
                level = stats.get('access_level', 'user')
                first_name = stats.get('first_name', '')
                username = stats.get('username', '')
                
                name_parts = []
                if first_name:
                    name_parts.append(first_name)
                if username:
                    name_parts.append(f"@{username}")
                
                name = " ".join(name_parts) if name_parts else f"User {user_id}"
                
                stats_text = f"""📊 **Ваша статистика**

👤 {name}
🔑 Уровень: **{level_info.get(level, 'Пользователь')}**

📈 Генерации:
• Сегодня: {stats.get('daily_count', 0)}
• Всего: {stats.get('total_count', 0)}

📅 В боте с: {stats.get('created_at', 'неизвестно')[:10]}"""
                await send_telegram_message(chat_id, stats_text)
            else:
                await send_telegram_message(chat_id, "❌ Не удалось получить статистику")
            # После показа статистики сбрасываем режим в auto
            mode_manager.set_mode(user_id, "auto")
            return

        elif mode == "generation":
            # В режиме генерации - если есть текст, генерируем изображение
            if text:
                # Загружаем модель из БД
                db = get_database()
                model_key = db.get_user_image_model(user_id)
                if model_key:
                    logger.info(f"💾 Загружена image_model из БД для {user_id}: {model_key}")
                await handle_image_generation(chat_id, user_id, text, model_key)
                return
            else:
                # Если нет текста - показываем выбор модели
                db = get_database()
                user_access_level = db.get_user_access_level(user_id)
                keyboard = create_image_model_selection_keyboard(user_access_level)
                await send_telegram_message(
                    chat_id,
                    f"🎨 **Генерация изображений**\n\n📊 Твой уровень доступа: **{user_access_level}**\n\nВыберите модель для генерации:",
                    reply_markup=keyboard
                )
                return
        # Получаем модель пользователя
        model_key = user_models.get(user_id, "groq-llama")
        model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
        client_type, model = model_info
        
        logger.info(f"🎯 {user_id} использует модель: {model_key} ({client_type} - {model})")

        # Системный промпт для русского языка с памятью
        system_prompt = """Ты - LiraAI, умный и дружелюбный AI-ассистент женского пола.
Ты общаешься на русском языке, кратко и по делу, но с теплотой и заботой.
Ты используешь женский род в своих ответах (например: "я помогла", "я сделала", "я думаю").

У тебя есть один разработчик - Danil Alekseevich. 
Познакомиться с ним можно через канал разработки @liranexus (кнопка "📢 Подписаться" в меню).

Запоминай информацию о пользователе и контекст разговора.
Если пользователь представился - запомни его имя и используй в дальнейшем общении.
Будь полезной, доброй и поддерживающей!"""

        # Получаем историю диалога пользователя из БАЗЫ ДАННЫХ (долговременная память)
        db = get_database()
        history = db.get_dialog_history(user_id, limit=20)  # Последние 20 сообщений
        
        # Конвертируем в формат для LLM
        chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]

        logger.info(f"📚 История из БД: {len(chat_history)} сообщений, модель: {model}, клиент: {client_type}")

        # Graceful degradation: пробуем модель, при ошибке предлагаем альтернативу
        response = None
        # Fallback последовательность: оригинал → Groq → Cerebras → Solar
        fallback_sequence = [(client_type, model, model_key)]
        if client_type == "cerebras":
            fallback_sequence.extend([
                ("groq", "llama-3.3-70b-versatile", "groq-llama"),
                ("openrouter", "upstage/solar-pro-3:free", "solar"),
            ])
        elif client_type == "groq":
            fallback_sequence.extend([
                ("cerebras", "llama3.1-8b", "cerebras-llama"),
                ("openrouter", "upstage/solar-pro-3:free", "solar"),
            ])
        else:  # openrouter
            fallback_sequence.extend([
                ("groq", "llama-3.3-70b-versatile", "groq-llama"),
                ("cerebras", "llama3.1-8b", "cerebras-llama"),
            ])

        response = None
        for attempt, (c_type, mdl, m_key) in enumerate(fallback_sequence):
            try:
                # Выбираем клиент
                if c_type == "groq":
                    client = groq_client
                elif c_type == "cerebras":
                    client = cerebras_client
                else:
                    client = llm_client

                logger.info(f"🚀 Попытка {attempt + 1}: {c_type} - {mdl}")

                response = await client.chat_completion(
                    user_message=text,
                    system_prompt=system_prompt,
                    chat_history=chat_history,
                    model=mdl,
                    temperature=0.7
                )

                # Успех!
                if attempt > 0:
                    # Fallback сработал - уведомляем
                    model_names_display = {
                        "groq-llama": "🚀 Groq Llama 3.3",
                        "cerebras-llama": "⚡ Cerebras Llama 3.1",
                        "solar": "☀️ Solar Pro 3",
                    }
                    fallback_name = model_names_display.get(m_key, m_key)
                    await send_telegram_message(
                        chat_id,
                        f"⚠️ **Оригинальная модель временно недоступна**\n\n"
                        f"✅ Переключаюсь на **{fallback_name}**\n\n"
                        f"Продолжаю общение..."
                    )

                # Сохраняем в историю
                db.save_dialog_message(user_id, "user", text, model=m_key)
                db.save_dialog_message(user_id, "assistant", response, model=m_key)
                break

            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Ошибка {c_type} ({mdl}): {error_msg}")
                logger.error(f"   Полный текст ошибки: {error_msg[:500]}")

                if attempt == len(fallback_sequence) - 1:
                    # Все попытки исчерпаны
                    await send_telegram_message(
                        chat_id,
                        f"❌ **Временная ошибка**\n\n"
                        f"Не удалось получить ответ от нейросети.\n\n"
                        f"Попробуйте:\n"
                        f"1. Переключить модель (/menu → Выбрать модель)\n"
                        f"2. Повторить запрос позже"
                    )
                    return

        if not response:
            await send_telegram_message(chat_id, "❌ Не удалось получить ответ. Попробуйте другую модель.")
            return

        await send_telegram_message(chat_id, response)

    except Exception as e:
        logger.error(f"Ошибка при обработке текстового сообщения: {e}", exc_info=True)
        await send_telegram_message(chat_id, f"❌ Ошибка: {str(e)}")


async def handle_image_generation(chat_id: str, user_id: str, prompt: str, model_key: str = None):
    """Обрабатывает запрос на генерацию изображения через Gemini/HF+Replicate с проверкой лимитов и уровней доступа"""
    from backend.database.users_db import get_database
    import os

    try:
        logger.info(f"🎨 Генерация изображения для пользователя {user_id}: {prompt}")

        # Проверяем лимиты и уровень доступа
        db = get_database()
        db.add_or_update_user(user_id)

        # Получаем уровень доступа
        access_level = db.get_user_access_level(user_id)

        # Проверяем лимиты
        limit_info = db.check_generation_limit(user_id)

        if not limit_info["allowed"]:
            await send_telegram_message(
                chat_id,
                f"❌ Превышен дневной лимит генерации изображений.\n\n"
                f"Использовано: {limit_info['daily_count']}/{limit_info['daily_limit']}\n"
                f"Всего: {limit_info['total_count']}\n\n"
                f"Лимит сбросится: {limit_info['reset_time']}"
            )
            return

        # Получаем модель пользователя (или используем переданную)
        if not model_key:
            # Загружаем из БД
            db = get_database()
            model_key = db.get_user_image_model(user_id)
            if model_key:
                logger.info(f"💾 Загружена image_model из БД для {user_id}: {model_key}")

        # Определяем тип модели (Gemini или HF+Replicate)
        is_hf_model = model_key and model_key.startswith("hf-")
        
        # Проверяем доступность модели для уровня доступа
        if is_hf_model:
            available_models = hf_replicate_client.get_models_for_user(access_level)
        else:
            available_models = gemini_image_client.get_models_for_user(access_level)

        if not model_key or model_key not in available_models:
            # Пробуем получить модель из HF+Replicate сначала, потом Gemini
            if hf_replicate_client.api_key:
                hf_models = hf_replicate_client.get_models_for_user(access_level)
                if hf_models:
                    model_key = list(hf_models.keys())[0]
                    is_hf_model = True
                    available_models = hf_models
            else:
                gemini_models = gemini_image_client.get_models_for_user(access_level)
                if gemini_models:
                    model_key = list(gemini_models.keys())[0]
                    is_hf_model = False
                    available_models = gemini_models
                else:
                    model_key = "hf-flux-dev"  # Default fallback
                    is_hf_model = True
                    available_models = hf_replicate_client.get_models_for_user(access_level)

        model_info = available_models.get(model_key, {})
        model_name = model_info.get("description", model_key)

        # Информируем о лимитах
        if limit_info['daily_limit'] == -1:
            limit_text = "📊 Доступно генераций: **Безлимит** (администратор)"
        else:
            available_count = limit_info['daily_limit'] - limit_info['daily_count']
            limit_text = f"📊 Доступно генераций: {available_count}/{limit_info['daily_limit']}"

        await send_telegram_message(
            chat_id,
            f"🎨 Генерирую изображение...\n\n"
            f"📊 Модель: **{model_name}**\n"
            f"{limit_text}\n"
            f"Всего использовано: {limit_info['total_count']}\n\n"
            f"Подождите немного, это займет 10-30 секунд."
        )
        
        logger.info(f"🔍 Отладка 2: после send_telegram_message")

        # Используем оригинальный промпт (HF API понимает русский)
        enhanced_prompt = f"{prompt}, high quality, detailed, artistic, 8k, masterpiece"
        
        logger.info(f"🔍 Отладка 3: промпт={enhanced_prompt[:80]}")

        # Генерация через HF
        image_data = None
        
        # Логирование для отладки
        logger.info(f"🔍 Отладка: model_key={model_key}, is_hf_model={is_hf_model}, hf_api_key={'✅' if hf_replicate_client.api_key else '❌'}")

        if is_hf_model and hf_replicate_client.api_key:
            # Генерация через HF (Stable Diffusion 3)
            try:
                image_data = await hf_replicate_client.generate_image(
                    prompt=enhanced_prompt,
                    model_key=model_key,
                    timeout=90
                )

                if image_data and len(image_data) > 10000:
                    logger.info(f"✅ HF успешно: {len(image_data)} байт")
            except Exception as e:
                logger.error(f"❌ Ошибка HF: {e}", exc_info=True)

        # Gemini - в разработке
        # if not image_data and gemini_image_client.api_key:
        #     try:
        #         image_data = await gemini_image_client.generate_image(
        #             prompt=enhanced_prompt,
        #             model_key=model_key if not is_hf_model else "gemini-flash",
        #             timeout=90
        #         )
        #         if image_data and len(image_data) > 10000:
        #             logger.info(f"✅ Gemini Image успешно: {len(image_data)} байт")
        #     except Exception as e:
        #         logger.error(f"❌ Ошибка Gemini Image: {e}", exc_info=True)

        # Если изображение получено - отправляем пользователю
        if image_data and len(image_data) > 10000:
            image_path = temp_dir / f"generated_{os.getpid()}.png"
            with open(image_path, "wb") as f:
                f.write(image_data)

            provider_name = "FLUX" if is_hf_model else "Gemini"
            await send_telegram_photo(
                chat_id,
                str(image_path),
                caption=f"🎨 {prompt}\n\n📊 Модель: {model_name}\n👤 Уровень: {access_level}\n🤖 {provider_name}"
            )

            db.increment_generation_count(user_id, prompt)

            try:
                os.remove(image_path)
            except:
                pass
            return

        # Если всё не сработало
        await send_telegram_message(
            chat_id,
            "❌ Не удалось сгенерировать изображение.\n\n"
            "Возможные причины:\n"
            "• HF+Replicate: проверьте токен Hugging Face\n"
            "• Gemini: недоступен в вашем регионе\n\n"
            "Попробуйте:\n"
            "1. Другую модель (/start → Генерация → Выбор модели)\n"
            "2. Позже"
        )

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации: {e}", exc_info=True)
        await send_telegram_message(chat_id, f"❌ Ошибка генерации: {str(e)[:200]}")


async def start_polling_for_bot(token: str, bot_name: str = "Bot"):
    """Запускает polling для одного бота"""
    global last_update_id
    last_update_id = 0

    logger.info(f"📱 Запуск Telegram polling для {bot_name}...")
    
    while True:
        try:
            updates = await get_updates(token, offset=last_update_id + 1)

            if updates:
                logger.debug(f"[{bot_name}] Получено {len(updates)} обновлений")

            for update in updates:
                update_id = update.get("update_id")
                
                # СРАЗУ обновляем last_update_id ПЕРЕД обработкой, чтобы избежать дублирования
                last_update_id = max(last_update_id, update_id)

                # Обрабатываем сообщения
                if "message" in update:
                    message = update["message"]
                    chat_id = str(message.get("chat", {}).get("id"))
                    chat_type = message.get("chat", {}).get("type", "unknown")
                    from_user_id = message.get("from", {}).get("id")
                    text = message.get("text", "")

                    logger.info(f"[{bot_name}] 📨 Получено сообщение в {chat_type} {chat_id} от {from_user_id}: {text[:50]}")

                    # Сохраняем связь chat_id -> token
                    from backend.api.telegram_core import set_token_for_chat
                    set_token_for_chat(chat_id, token)
                    await process_message(message, token)

                # Обрабатываем callback_query (для кнопок)
                if "callback_query" in update:
                    callback_query = update["callback_query"]
                    callback_data = callback_query.get("data", "")
                    callback_chat_id = str(callback_query["message"]["chat"]["id"])
                    callback_message_id = callback_query["message"]["message_id"]
                    callback_user_id = str(callback_query.get("from", {}).get("id", ""))

                    logger.info(f"[CALLBACK] Получен callback: {callback_data} в чате {callback_chat_id}")

                    # Получаем базу данных для проверки тех.работ
                    from backend.database.users_db import get_database
                    db = get_database()
                    
                    # Проверяем режим тех.работ для callback кнопок
                    maint_status = db.get_maintenance_mode()
                    if maint_status["enabled"]:
                        is_admin = db.is_admin(callback_user_id)
                        if not is_admin:
                            # Блокируем все callback кнопки кроме stats и help
                            if callback_data not in ["stats", "help"]:
                                from backend.api.telegram_core import answer_callback_query
                                await answer_callback_query(
                                    callback_query["id"],
                                    "🔧 Технические работы. Бот временно недоступен."
                                )
                                continue
                    
                    # Обработка кнопок выбора модели
                    if callback_data.startswith("model_"):
                        from backend.api.telegram_core import answer_callback_query, edit_message_text

                        model_key = callback_data.replace("model_", "")
                        if model_key in AVAILABLE_MODELS:
                            # Переключаем модель (в памяти)
                            user_models[callback_user_id] = model_key

                            # Отвечаем на callback
                            await answer_callback_query(
                                callback_query["id"],
                                f"✅ Модель переключена на {model_key}!"
                            )

                            # Редактируем сообщение
                            model_names = {
                                "groq-llama": "🚀 Llama 3.3 70B - лучшая для русского",
                                "groq-maverick": "🦙 Llama 4 Maverick - новейшая от Meta",
                                "groq-scout": "🔍 Llama 4 Scout - легкая и быстрая",
                                "groq-kimi": "🌙 Kimi K2 - от Moonshot AI",
                                "cerebras-llama": "⚡ Llama 3.1 8B - сверхбыстрая (Cerebras)",
                                "solar": "☀️ Solar Pro 3 - быстрая и качественная",
                                "trinity": "🔱 Trinity Mini - мультимодальная",
                                "glm": "🤖 GLM-4.5 - полностью бесплатная"
                            }

                            await edit_message_text(
                                callback_chat_id,
                                callback_message_id,
                                f"✅ Модель выбрана: {model_names.get(model_key, model_key)}\n\nТеперь я буду использовать эту модель для общения."
                            )
                        continue

                    # Обработка выбора модели генерации изображений (img_*)
                    elif callback_data.startswith("img_"):
                        from backend.api.telegram_core import answer_callback_query, edit_message_text, send_telegram_message

                        model_key = callback_data.replace("img_", "")

                        # Получаем уровень доступа пользователя
                        db = get_database()
                        user_access_level = db.get_user_access_level(callback_user_id)

                        # Определяем тип модели (Gemini или HF+Replicate)
                        is_hf_model = model_key.startswith("hf-")
                        
                        # Проверяем доступность модели для уровня доступа
                        if is_hf_model:
                            available_models = hf_replicate_client.get_models_for_user(user_access_level)
                        else:
                            available_models = gemini_image_client.get_models_for_user(user_access_level)

                        if model_key not in available_models:
                            await answer_callback_query(
                                callback_query["id"],
                                "❌ Эта модель недоступна для вашего уровня доступа!"
                            )
                            return

                        # Сохраняем выбор модели в БД
                        db = get_database()
                        db.set_user_image_model(callback_user_id, model_key)

                        model_name = available_models[model_key]["description"]
                        provider_name = "FLUX (Replicate)" if is_hf_model else "Gemini"

                        await answer_callback_query(
                            callback_query["id"],
                            f"✅ Модель генерации выбрана: {model_name}!"
                        )

                        # Открываем меню генерации
                        await send_telegram_message(
                            callback_chat_id,
                            f"✅ **Модель генерации выбрана:** {model_name}\n\n"
                            f"🤖 Провайдер: {provider_name}\n"
                            f"Теперь отправьте описание изображения, которое хотите создать!\n\n"
                            f"📊 Ваш уровень доступа: {user_access_level}"
                        )
                        continue

                    # Обработка кнопки генерации фото
                    elif callback_data == "gen_photo":
                        from backend.api.telegram_core import answer_callback_query

                        # Устанавливаем флаг ожидания описания
                        user_generating_photo[callback_user_id] = True

                        await answer_callback_query(
                            callback_query["id"],
                            "🎨 Отправьте мне описание изображения!"
                        )

                        await send_telegram_message(
                            callback_chat_id,
                            "🎨 **Генерация изображений**\n\nОтправьте описание изображения."
                        )
                        continue

                    # Обработка кнопки статистики
                    elif callback_data == "stats":
                        from backend.api.telegram_core import answer_callback_query, send_telegram_message
                        from backend.database.users_db import get_database
                        
                        await answer_callback_query(callback_query["id"])
                        
                        db = get_database()
                        stats = db.get_user_stats(callback_user_id)
                        
                        if stats:
                            level_info = {
                                "admin": "👑 Администратор (безлимит)",
                                "subscriber": "⭐ Подписчик (5 в день)",
                                "user": "👤 Пользователь (3 в день)"
                            }
                            level = stats.get('access_level', 'user')
                            first_name = stats.get('first_name', '')
                            username = stats.get('username', '')
                            
                            name_parts = []
                            if first_name:
                                name_parts.append(first_name)
                            if username:
                                name_parts.append(f"@{username}")
                            
                            name = " ".join(name_parts) if name_parts else f"User {callback_user_id}"
                            
                            stats_text = f"""📊 **Ваша статистика**

👤 {name}
🔑 Уровень: **{level_info.get(level, 'Пользователь')}**

📈 Генерации:
• Сегодня: {stats.get('daily_count', 0)}
• Всего: {stats.get('total_count', 0)}

📅 В боте с: {stats.get('created_at', 'неизвестно')[:10]}"""
                            await send_telegram_message(callback_chat_id, stats_text)
                        else:
                            await send_telegram_message(callback_chat_id, "❌ Не удалось получить статистику")
                        continue

                    # Обработка кнопки помощи
                    elif callback_data == "help":
                        from backend.api.telegram_core import answer_callback_query, send_telegram_message

                        await answer_callback_query(callback_query["id"])

                        help_text = """ℹ️ **Помощь - LiraAI MultiAssistant**

**Команды:**
• /start - Главное меню
• /menu - Показать клавиатуру
• /hide - Скрыть кла��иатуру
• /models - Выбор модели
• /generate [описание] - Генерация изображения
• /stats - Ваша статистика

**Возможности:**
• 💬 Общение на русском язы��е
• 🎨 Генерация изображений
• 🎤 Распознавание го��оса
• 📸 Анал��з фотографий

Бот запоминает п��следние 10 сообщений!"""
                        await send_telegram_message(callback_chat_id, help_text)
                        continue

                    # Обработка inline кнопок из welcome сообщения
                    elif callback_data.startswith("menu_"):
                        from backend.api.telegram_core import answer_callback_query, send_telegram_message

                        await answer_callback_query(callback_query["id"])

                        if callback_data == "menu_models":
                            # Открываем выбор моделей
                            user_selecting_model[callback_user_id] = True
                            keyboard = create_model_selection_keyboard()
                            await send_telegram_message(
                                callback_chat_id,
                                "🤖 **Выбор модели**\n\nВыберите модель для общени��:",
                                reply_markup=keyboard
                            )
                        elif callback_data == "menu_photo":
                            await send_telegram_message(
                                callback_chat_id,
                                "📸 **Режим фото**\n\nОтправьте мне фотографию, и я её проанализирую!"
                            )
                        elif callback_data == "menu_voice":
                            await send_telegram_message(
                                callback_chat_id,
                                "🎤 **Голосовой режим**\n\nОтправьте голосовое сообщение, и я распознаю его!"
                            )
                        elif callback_data == "gen_photo":
                            user_generating_photo[callback_user_id] = True
                            await send_telegram_message(
                                callback_chat_id,
                                "🎨 **Генерация изображений**\n\nОтправьте описание изображения."
                            )
                        elif callback_data == "stats":
                            # Показываем статистику
                            stats = db.get_user_stats(callback_user_id)
                            if stats:
                                level_info = {
                                    "admin": "👑 Администратор (безлимит)",
                                    "subscriber": "⭐ Подписчик (5 �� день)",
                                    "user": "👤 Пользователь (3 в день)"
                                }
                                level = stats.get('access_level', 'user')
                                first_name = stats.get('first_name', '')
                                username = stats.get('username', '')
                                name_parts = []
                                if first_name:
                                    name_parts.append(first_name)
                                if username:
                                    name_parts.append(f"@{username}")
                                name = " ".join(name_parts) if name_parts else f"User {callback_user_id}"
                                stats_text = f"""📊 **Ваша статистика**

👤 {name}
🔑 Уровень: **{level_info.get(level, 'Пользователь')}**

📈 Генерации:
• Сегодня: {stats.get('daily_count', 0)}
• Всего: {stats.get('total_count', 0)}

📅 В боте с: {stats.get('created_at', 'неизвестно')[:10]}"""
                                await send_telegram_message(callback_chat_id, stats_text)
                            else:
                                await send_telegram_message(callback_chat_id, "❌ Не удалось получить статистику")
                        continue

                    # Обработка кнопок для фото
                    if callback_data.startswith("photo_img_") or callback_data.startswith("photo_text_"):
                        from backend.api.telegram_photo_handler import handle_photo_callback
                        from backend.api.telegram_core import answer_callback_query

                        # Отвечаем на callback сразу, чтобы убрать "часики"
                        await answer_callback_query(callback_query["id"], "✅ Обрабатываю...")

                        # Обрабатываем callback (может занять время)
                        handled = await handle_photo_callback(
                            callback_query,
                            callback_data,
                            callback_chat_id,
                            callback_message_id,
                            callback_user_id,
                            temp_dir,
                            download_telegram_file,
                            config
                        )

                        if not handled:
                            await answer_callback_query(callback_query["id"], "❌ Ошибка обработки")
                        continue
            
            # Небольшая задержка между запросами
            await asyncio.sleep(0.1)
            
        except KeyboardInterrupt:
            logger.info(f"Остановка polling для {bot_name} по запросу пользователя")
            break
        except Exception as e:
            error_str = str(e)
            # Для ошибок 502 делаем экспоненциальную задержку
            if "502" in error_str or "Bad Gateway" in error_str:
                logger.warning(f"Ошибка 502 в polling для {bot_name}, увеличиваю задержку...")
                await asyncio.sleep(30)  # Большая задержка для 502
            else:
                logger.error(f"Ошибка в polling для {bot_name}: {e}")
                await asyncio.sleep(5)  # Обычная пауза перед повтором


async def start_telegram_polling():
    """Запускает polling для бота"""
    tokens = TELEGRAM_CONFIG.get("tokens", [])
    if not tokens:
        token = TELEGRAM_CONFIG.get("token")
        if token:
            tokens = [token]
        else:
            logger.error("TELEGRAM_BOT_TOKEN не настроен")
            return

    # Используем только первый токен
    token = tokens[0]

    # Запускаем polling
    await start_polling_for_bot(token, "Bot")

