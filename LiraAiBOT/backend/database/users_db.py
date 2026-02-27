"""
Модуль для работы с базой данных пользователей.
SQLite для хранения пользователей, лимитов генерации и уровней доступа.
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger("bot.database")

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent.parent / "data" / "bot.db"

# Создаем директорию если не существует
DB_PATH.parent.mkdir(exist_ok=True, parents=True)

# Уровни доступа и квоты
ACCESS_LEVELS = {
    "admin": {"daily_limit": -1, "description": "Администратор (безлимит)"},
    "subscriber": {"daily_limit": 5, "description": "Подписчик (5 в день)"},
    "user": {"daily_limit": 3, "description": "Пользователь (3 в день)"}
}


class BotDatabase:
    """База данных для хранения пользователей и лимитов"""

    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
        logger.info(f"✅ База данных инициализирована: {self.db_path}")

    def _get_connection(self):
        """Получает соединение с БД"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Инициализирует базу данных"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                access_level TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица лимитов генерации изображений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_limits (
                user_id TEXT PRIMARY KEY,
                daily_count INTEGER DEFAULT 0,
                last_reset DATE DEFAULT CURRENT_DATE,
                total_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Таблица истории генераций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                prompt TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Таблица уровней доступа (квоты)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_quotas (
                level_name TEXT PRIMARY KEY,
                daily_limit INTEGER NOT NULL,
                description TEXT
            )
        """)

        # Таблица настроек бота (для тех.работ и других настроек)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Заполняем уровни доступа
        for level, quota in ACCESS_LEVELS.items():
            cursor.execute("""
                INSERT OR REPLACE INTO access_quotas (level_name, daily_limit, description)
                VALUES (?, ?, ?)
            """, (level, quota["daily_limit"], quota["description"]))

        conn.commit()
        conn.close()
        logger.info("✅ Таблицы базы данных созданы")

    def add_or_update_user(self, user_id: str, username: str = None, 
                          first_name: str = None, last_name: str = None):
        """Добавляет или обновляет пользователя (всегда обновляет username если есть)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Проверяем существует ли пользователь
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()

        if exists:
            # Обновляем last_seen и username (если передан)
            if username:
                cursor.execute("""
                    UPDATE users 
                    SET last_seen = CURRENT_TIMESTAMP,
                        username = ?,
                        first_name = COALESCE(?, first_name),
                        last_name = COALESCE(?, last_name)
                    WHERE user_id = ?
                """, (username, first_name, last_name, user_id))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET last_seen = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
        else:
            # Добавляем нового пользователя
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))

            # Инициализируем лимиты
            cursor.execute("""
                INSERT INTO generation_limits (user_id, daily_count, last_reset, total_count)
                VALUES (?, 0, CURRENT_DATE, 0)
            """, (user_id,))

        conn.commit()
        conn.close()

    def get_user_access_level(self, user_id: str) -> str:
        """Получает уровень доступа пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT access_level FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        return row["access_level"] if row else "user"

    def set_user_access_level(self, user_id: str, level: str) -> bool:
        """Устанавливает уровень доступа пользователя"""
        if level not in ACCESS_LEVELS:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users SET access_level = ? WHERE user_id = ?
        """, (level, user_id))

        conn.commit()
        conn.close()
        return True

    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает статистику пользователя (всегда свежие данные)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Информация о пользователе - получаем свежие данные
        cursor.execute("""
            SELECT user_id, username, first_name, last_name, access_level, created_at, last_seen
            FROM users 
            WHERE user_id = ?
        """, (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return None

        # Лимиты - получаем свежие данные с обновлением
        cursor.execute("""
            SELECT daily_count, last_reset, total_count
            FROM generation_limits 
            WHERE user_id = ?
        """, (user_id,))
        limit_row = cursor.fetchone()

        # Количество генераций за сегодня
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM generation_history
            WHERE user_id = ? AND DATE(created_at) = CURRENT_DATE
        """, (user_id,))
        today_count = cursor.fetchone()["count"]

        conn.close()

        return {
            "user_id": user_row["user_id"],
            "username": user_row["username"],
            "first_name": user_row["first_name"],
            "last_name": user_row["last_name"],
            "access_level": user_row["access_level"],
            "created_at": user_row["created_at"],
            "last_seen": user_row["last_seen"],
            "daily_count": limit_row["daily_count"] if limit_row else 0,
            "total_count": limit_row["total_count"] if limit_row else 0,
            "today_generations": today_count
        }
    
    def set_maintenance_mode(self, enabled: bool, until_time: str = None):
        """
        Включает/выключает режим тех.работ.
        
        Args:
            enabled: True - включить, False - выключить
            until_time: Время окончания в формате "HH:MM"
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Создаём таблицу для настроек если нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Сохраняем настройки
        cursor.execute("""
            INSERT OR REPLACE INTO bot_settings (key, value)
            VALUES ('maintenance_enabled', ?)
        """, ("1" if enabled else "0",))
        
        if until_time:
            cursor.execute("""
                INSERT OR REPLACE INTO bot_settings (key, value)
                VALUES ('maintenance_until', ?)
            """, (until_time,))
        
        conn.commit()
        conn.close()
    
    def get_maintenance_mode(self) -> Dict[str, Any]:
        """
        Получает статус режима тех.работ.
        
        Returns:
            {
                "enabled": bool,
                "until_time": str or None
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT key, value FROM bot_settings WHERE key IN ('maintenance_enabled', 'maintenance_until')")
            rows = cursor.fetchall()
            
            settings = {row["key"]: row["value"] for row in rows}
            
            return {
                "enabled": settings.get("maintenance_enabled", "0") == "1",
                "until_time": settings.get("maintenance_until", None)
            }
        finally:
            conn.close()
    
    def get_all_users_for_notification(self) -> List[str]:
        """
        Получает список всех user_id для рассылки уведомлений.
        
        Returns:
            Список user_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM users")
        user_ids = [row["user_id"] for row in cursor.fetchall()]
        
        conn.close()
        return user_ids

    def check_generation_limit(self, user_id: str) -> Dict[str, Any]:
        """
        Проверяет лимит генерации для пользователя
        
        Returns:
            {
                "allowed": bool,
                "daily_count": int,
                "daily_limit": int,
                "total_count": int,
                "reset_time": str,
                "access_level": str
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Получаем уровень доступа и лимиты
        cursor.execute("""
            SELECT u.access_level, g.daily_count, g.last_reset, g.total_count
            FROM users u
            JOIN generation_limits g ON u.user_id = g.user_id
            WHERE u.user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            # Пользователь не найден, создаем запись
            self.add_or_update_user(user_id)
            return {
                "allowed": True,
                "daily_count": 0,
                "daily_limit": 3,
                "total_count": 0,
                "reset_time": "сегодня",
                "access_level": "user"
            }

        access_level = row["access_level"]
        daily_count = row["daily_count"]
        last_reset = row["last_reset"]
        total_count = row["total_count"]

        # Получаем лимит для уровня доступа
        daily_limit = ACCESS_LEVELS.get(access_level, {}).get("daily_limit", 3)

        # Проверяем нужно ли сбросить счетчик (новый день)
        today = datetime.now().date()
        last_reset_date = datetime.strptime(last_reset, "%Y-%m-%d").date() if last_reset else today

        if last_reset_date < today:
            # Новый день - сбрасываем счетчик
            self._reset_daily_limit(user_id)
            daily_count = 0
            last_reset = str(today)

        # -1 означает безлимит
        allowed = daily_limit == -1 or daily_count < daily_limit

        # Время сброса (полночь)
        reset_time = "сегодня в 00:00"

        return {
            "allowed": allowed,
            "daily_count": daily_count,
            "daily_limit": daily_limit,
            "total_count": total_count,
            "reset_time": reset_time,
            "access_level": access_level
        }

    def _reset_daily_limit(self, user_id: str):
        """Сбрасывает дневной счетчик"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE generation_limits
            SET daily_count = 0, last_reset = CURRENT_DATE
            WHERE user_id = ?
        """, (user_id,))

        conn.commit()
        conn.close()

    def increment_generation_count(self, user_id: str, prompt: str = None):
        """Увеличивает счетчик генераций"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Увеличиваем счетчики
        cursor.execute("""
            UPDATE generation_limits
            SET daily_count = daily_count + 1,
                total_count = total_count + 1,
                last_reset = CURRENT_DATE
            WHERE user_id = ?
        """, (user_id,))

        # Добавляем запись в историю
        if prompt:
            cursor.execute("""
                INSERT INTO generation_history (user_id, prompt)
                VALUES (?, ?)
            """, (user_id, prompt))

        conn.commit()
        conn.close()

    def get_all_users_count(self) -> int:
        """Получает общее количество пользователей"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()["count"]

        conn.close()
        return count

    def get_all_users(self) -> list:
        """Получает всех пользователей"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.*, g.daily_count, g.total_count, g.last_reset
            FROM users u
            JOIN generation_limits g ON u.user_id = g.user_id
            ORDER BY u.created_at DESC
        """)

        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users

    def is_admin(self, user_id: str) -> bool:
        """Проверяет является ли пользователь администратором"""
        return self.get_user_access_level(user_id) == "admin"

    def remove_user(self, user_id: str) -> bool:
        """Удаляет пользователя из базы данных"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Удаляем из generation_limits
            cursor.execute("DELETE FROM generation_limits WHERE user_id = ?", (user_id,))
            
            # Удаляем из generation_history
            cursor.execute("DELETE FROM generation_history WHERE user_id = ?", (user_id,))
            
            # Удаляем из users
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления пользователя: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


# Глобальный экземпляр
_db: Optional[BotDatabase] = None


def get_database() -> BotDatabase:
    """Получает или создает экземпляр базы данных"""
    global _db
    if _db is None:
        _db = BotDatabase()
    return _db
