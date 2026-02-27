"""
Модуль для работы с базой данных пользователей.
Поддерживает Supabase (PostgreSQL) и SQLite fallback.
"""
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger("bot.database")

# Путь к SQLite базе данных (только для локальной разработки)
DB_PATH = Path(__file__).parent.parent.parent / "data" / "bot.db"

# Создаем директорию если не существует
DB_PATH.parent.mkdir(exist_ok=True, parents=True)

# Проверяем использование Supabase
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Supabase клиент
supabase = None
if USE_SUPABASE and SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase клиент инициализирован")
    except ImportError:
        logger.warning("⚠️ supabase пакет не установлен. Установи: pip install supabase")
        USE_SUPABASE = False
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Supabase: {e}")
        USE_SUPABASE = False

if not USE_SUPABASE:
    logger.info("ℹ️ Используем SQLite базу данных")

# Кэш пользователей в памяти (user_id -> данные)
_user_cache: Dict[str, Dict] = {}
_limits_cache: Dict[str, Dict] = {}

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
        if not USE_SUPABASE:
            self._init_db()
            logger.info(f"✅ База данных инициализирована: {self.db_path}")
        else:
            logger.info(f"✅ Supabase база данных инициализирована: {SUPABASE_URL}")

    def _get_connection(self):
        """Получает соединение с SQLite БД"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Инициализирует SQLite базу данных"""
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

        # Таблица настроек бота
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
        """Добавляет или обновляет пользователя (только Supabase + кэш)"""
        
        # Обновляем кэш
        if user_id not in _user_cache:
            _user_cache[user_id] = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "access_level": "user"
            }
        else:
            if username:
                _user_cache[user_id]["username"] = username
            if first_name:
                _user_cache[user_id]["first_name"] = first_name
            if last_name:
                _user_cache[user_id]["last_name"] = last_name
        
        # Если используем Supabase - отправляем данные
        if USE_SUPABASE and supabase:
            try:
                data = {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "last_seen": datetime.now().isoformat()
                }
                
                # Проверяем существует ли пользователь
                result = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
                
                if result.data:
                    # Обновляем
                    supabase.table("users").update(data).eq("user_id", user_id).execute()
                else:
                    # Создаём
                    supabase.table("users").insert(data).execute()
                    
                    # Создаём лимиты
                    supabase.table("generation_limits").insert({
                        "user_id": user_id,
                        "daily_count": 0,
                        "total_count": 0
                    }).execute()
                    
            except Exception as e:
                # Логируем ошибку но не падаем - кэш работает
                logger.warning(f"⚠️ Supabase недоступен, работаем в памяти: {e}")
        
        # SQLite только для локальной разработки
        elif not USE_SUPABASE:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()
            if exists:
                if username:
                    cursor.execute("""
                        UPDATE users SET last_seen = CURRENT_TIMESTAMP, username = ? WHERE user_id = ?
                    """, (username, user_id))
                else:
                    cursor.execute("UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
            else:
                cursor.execute("INSERT INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                              (user_id, username, first_name, last_name))
                cursor.execute("INSERT INTO generation_limits (user_id, daily_count, last_reset, total_count) VALUES (?, 0, CURRENT_DATE, 0)", (user_id,))
            conn.commit()
            conn.close()

    def get_user_access_level(self, user_id: str) -> str:
        """Получает уровень доступа пользователя (сначала кэш)"""
        # Проверяем кэш
        if user_id in _user_cache:
            return _user_cache[user_id].get("access_level", "user")
        
        # Если используем Supabase
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("users").select("access_level").eq("user_id", user_id).execute()
                if result.data:
                    level = result.data[0].get("access_level", "user")
                    # Кэшируем
                    if user_id not in _user_cache:
                        _user_cache[user_id] = {"user_id": user_id, "access_level": level}
                    else:
                        _user_cache[user_id]["access_level"] = level
                    return level
            except Exception as e:
                logger.warning(f"⚠️ Ошибка Supabase: {e}")
                return "user"  # Возвращаем дефолтный уровень
        
        # SQLite только для локальной разработки
        if not USE_SUPABASE:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT access_level FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            return row["access_level"] if row else "user"
        
        return "user"

    def set_user_access_level(self, user_id: str, level: str) -> bool:
        """Устанавливает уровень доступа пользователя"""
        if level not in ACCESS_LEVELS:
            return False
        
        if USE_SUPABASE and supabase:
            try:
                supabase.table("users").update({"access_level": level}).eq("user_id", user_id).execute()
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в set_user_access_level: {e}")
                return False
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET access_level = ? WHERE user_id = ?", (level, user_id))
        conn.commit()
        conn.close()
        return True

    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает статистику пользователя"""
        if USE_SUPABASE and supabase:
            try:
                # Информация о пользователе
                user_result = supabase.table("users").select("*").eq("user_id", user_id).execute()
                if not user_result.data:
                    return None
                user_row = user_result.data[0]
                
                # Лимиты
                limits_result = supabase.table("generation_limits").select("*").eq("user_id", user_id).execute()
                limit_row = limits_result.data[0] if limits_result.data else None
                
                # Количество генераций за сегодня
                today = datetime.now().date().isoformat()
                history_result = supabase.table("generation_history").select("id", count="exact").eq("user_id", user_id).gte("created_at", today).execute()
                
                return {
                    "user_id": user_row.get("user_id"),
                    "username": user_row.get("username"),
                    "first_name": user_row.get("first_name"),
                    "last_name": user_row.get("last_name"),
                    "access_level": user_row.get("access_level"),
                    "created_at": user_row.get("created_at"),
                    "last_seen": user_row.get("last_seen"),
                    "daily_count": limit_row.get("daily_count", 0) if limit_row else 0,
                    "total_count": limit_row.get("total_count", 0) if limit_row else 0,
                    "today_generations": history_result.count
                }
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в get_user_stats: {e}")
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, first_name, last_name, access_level, created_at, last_seen
            FROM users WHERE user_id = ?
        """, (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return None

        cursor.execute("""
            SELECT daily_count, last_reset, total_count
            FROM generation_limits WHERE user_id = ?
        """, (user_id,))
        limit_row = cursor.fetchone()

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
        """Включает/выключает режим тех.работ"""
        data = {
            "key": "maintenance_enabled",
            "value": "1" if enabled else "0"
        }
        
        if USE_SUPABASE and supabase:
            try:
                supabase.table("bot_settings").upsert(data).execute()
                if until_time:
                    supabase.table("bot_settings").upsert({"key": "maintenance_until", "value": until_time}).execute()
                return
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в set_maintenance_mode: {e}")
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('maintenance_enabled', ?)
        """, ("1" if enabled else "0",))
        if until_time:
            cursor.execute("""
                INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('maintenance_until', ?)
            """, (until_time,))
        conn.commit()
        conn.close()

    def get_maintenance_mode(self) -> Dict[str, Any]:
        """Получает статус режима тех.работ"""
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("bot_settings").select("key, value").in_("key", ["maintenance_enabled", "maintenance_until"]).execute()
                settings = {row["key"]: row["value"] for row in result.data} if result.data else {}
                return {
                    "enabled": settings.get("maintenance_enabled", "0") == "1",
                    "until_time": settings.get("maintenance_until", None)
                }
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в get_maintenance_mode: {e}")
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM bot_settings WHERE key IN ('maintenance_enabled', 'maintenance_until')")
        rows = cursor.fetchall()
        settings = {row["key"]: row["value"] for row in rows}
        conn.close()
        return {
            "enabled": settings.get("maintenance_enabled", "0") == "1",
            "until_time": settings.get("maintenance_until", None)
        }

    def get_all_users_for_notification(self) -> List[str]:
        """Получает список всех user_id для рассылки уведомлений (с кэшем)"""
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("users").select("user_id").execute()
                user_ids = [row["user_id"] for row in result.data] if result.data else []
                # Кэшируем
                for uid in user_ids:
                    if uid not in _user_cache:
                        _user_cache[uid] = {"user_id": uid}
                return user_ids
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в get_all_users_for_notification: {e}")
                # Возвращаем из кэша
                return list(_user_cache.keys())
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        user_ids = [row["user_id"] for row in cursor.fetchall()]
        conn.close()
        return user_ids

    def check_generation_limit(self, user_id: str) -> Dict[str, Any]:
        """Проверяет лимит генерации для пользователя"""
        if USE_SUPABASE and supabase:
            try:
                # Получаем уровень доступа и лимиты
                user_result = supabase.table("users").select("access_level").eq("user_id", user_id).execute()
                if not user_result.data:
                    self.add_or_update_user(user_id)
                    return {
                        "allowed": True,
                        "daily_count": 0,
                        "daily_limit": 3,
                        "total_count": 0,
                        "reset_time": "сегодня",
                        "access_level": "user"
                    }
                
                access_level = user_result.data[0].get("access_level", "user")
                
                limits_result = supabase.table("generation_limits").select("*").eq("user_id", user_id).execute()
                if not limits_result.data:
                    return {
                        "allowed": True,
                        "daily_count": 0,
                        "daily_limit": ACCESS_LEVELS.get(access_level, {}).get("daily_limit", 3),
                        "total_count": 0,
                        "reset_time": "сегодня",
                        "access_level": access_level
                    }
                
                limit_row = limits_result.data[0]
                daily_count = limit_row.get("daily_count", 0)
                daily_limit = ACCESS_LEVELS.get(access_level, {}).get("daily_limit", 3)
                
                # Проверяем нужно ли сбросить счетчик
                today = datetime.now().date()
                last_reset_str = limit_row.get("last_reset", str(today))
                last_reset_date = datetime.strptime(last_reset_str, "%Y-%m-%d").date() if last_reset_str else today
                
                if last_reset_date < today:
                    self._reset_daily_limit(user_id)
                    daily_count = 0
                
                allowed = daily_limit == -1 or daily_count < daily_limit
                
                return {
                    "allowed": allowed,
                    "daily_count": daily_count,
                    "daily_limit": daily_limit,
                    "total_count": limit_row.get("total_count", 0),
                    "reset_time": "сегодня в 00:00",
                    "access_level": access_level
                }
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в check_generation_limit: {e}")
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.access_level, g.daily_count, g.last_reset, g.total_count
            FROM users u
            JOIN generation_limits g ON u.user_id = g.user_id
            WHERE u.user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
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
        daily_limit = ACCESS_LEVELS.get(access_level, {}).get("daily_limit", 3)

        today = datetime.now().date()
        last_reset_date = datetime.strptime(last_reset, "%Y-%m-%d").date() if last_reset else today

        if last_reset_date < today:
            self._reset_daily_limit(user_id)
            daily_count = 0

        allowed = daily_limit == -1 or daily_count < daily_limit

        return {
            "allowed": allowed,
            "daily_count": daily_count,
            "daily_limit": daily_limit,
            "total_count": total_count,
            "reset_time": "сегодня в 00:00",
            "access_level": access_level
        }

    def _reset_daily_limit(self, user_id: str):
        """Сбрасывает дневной счетчик"""
        if USE_SUPABASE and supabase:
            try:
                supabase.table("generation_limits").update({
                    "daily_count": 0,
                    "last_reset": datetime.now().date().isoformat()
                }).eq("user_id", user_id).execute()
                return
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в _reset_daily_limit: {e}")
        
        # SQLite версия
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
        if USE_SUPABASE and supabase:
            try:
                # Увеличиваем счетчики
                supabase.table("generation_limits").update("""
                    daily_count = daily_count + 1,
                    total_count = total_count + 1,
                    last_reset = CURRENT_DATE
                """).eq("user_id", user_id).execute()
                
                # Добавляем запись в историю
                if prompt:
                    supabase.table("generation_history").insert({
                        "user_id": user_id,
                        "prompt": prompt
                    }).execute()
                return
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в increment_generation_count: {e}")
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE generation_limits
            SET daily_count = daily_count + 1,
                total_count = total_count + 1,
                last_reset = CURRENT_DATE
            WHERE user_id = ?
        """, (user_id,))

        if prompt:
            cursor.execute("""
                INSERT INTO generation_history (user_id, prompt)
                VALUES (?, ?)
            """, (user_id, prompt))

        conn.commit()
        conn.close()

    def get_all_users_count(self) -> int:
        """Получает общее количество пользователей"""
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("users").select("user_id", count="exact").execute()
                return result.count
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в get_all_users_count: {e}")
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()["count"]
        conn.close()
        return count

    def get_all_users(self) -> list:
        """Получает всех пользователей"""
        if USE_SUPABASE and supabase:
            try:
                user_result = supabase.table("users").select("*").execute()
                users = user_result.data if user_result.data else []
                
                # Добавляем лимиты
                limits_result = supabase.table("generation_limits").select("*").execute()
                limits_map = {row["user_id"]: row for row in limits_result.data} if limits_result.data else {}
                
                for user in users:
                    limit = limits_map.get(user["user_id"], {})
                    user["daily_count"] = limit.get("daily_count", 0)
                    user["total_count"] = limit.get("total_count", 0)
                    user["last_reset"] = limit.get("last_reset", "")
                
                return users
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в get_all_users: {e}")
        
        # SQLite версия
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
        """Проверяет является ли пользователь администратором (с кэшем)"""
        return self.get_user_access_level(user_id) == "admin"

    def remove_user(self, user_id: str) -> bool:
        """Удаляет пользователя из базы данных"""
        if USE_SUPABASE and supabase:
            try:
                # Удаляем из generation_limits
                supabase.table("generation_limits").delete().eq("user_id", user_id).execute()
                # Удаляем из generation_history
                supabase.table("generation_history").delete().eq("user_id", user_id).execute()
                # Удаляем из users
                supabase.table("users").delete().eq("user_id", user_id).execute()
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в remove_user: {e}")
                return False
        
        # SQLite версия
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM generation_limits WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM generation_history WHERE user_id = ?", (user_id,))
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
