"""
Модуль для красивого форматирования статистики и лимитов.
UI/UX улучшения из документа UI_UX_RECOMMENDATIONS.md
"""
from typing import Dict, Any
from datetime import datetime


# ============================================
# Константы для форматирования
# ============================================

DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
THIN_DIVIDER = "────────────────────"
DOT_DIVIDER = "· · · · · · · · · · · ·"

# Эмодзи для уровней
LEVEL_EMOJI = {
    "admin": "👑",
    "sub+": "🚀",
    "subscriber": "⭐",
    "user": "👤"
}

# Описания уровней
LEVEL_DESCRIPTIONS = {
    "admin": "Админ (безлимит)",
    "sub+": "sub+ (30/день)",
    "subscriber": "Подписчик (5/день)",
    "user": "Пользователь (3/день)"
}

# Статусы лимитов
STATUS_ICONS = {
    "available": "✅",
    "warning": "⚠️",
    "exhausted": "🔒",
    "unlimited": "∞"
}


def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """
    Создаёт текстовый прогресс-бар.
    
    Args:
        current: Текущее значение
        total: Максимальное значение
        length: Длина бара в символах
    
    Returns:
        Строка с прогресс-баром
    """
    if total <= 0 or total == -1:
        return f"{'█' * length} ∞ Безлимит"
    
    percentage = min(current / total, 1.0)
    filled = int(length * percentage)
    bar = "█" * filled + "░" * (length - filled)
    
    return f"{bar} {current}/{total} ({percentage:.0%})"


def get_limit_status(daily: int, limit: int) -> tuple[str, str]:
    """
    Определяет статус лимита.
    
    Returns:
        (icon, text) - иконка и текст статуса
    """
    if limit <= 0 or limit == -1:
        return STATUS_ICONS["unlimited"], "Безлимит"
    
    if daily >= limit:
        return STATUS_ICONS["exhausted"], "Лимит исчерпан"
    elif daily >= limit * 0.8:
        return STATUS_ICONS["warning"], "Скоро лимит"
    else:
        return STATUS_ICONS["available"], "Доступно"


def format_stats_card(stats: Dict[str, Any]) -> str:
    """
    Форматирует статистику пользователя в виде красивой карточки.
    
    Args:
        stats: Словарь со статистикой пользователя
    
    Returns:
        Отформатированная строка с карточкой
    """
    # Извлекаем данные
    first_name = stats.get('first_name', '')
    username = stats.get('username', '')
    access_level = stats.get('access_level', 'user')
    daily_count = stats.get('daily_count', 0)
    total_count = stats.get('total_count', 0)
    messages_today = stats.get('messages_today', 0)
    created_at = stats.get('created_at', '')
    
    # Получаем лимит
    daily_limit = stats.get('daily_limit', 3)
    
    # Формируем имя
    name_parts = []
    if first_name:
        name_parts.append(first_name)
    if username:
        name_parts.append(f"@{username}")
    user_name = " ".join(name_parts) if name_parts else "Пользователь"
    
    # Начинаем формировать карточку
    text = "┌─────────────────────────────────┐\n"
    text += "│ 📊 ВАША СТАТИСТИКА              │\n"
    text += "├─────────────────────────────────┤\n"
    
    # Имя пользователя
    text += f"│ 👤 {user_name:<31} │\n"
    
    # Уровень с эмодзи
    level_emoji = LEVEL_EMOJI.get(access_level, "👤")
    level_desc = LEVEL_DESCRIPTIONS.get(access_level, "Пользователь")
    text += f"│ {level_emoji} {level_desc:<29} │\n"
    
    text += "│                                 │\n"
    
    # Прогресс-бар генераций
    text += "│ 📈 Генерации изображений:       │\n"
    
    if daily_limit <= 0 or daily_limit == -1:
        # Безлимит
        bar = "█" * 20
        text += f"│ ├─ Сегодня: {bar} ∞ │\n"
    else:
        # Создаём прогресс-бар
        percentage = min(daily_count / daily_limit, 1.0)
        filled = int(20 * percentage)
        bar = "█" * filled + "░" * (20 - filled)
        
        status_icon, _ = get_limit_status(daily_count, daily_limit)
        text += f"│ ├─ Сегодня: {bar} {status_icon} │\n"
    
    text += f"│ └─ Всего: {total_count:<25} │\n"
    
    text += "│                                 │\n"
    
    # Сообщения
    text += f"│ 💬 Сообщения в боте:            │\n"
    text += f"│   • Сегодня: {messages_today:<22} │\n"
    
    # Дата регистрации
    if created_at:
        try:
            # Пытаемся распарсить дату
            if 'T' in created_at:
                date_str = created_at[:10]
            else:
                date_str = created_at[:10]
            text += f"│   • В боте с: {date_str:<21} │\n"
        except:
            text += f"│   • В боте с: {created_at[:10]:<21} │\n"
    else:
        text += "│   • В боте с: N/A                   │\n"
    
    text += "└─────────────────────────────────┘"
    
    return text


def format_limit_info(limit_info: Dict[str, Any]) -> str:
    """
    Форматирует информацию о лимитах с прогресс-баром.
    
    Args:
        limit_info: Словарь с информацией о лимитах
    
    Returns:
        Отформатированная строка с прогресс-баром
    """
    daily = limit_info.get('daily_count', 0)
    limit = limit_info.get('daily_limit', 3)
    reset_time = limit_info.get('reset_time', 'N/A')
    total = limit_info.get('total_count', 0)
    
    # Начинаем формировать текст
    text = "📊 **ЛИМИТЫ ГЕНЕРАЦИИ**\n\n"
    
    # Прогресс-бар
    if limit <= 0 or limit == -1:
        bar = "█" * 20
        text += f"{bar}\n"
        text += f"{STATUS_ICONS['unlimited']} **Безлимитный доступ**\n"
    else:
        percentage = min(daily / limit, 1.0)
        filled = int(20 * percentage)
        bar = "█" * filled + "░" * (20 - filled)
        
        status_icon, status_text = get_limit_status(daily, limit)
        
        text += f"{bar}\n"
        text += f"{status_icon} **{status_text}**\n\n"
        
        # Детали
        text += f"📈 Использовано: `{daily}/{limit}` ({percentage:.0%})\n"
        text += f"📊 Всего генераций: `{total}`\n"
        
        if reset_time and reset_time != 'N/A':
            text += f"⏱️ Лимит обновится: _{reset_time}_"
    
    return text


def format_short_stats(stats: Dict[str, Any]) -> str:
    """
    Короткая версия статистики для быстрых уведомлений.
    
    Args:
        stats: Словарь со статистикой
    
    Returns:
        Короткая отформатированная строка
    """
    access_level = stats.get('access_level', 'user')
    daily_count = stats.get('daily_count', 0)
    daily_limit = stats.get('daily_limit', 3)
    total_count = stats.get('total_count', 0)
    
    level_emoji = LEVEL_EMOJI.get(access_level, "👤")
    level_desc = LEVEL_DESCRIPTIONS.get(access_level, "Пользователь")
    
    text = f"📊 **Статистика**\n\n"
    text += f"{level_emoji} Уровень: *{level_desc}*\n\n"
    
    if daily_limit <= 0 or daily_limit == -1:
        text += "📈 Генерации: *∞ Безлимит*\n"
    else:
        percentage = min(daily_count / daily_limit, 1.0)
        text += f"📈 Генерации: `{daily_count}/{daily_limit}` ({percentage:.0%})\n"
    
    text += f"📊 Всего: `{total_count}`"
    
    return text


def format_level_display(access_level: str) -> str:
    """
    Красиво форматирует отображение уровня.
    
    Args:
        access_level: Уровень доступа
    
    Returns:
        Отформатированная строка с эмодзи и описанием
    """
    level_emoji = LEVEL_EMOJI.get(access_level, "👤")
    level_desc = LEVEL_DESCRIPTIONS.get(access_level, "Пользователь")
    
    return f"{level_emoji} {level_desc}"


def format_time_ago(dt: datetime) -> str:
    """
    Форматирует время в стиле '5 мин назад'.
    
    Args:
        dt: datetime объект
    
    Returns:
        Строка в формате 'X мин/час/дн. назад'
    """
    now = datetime.now()
    diff = now - dt
    
    minutes = int(diff.total_seconds() / 60)
    hours = int(minutes / 60)
    days = int(hours / 24)
    
    if days > 0:
        return f"{days} дн. назад"
    elif hours > 0:
        return f"{hours} ч. назад"
    elif minutes > 0:
        return f"{minutes} мин. назад"
    else:
        return "Только что"


def format_admin_stats_card(stats: Dict[str, Any]) -> str:
    """
    Форматирует статистику администратора в виде карточки.
    
    Args:
        stats: Словарь со статистикой администратора
    
    Returns:
        Отформатированная строка
    """
    total_actions = stats.get('total_actions', 0)
    successful = stats.get('successful_actions', 0)
    failed = stats.get('failed_actions', 0)
    level_changes = stats.get('level_changes', 0)
    users_added = stats.get('users_added', 0)
    users_removed = stats.get('users_removed', 0)
    history_views = stats.get('history_views', 0)
    
    text = "┌─────────────────────────────────┐\n"
    text += "│ 👑 СТАТИСТИКА АДМИНИСТРАТОРА    │\n"
    text += "├─────────────────────────────────┤\n"
    
    # Общие действия
    success_rate = (successful / total_actions * 100) if total_actions > 0 else 0
    text += f"│ 🔧 Всего действий: {total_actions:<16} │\n"
    text += f"│ ✅ Успешных: {successful:<22} │\n"
    text += f"│ ❌ Ошибок: {failed:<23} │\n"
    text += f"│ 📊 Эффективность: {success_rate:.0f}%{' ' * (17 - len(f'{success_rate:.0f}%'))} │\n"
    
    text += "│                                 │\n"
    
    # Детализация
    text += "│ 📈 Детализация:                 │\n"
    text += f"│ ├─ Изменений уровня: {level_changes:<14} │\n"
    text += f"│ ├─ Добавлено пользователей: {users_added:<7} │\n"
    text += f"│ ├─ Удалено пользователей: {users_removed:<8} │\n"
    text += f"│ └─ Просмотров истории: {history_views:<12} │\n"
    
    text += "└─────────────────────────────────┘"
    
    return text
