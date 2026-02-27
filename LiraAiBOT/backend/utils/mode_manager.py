"""
Модуль для управления режимами пользователей.
Хранит состояние режима для каждого пользователя.
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("bot.mode_manager")


class UserModeManager:
    """Менеджер режимов пользователей"""
    
    def __init__(self):
        # Хранилище: user_id -> {mode, last_changed, message_count}
        self._user_modes: Dict[str, Dict] = {}
    
    def set_mode(self, user_id: str, mode: str):
        """
        Устанавливает режим для пользователя.
        
        Args:
            user_id: ID пользователя
            mode: Режим (text, voice, photo, generation, help, auto)
        """
        if user_id not in self._user_modes:
            self._user_modes[user_id] = {
                "mode": "auto",
                "last_changed": datetime.now(),
                "message_count": 0
            }
        
        self._user_modes[user_id]["mode"] = mode
        self._user_modes[user_id]["last_changed"] = datetime.now()
        
        logger.info(f"🔧 Пользователь {user_id} переключен в режим: {mode}")
    
    def get_mode(self, user_id: str) -> str:
        """
        Получает режим пользователя.
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Название режима
        """
        if user_id not in self._user_modes:
            return "auto"  # По умолчанию автоматический режим
        
        # Авто-сброс в auto после 10 сообщений в режиме help
        user_data = self._user_modes[user_id]
        if user_data["mode"] == "help":
            user_data["message_count"] += 1
            if user_data["message_count"] >= 10:
                self.set_mode(user_id, "auto")
                return "auto"
        
        return user_data["mode"]
    
    def reset_mode(self, user_id: str):
        """
        Сбрасывает режим пользователя в auto.
        
        Args:
            user_id: ID пользователя
        """
        self.set_mode(user_id, "auto")
    
    def increment_message_count(self, user_id: str):
        """
        Увеличивает счётчик сообщений пользователя.
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self._user_modes:
            self._user_modes[user_id]["message_count"] += 1


# Глобальный экземпляр
_mode_manager: Optional[UserModeManager] = None


def get_mode_manager() -> UserModeManager:
    """Получает или создаёт менеджер режимов"""
    global _mode_manager
    if _mode_manager is None:
        _mode_manager = UserModeManager()
    return _mode_manager
