"""
Модуль для работы с клавиатурами Telegram.
"""
from typing import List, Dict, Any


def create_main_menu_keyboard() -> Dict[str, Any]:
    """
    Создаёт основную reply-клавиатуру с режимами.

    Returns:
        JSON-структура клавиатуры для Telegram API
    """
    keyboard = {
        "keyboard": [
            [
                {"text": "🤖 Выбрать модель"},
                {"text": "🎨 Генерация"}
            ],
            [
                {"text": "📸 Фото"},
                {"text": "🎤 Голос"}
            ],
            [
                {"text": "📊 Статистика"},
                {"text": "📢 Подписаться"}
            ],
            [
                {"text": "💬 Поддержка"},
                {"text": "🔒 Политика конфиденциальности"}
            ],
            [
                {"text": "⬇️ Скрыть клавиатуру"}
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Выберите модель или режим"
    }
    return keyboard


def create_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Создаёт inline-клавиатуру (кнопки под сообщением).
    
    Args:
        buttons: Список списков кнопок [[{"text": "...", "callback_data": "..."}]]
    
    Returns:
        JSON-структура клавиатуры для Telegram API
    """
    return {
        "inline_keyboard": buttons
    }


def create_hide_keyboard() -> Dict[str, Any]:
    """
    Создаёт структуру для скрытия клавиатуры.
    
    Returns:
        JSON-структура для удаления клавиатуры
    """
    return {
        "remove_keyboard": True
    }


# Режимы работы бота
BOT_MODES = {
    "text": "💬 Текст",
    "voice": "🎤 Голос",
    "photo": "📸 Фото",
    "generation": "🎨 Генерация",
    "help": "💬 Поддержка",
    "privacy": "🔒 Политика конфиденциальности",
    "auto": "🤖 Авто",  # Автоматическое определение
    "select_model": "🤖 Выбрать модель",
    "hide": "⬇️ Скрыть клавиатуру",
    "stats": "📊 Статистика"
}


def create_model_selection_keyboard() -> Dict[str, Any]:
    """
    Создаёт клавиатуру для выбора модели.

    Returns:
        JSON-структура клавиатуры для Telegram API
    """
    keyboard = {
        "keyboard": [
            [
                {"text": "🚀 Groq Llama 3.3"},
                {"text": "🦙 Groq Llama 4"}
            ],
            [
                {"text": "🔍 Groq Scout"},
                {"text": "🌙 Groq Kimi K2"}
            ],
            [
                {"text": "⚡ Cerebras Llama 3.1"},
                {"text": "🧠 Cerebras GPT-oss 120B"}
            ],
            [
                {"text": "☁️ OpenRouter Gemma 3N"}
            ],
            [
                {"text": "◀️ Назад к меню"}
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Выберите модель"
    }
    return keyboard


def get_mode_from_button(text: str) -> str:
    """
    Определяет режим по тексту кнопки.
    
    Args:
        text: Текст кнопки (например, "💬 Текст")
    
    Returns:
        Название режима (например, "text")
    """
    mode_map = {v: k for k, v in BOT_MODES.items()}
    return mode_map.get(text, "auto")


def get_model_from_button(text: str) -> str:
    """
    Определяет модель по тексту кнопки.

    Args:
        text: Текст кнопки (например, "🚀 Groq Llama 3.3")

    Returns:
        ID модели (например, "groq-llama")
    """
    model_map = {
        # Groq модели
        "🚀 Groq Llama 3.3": "groq-llama",
        "🦙 Groq Llama 4": "groq-maverick",
        "🔍 Groq Scout": "groq-scout",
        "🌙 Groq Kimi K2": "groq-kimi",
        # Cerebras модели
        "⚡ Cerebras Llama 3.1": "cerebras-llama",
        "🧠 Cerebras GPT-oss 120B": "cerebras-gpt",
        # OpenRouter модели
        "☁️ OpenRouter Gemma 3N": "openrouter-gemma",
    }
    return model_map.get(text, None)


def get_mode_prompt(mode: str) -> str:
    """
    Возвращает подсказку для режима.

    Args:
        mode: Название режима

    Returns:
        Текст подсказки
    """
    prompts = {
        "text": "💬 **Режим текста**\n\nПросто напишите сообщение, и я отвечу!",
        "voice": "🎤 **Голосовой режим**\n\nОтправьте голосовое сообщение, и я распознаю его!",
        "photo": "📸 **Режим фото**\n\nОтправьте фото, и я его проанализирую!",
        "generation": "🎨 **Генерация изображений**\n\nОпишите изображение, которое хотите создать!",
        "help": "❓ **Помощь**\n\nИспользуйте кнопки ниже или отправьте /help для информации.",
        "auto": "🤖 **Автоматический режим**\n\nЯ сам определю, что вы хотите сделать!",
        "select_model": "🤖 **Выбор модели**\n\nВыберите модель из списка ниже!",
        "hide": "⬇️ Клавиатура скрыта. Используйте /menu чтобы вернуть.",
        "stats": "📊 **Статистика**\n\nПоказываю вашу статистику...",
        "select_image_model": "🎨 **Выбор модели генерации**\n\nВыберите модель для генерации изображения:"
    }
    return prompts.get(mode, "")


def create_image_model_selection_keyboard(access_level: str = "user") -> Dict[str, Any]:
    """
    Создаёт inline-клавиатуру для выбора модели генерации изображений.

    Args:
        access_level: Уровень доступа (admin, subscriber, user)

    Returns:
        JSON-структура клавиатуры для Telegram API
    """
    # Модели по уровням доступа - каждая кнопка в отдельном массиве (строка)
    models_by_level = {
        "admin": [
            # [{"text": "✨ Gemini 2.5 Flash", "callback_data": "img_gemini-flash"}],  # В разработке
            [{"text": "🎨 Z-Image (Polza.ai)", "callback_data": "img_polza-zimage"}],
        ],
        "subscriber": [
            # [{"text": "✨ Gemini 2.5 Flash", "callback_data": "img_gemini-flash"}],  # В разработке
            [{"text": "🎨 Z-Image (Polza.ai)", "callback_data": "img_polza-zimage"}],
        ],
        "user": [
            # [{"text": "✨ Gemini 2.5 Flash", "callback_data": "img_gemini-flash"}],  # В разработке
            [{"text": "🎨 Z-Image (Polza.ai)", "callback_data": "img_polza-zimage"}],
        ]
    }

    keyboard_models = models_by_level.get(access_level, models_by_level["user"])

    # Добавляем кнопку "Назад"
    keyboard_models.append([{"text": "◀️ Назад к меню", "callback_data": "menu_back"}])

    keyboard = {
        "inline_keyboard": keyboard_models,
    }
    return keyboard
