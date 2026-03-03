"""
Обработчик callback кнопок для инлайн-меню.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger("bot.callbacks")


async def handle_callback(
    callback_query: Dict[str, Any],
    callback_data: str,
    callback_chat_id: str,
    callback_message_id: int,
    callback_user_id: str,
    send_telegram_message,
    edit_message_text,
    answer_callback_query,
    user_models: dict,
    AVAILABLE_MODELS: dict
):
    """Обрабатывает callback кнопки"""
    
    # Обработка кнопок выбора модели
    if callback_data.startswith("model_"):
        model_key = callback_data.replace("model_", "")
        if model_key in AVAILABLE_MODELS:
            # Сохраняем выбор пользователя
            user_models[callback_user_id] = AVAILABLE_MODELS[model_key]
            
            # Отвечаем на callback
            await answer_callback_query(
                callback_query["id"],
                f"✅ Модель: {model_key}"
            )
            
            # Кнопка "Назад"
            back_buttons = [[{"text": "◀️ Назад", "callback_data": "back_to_main"}]]
            
            await edit_message_text(
                callback_chat_id,
                callback_message_id,
                f"✅ Модель выбрана: **{model_key}**\n\nТеперь я буду использовать эту модель.",
                back_buttons
            )
        return True
    
    # Обработка кнопки генерации фото
    elif callback_data == "gen_photo":
        await answer_callback_query(
            callback_query["id"],
            "🎨 Отправьте описание изображения!"
        )
        return True
    
    # Обработка кнопки помощи
    elif callback_data == "help":
        await answer_callback_query(callback_query["id"])
        
        help_text = """ℹ️ **Помощь**

**Команды:**
• /start - Главное меню
• /models - Выбор модели
• /stats - Статистика
• /admin - Админ панель

**Возможности:**
• 💬 Общение
• 🎨 Генерация фото
• 🎤 Голосовые
• 📸 Анализ фото"""
        
        back_buttons = [[{"text": "◀️ Назад", "callback_data": "back_to_main"}]]
        
        await edit_message_text(
            callback_chat_id,
            callback_message_id,
            help_text,
            back_buttons
        )
        return True
    
    # Обработка кнопки статистики
    elif callback_data == "stats":
        await answer_callback_query(callback_query["id"])
        
        from backend.database.users_db import get_database
        db = get_database()
        stats = db.get_user_stats(callback_user_id)
        
        if stats:
            level_info = {
                "admin": "👑 Админ (безлимит)",
                "subscriber": "⭐ Подписчик (5/день)",
                "sub+": "🚀 sub+ (30/день)",
                "user": "👤 Пользователь (3/день)"
            }
            level = stats.get('access_level', 'user')

            stats_text = f"""📊 **Статистика**

🔑 Уровень: {level_info.get(level, 'Пользователь')}

📈 Генерации:
• Сегодня: {stats.get('daily_count', 0)}
• Всего: {stats.get('total_count', 0)}"""
            
            back_buttons = [[{"text": "◀️ Назад", "callback_data": "back_to_main"}]]
            
            await edit_message_text(
                callback_chat_id,
                callback_message_id,
                stats_text,
                back_buttons
            )
        return True
    
    # Обработка кнопки "Назад"
    elif callback_data == "back_to_main":
        await answer_callback_query(callback_query["id"])
        
        # Возвращаем главное меню
        buttons = [
            [
                {"text": "🚀 Llama 3.3", "callback_data": "model_groq-llama"},
                {"text": "🦙 Llama 4", "callback_data": "model_groq-maverick"},
            ],
            [
                {"text": "🔍 Scout", "callback_data": "model_groq-scout"},
                {"text": "🌙 Kimi K2", "callback_data": "model_groq-kimi"},
            ],
            [
                {"text": "☀️ Solar", "callback_data": "model_solar"},
                {"text": "🔱 Trinity", "callback_data": "model_trinity"},
            ],
            [
                {"text": "🤖 GLM-4.5", "callback_data": "model_glm"},
            ],
            [
                {"text": "🎨 Генерировать фото", "callback_data": "gen_photo"},
            ],
            [
                {"text": "📊 Статистика", "callback_data": "stats"},
                {"text": "📢 Подписаться", "url": "https://t.me/liranexus"},
            ],
            [
                {"text": "ℹ️ Помощь", "callback_data": "help"},
            ]
        ]
        
        welcome_text = """👋 **LiraAI MultiAssistant**

💬 Общение
🎨 Генерация фото (Z-Image via Polza.ai)
🎤 Голосовые
📸 Анализ фото

🆓 Все модели БЕСПЛАТНЫЕ!

⚠️ Gemini Image - в разработке"""
        
        await edit_message_text(
            callback_chat_id,
            callback_message_id,
            welcome_text,
            buttons
        )
        return True
    
    return False
