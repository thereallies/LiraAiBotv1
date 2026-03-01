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


# ============================================
# Функции управления кэшем
# ============================================

def _get_from_cache(cache: Dict, timestamps: Dict, key: str, default=None):
    """Получает значение из кэша с проверкой TTL"""
    import time
    if key in cache:
        if key in timestamps and (time.time() - timestamps[key]) < CACHE_TTL:
            return cache[key]
        else:
            # Истекло TTL - удаляем
            del cache[key]
            if key in timestamps:
                del timestamps[key]
    return default


def _save_to_cache(cache: Dict, timestamps: Dict, key: str, value):
    """Сохраняет значение в кэш с timestamp"""
    import time
    cache[key] = value
    timestamps[key] = time.time()


def _invalidate_cache(cache: Dict, timestamps: Dict, key: str = None):
    """Инвалидирует кэш (полностью или по ключу)"""
    if key:
        if key in cache:
            del cache[key]
        if key in timestamps:
            del timestamps[key]
    else:
        cache.clear()
        timestamps.clear()


def invalidate_user_cache(user_id: str = None):
    """Инвалидирует кэш пользователя"""
    _invalidate_cache(_user_cache, _user_cache_timestamps, user_id)
    _invalidate_cache(_limits_cache, _limits_cache_timestamps, user_id)
    logger.info(f"🗑️ Кэш {'пользователя ' + user_id if user_id else 'полностью'} очищен")


# ============================================
# Кэш настроек бота (тех.режим и т.д.)
# ============================================
_user_cache: Dict[str, Dict] = {}
_user_cache_timestamps: Dict[str, float] = {}
_limits_cache: Dict[str, Dict] = {}
_limits_cache_timestamps: Dict[str, float] = {}

# TTL для кэша (5 минут)
CACHE_TTL = 300  # секунд

# Кэш настроек бота (тех.режим и т.д.)
_bot_settings_cache: Dict[str, Any] = {
    "maintenance_enabled": False,
    "maintenance_until": None
}

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
                "access_level": "user"  # По умолчанию user
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
                # Проверяем существует ли пользователь
                result = supabase.table("users").select("user_id, username, first_name, last_name, access_level").eq("user_id", user_id).execute()
                
                if result.data:
                    # Обновляем ТОЛЬКО изменённые поля (не затираем existing data)
                    update_data = {"last_seen": datetime.now().isoformat()}
                    if username:
                        update_data["username"] = username
                    if first_name:
                        update_data["first_name"] = first_name
                    if last_name:
                        update_data["last_name"] = last_name
                    
                    supabase.table("users").update(update_data).eq("user_id", user_id).execute()
                    # Обновляем кэш access_level
                    _user_cache[user_id]["access_level"] = result.data[0].get("access_level", "user")
                else:
                    # Создаём нового пользователя
                    data = {
                        "user_id": user_id,
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                        "access_level": "user",
                        "last_seen": datetime.now().isoformat()
                    }
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
        """Устанавливает уровень доступа пользователя (с кэшем)"""
        if level not in ACCESS_LEVELS:
            return False
        
        # Сразу обновляем кэш!
        if user_id not in _user_cache:
            _user_cache[user_id] = {"user_id": user_id, "access_level": level}
        else:
            _user_cache[user_id]["access_level"] = level
        
        # Если используем Supabase
        if USE_SUPABASE and supabase:
            try:
                # Сначала получаем текущие данные пользователя
                result = supabase.table("users").select("username, first_name, last_name").eq("user_id", user_id).execute()
                
                if result.data:
                    # Обновляем ТОЛЬКО access_level, сохраняя остальные поля
                    update_data = {"access_level": level}
                    supabase.table("users").update(update_data).eq("user_id", user_id).execute()
                else:
                    # Пользователя нет - создаём
                    supabase.table("users").insert({
                        "user_id": user_id,
                        "access_level": level
                    }).execute()
                
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в set_user_access_level: {e}")
                return False
        
        # SQLite только для локальной разработки
        if not USE_SUPABASE:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET access_level = ? WHERE user_id = ?", (level, user_id))
            conn.commit()
            conn.close()
            return True
        
        return False

    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получает статистику пользователя (с кэшированием)"""
        # Проверяем кэш с TTL
        cached = _get_from_cache(_user_cache, _user_cache_timestamps, f"stats_{user_id}")
        if cached:
            logger.debug(f"🗄️ Статистика {user_id} из кэша")
            return cached
        
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

                stats = {
                    "user_id": user_row.get("user_id"),
                    "username": user_row.get("username"),
                    "first_name": user_row.get("first_name"),
                    "last_name": user_row.get("last_name"),
                    "access_level": user_row.get("access_level"),
                    "created_at": user_row.get("created_at"),
                    "last_seen": user_row.get("last_seen"),
                    "daily_count": limit_row.get("daily_count", 0) if limit_row else 0,
                    "total_count": limit_row.get("total_count", 0) if limit_row else 0,
                    "today_generations": history_result.count if hasattr(history_result, 'count') else 0
                }
                
                # Кэшируем с TTL
                _save_to_cache(_user_cache, _user_cache_timestamps, f"stats_{user_id}", stats)
                return stats
            except Exception as e:
                logger.error(f"❌ Ошибка Supabase в get_user_stats: {e}")
                return None
        
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
        global _bot_settings_cache
        
        # Сразу обновляем кэш!
        _bot_settings_cache["maintenance_enabled"] = enabled
        _bot_settings_cache["maintenance_until"] = until_time
        
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
                # Кэш уже обновлён, тех.режим работает в памяти
        
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
        """Получает статус режима тех.работ (с кэшем)"""
        global _bot_settings_cache
        
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("bot_settings").select("key, value").in_("key", ["maintenance_enabled", "maintenance_until"]).execute()
                settings = {row["key"]: row["value"] for row in result.data} if result.data else {}
                
                # Обновляем кэш
                _bot_settings_cache["maintenance_enabled"] = settings.get("maintenance_enabled", "0") == "1"
                _bot_settings_cache["maintenance_until"] = settings.get("maintenance_until", None)
                
                return {
                    "enabled": _bot_settings_cache["maintenance_enabled"],
                    "until_time": _bot_settings_cache["maintenance_until"]
                }
            except Exception as e:
                logger.warning(f"⚠️ Supabase недоступен, используем кэш тех.режима: {e}")
                # Возвращаем кэш (тех.режим всё равно работает!)
                return {
                    "enabled": _bot_settings_cache.get("maintenance_enabled", False),
                    "until_time": _bot_settings_cache.get("maintenance_until", None)
                }
        
        # SQLite версия (создаём таблицу если нет)
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM bot_settings WHERE key IN ('maintenance_enabled', 'maintenance_until')")
            rows = cursor.fetchall()
            settings = {row["key"]: row["value"] for row in rows}
            conn.close()
            
            # Обновляем кэш
            _bot_settings_cache["maintenance_enabled"] = settings.get("maintenance_enabled", "0") == "1"
            _bot_settings_cache["maintenance_until"] = settings.get("maintenance_until", None)
            
            return {
                "enabled": _bot_settings_cache["maintenance_enabled"],
                "until_time": _bot_settings_cache["maintenance_until"]
            }
        except sqlite3.OperationalError:
            # Таблицы нет - возвращаем кэш
            return {
                "enabled": _bot_settings_cache.get("maintenance_enabled", False),
                "until_time": _bot_settings_cache.get("maintenance_until", None)
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
                
                # Инвалидируем кэш
                invalidate_user_cache(user_id)
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
        
        # Инвалидируем кэш
        invalidate_user_cache(user_id)

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
        # Проверяем кэш сначала
        if user_id in _user_cache:
            return _user_cache[user_id].get("access_level", "user") == "admin"
        
        # Если нет в кэше - проверяем через Supabase
        level = self.get_user_access_level(user_id)
        return level == "admin"

    # =========================================
    # Долговременная память (диалоги)
    # =========================================

    def save_dialog_message(
        self,
        user_id: str,
        role: str,
        content: str,
        model: str = None,
        tokens_count: int = 0
    ):
        """
        Сохраняет сообщение в историю диалога (асинхронно, не блокирует)
        
        Args:
            user_id: ID пользователя
            role: 'user', 'assistant', или 'system'
            content: Текст сообщения
            model: Название модели
            tokens_count: Количество токенов
        """
        if USE_SUPABASE and supabase:
            try:
                data = {
                    "user_id": user_id,
                    "role": role,
                    "content": content,
                    "model": model,
                    "tokens_count": tokens_count
                }
                
                # Вставляем в фоне (не ждём ответа)
                supabase.table("dialog_history").insert(data).execute()
            except Exception as e:
                logger.warning(f"⚠️ Не удалось сохранить сообщение в историю: {e}")
        else:
            # SQLite fallback
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO dialog_history (user_id, role, content, model, tokens_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, role, content, model, tokens_count))
                conn.commit()
                conn.close()
            except sqlite3.OperationalError:
                # Таблицы нет - игнорируем
                pass

    def get_dialog_history(
        self,
        user_id: str,
        limit: int = 20,
        before_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Получает историю диалога пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество сообщений (по умолчанию 20)
            before_date: Получить сообщения до указанной даты (ISO format)
        
        Returns:
            Список сообщений в формате [{"role": "...", "content": "..."}, ...]
        """
        if USE_SUPABASE and supabase:
            try:
                query = supabase.table("dialog_history").select(
                    "role, content, model, created_at"
                ).eq("user_id", user_id)
                
                if before_date:
                    query = query.lt("created_at", before_date)
                
                query = query.order("created_at", desc=True).limit(limit)
                result = query.execute()
                
                # Возвращаем в правильном порядке (от старых к новым)
                messages = result.data if result.data else []
                return list(reversed(messages))
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить историю диалога: {e}")
                return []
        else:
            # SQLite fallback
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                if before_date:
                    cursor.execute("""
                        SELECT role, content, model, created_at
                        FROM dialog_history
                        WHERE user_id = ? AND created_at < ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (user_id, before_date, limit))
                else:
                    cursor.execute("""
                        SELECT role, content, model, created_at
                        FROM dialog_history
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """, (user_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [
                    {"role": row[0], "content": row[1], "model": row[2], "created_at": row[3]}
                    for row in rows
                ][::-1]  # Reverse to get oldest first
            except sqlite3.OperationalError:
                return []

    def clear_dialog_history(self, user_id: str) -> bool:
        """
        Очищает всю историю диалога пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            True если успешно
        """
        if USE_SUPABASE and supabase:
            try:
                supabase.table("dialog_history").delete().eq("user_id", user_id).execute()
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка очистки истории: {e}")
                return False
        else:
            # SQLite fallback
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM dialog_history WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                return True
            except sqlite3.OperationalError:
                return False

    def get_user_dialog_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Получает статистику по истории диалога пользователя
        """
        if USE_SUPABASE and supabase:
            try:
                # Загружаем все сообщения и считаем
                all_messages = supabase.table("dialog_history").select(
                    "role, created_at, feedback_score"
                ).eq("user_id", user_id).execute()
                
                messages = all_messages.data if all_messages.data else []
                
                # Считаем статистику
                total = len(messages)
                user_msgs = sum(1 for m in messages if m.get("role") == "user")
                assistant_msgs = sum(1 for m in messages if m.get("role") == "assistant")
                positive = sum(1 for m in messages if m.get("feedback_score") == 1)
                negative = sum(1 for m in messages if m.get("feedback_score") == -1)
                
                # Первое и последнее
                first_msg = messages[0]["created_at"] if messages else None
                last_msg = messages[-1]["created_at"] if messages else None
                
                return {
                    "total_messages": total,
                    "user_messages": user_msgs,
                    "assistant_messages": assistant_msgs,
                    "first_message": first_msg,
                    "last_message": last_msg,
                    "positive_feedback": positive,
                    "negative_feedback": negative
                }
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить статистику диалога: {e}")
                return {}
        else:
            # SQLite fallback
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE role = 'user') as user_msgs,
                        COUNT(*) FILTER (WHERE role = 'assistant') as assistant_msgs,
                        MIN(created_at) as first_msg,
                        MAX(created_at) as last_msg,
                        COUNT(*) FILTER (WHERE feedback_score = 1) as positive,
                        COUNT(*) FILTER (WHERE feedback_score = -1) as negative
                    FROM dialog_history
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        "total_messages": row[0] or 0,
                        "user_messages": row[1] or 0,
                        "assistant_messages": row[2] or 0,
                        "first_message": row[3],
                        "last_message": row[4],
                        "positive_feedback": row[5] or 0,
                        "negative_feedback": row[6] or 0
                    }
                return {}
            except sqlite3.OperationalError:
                return {}

    def get_admin_dialog_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Получает историю диалога для админа (с подробной информацией)
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество сообщений
        
        Returns:
            Список сообщений с полной информацией
        """
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("dialog_history").select(
                    "id, role, content, model, created_at, tokens_count, feedback_score"
                ).eq("user_id", user_id).order(
                    "created_at", desc=True
                ).limit(limit).execute()
                
                messages = result.data if result.data else []
                return list(reversed(messages))
            except Exception as e:
                logger.error(f"❌ Ошибка получения истории для админа: {e}")
                return []
        else:
            # SQLite fallback
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, role, content, model, created_at, tokens_count, feedback_score
                    FROM dialog_history
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [
                    {
                        "id": row[0],
                        "role": row[1],
                        "content": row[2],
                        "model": row[3],
                        "created_at": row[4],
                        "tokens_count": row[5],
                        "feedback_score": row[6]
                    }
                    for row in rows
                ][::-1]
            except sqlite3.OperationalError:
                return []

    def cleanup_old_dialogs(self, days_to_keep: int = 30) -> int:
        """
        Удаляет старые сообщения из истории
        
        Args:
            days_to_keep: Хранить сообщения за последние N дней
        
        Returns:
            Количество удалённых сообщений
        """
        if USE_SUPABASE and supabase:
            try:
                # Supabase не поддерживает хранимые процедуры напрямую
                # Удаляем через фильтр
                from datetime import datetime, timedelta
                
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                # Получаем ID сообщений для удаления
                old_messages = supabase.table("dialog_history").select("id").lt(
                    "created_at", cutoff_date.isoformat()
                ).execute()
                
                deleted_count = len(old_messages.data) if old_messages.data else 0
                
                if deleted_count > 0:
                    supabase.table("dialog_history").delete().lt(
                        "created_at", cutoff_date.isoformat()
                    ).execute()
                
                logger.info(f"🗑️ Удалено {deleted_count} старых сообщений")
                return deleted_count
            except Exception as e:
                logger.error(f"❌ Ошибка очистки старых сообщений: {e}")
                return 0
        else:
            # SQLite fallback
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM dialog_history
                    WHERE created_at < datetime('now', ?)
                """, (f'-{days_to_keep} days',))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                logger.info(f"🗑️ Удалено {deleted_count} старых сообщений")
                return deleted_count
            except sqlite3.OperationalError:
                return 0

    def set_message_feedback(
        self,
        message_id: int,
        user_id: str,
        score: int
    ) -> bool:
        """
        Устанавливает оценку сообщению (👍/👎)
        
        Args:
            message_id: ID сообщения в dialog_history
            user_id: ID пользователя
            score: 1 (👍) или -1 (👎)
        
        Returns:
            True если успешно
        """
        if USE_SUPABASE and supabase:
            try:
                # Обновляем оценку в dialog_history
                supabase.table("dialog_history").update({
                    "feedback_score": score
                }).eq("id", message_id).eq("user_id", user_id).execute()
                
                # Также сохраняем в таблицу feedback для статистики
                supabase.table("feedback").insert({
                    "user_id": user_id,
                    "message_id": message_id,
                    "score": score
                }).execute()
                
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка установки оценки: {e}")
                return False
        else:
            # SQLite fallback
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE dialog_history
                    SET feedback_score = ?
                    WHERE id = ? AND user_id = ?
                """, (score, message_id, user_id))
                
                conn.commit()
                conn.close()
                return True
            except sqlite3.OperationalError:
                return False

    # =========================================
    # Настройки пользователя (выбор модели)
    # =========================================

    def get_user_model(self, user_id: str) -> str:
        """
        Получает выбранную модель пользователя из БД
        """
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("user_settings").select("selected_model").eq("user_id", user_id).execute()
                
                if result.data and len(result.data) > 0:
                    model = result.data[0].get("selected_model", "groq-llama")
                    logger.info(f"💾 Загружена модель из БД для {user_id}: {model}")
                    return model
                
                logger.info(f"💾 Нет настроек для {user_id}, используем groq-llama")
                return "groq-llama"
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки модели: {e}")
                return "groq-llama"
        else:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT selected_model FROM user_settings WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    return row[0]
                return "groq-llama"
            except sqlite3.OperationalError:
                return "groq-llama"

    def set_user_model(self, user_id: str, model_key: str) -> bool:
        """
        Сохраняет выбранную модель пользователя в БД
        """
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("user_settings").select("user_id").eq("user_id", user_id).execute()
                
                if result.data and len(result.data) > 0:
                    supabase.table("user_settings").update({
                        "selected_model": model_key,
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user_id).execute()
                else:
                    supabase.table("user_settings").insert({
                        "user_id": user_id,
                        "selected_model": model_key
                    }).execute()
                
                logger.info(f"💾 Сохранена модель для {user_id}: {model_key}")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения модели: {e}")
                return False
        else:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
                exists = cursor.fetchone()
                
                if exists:
                    cursor.execute("""
                        UPDATE user_settings
                        SET selected_model = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (model_key, user_id))
                else:
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, selected_model)
                        VALUES (?, ?)
                    """, (user_id, model_key))
                
                conn.commit()
                conn.close()
                logger.info(f"💾 Сохранена модель для {user_id}: {model_key}")
                return True
            except sqlite3.OperationalError:
                return False

    # =========================================
    # Настройки генерации изображений
    # =========================================

    def get_user_image_model(self, user_id: str) -> Optional[str]:
        """
        Получает выбранную модель генерации изображений из БД
        """
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("user_settings").select("image_model").eq("user_id", user_id).execute()

                if result.data and len(result.data) > 0:
                    model = result.data[0].get("image_model")
                    if model:
                        logger.info(f"💾 Загружена image_model из БД для {user_id}: {model}")
                        return model

                logger.info(f"💾 Нет image_model для {user_id}")
                return None
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки image_model: {e}")
                return None
        else:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT image_model FROM user_settings WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                conn.close()
                if row and row[0]:
                    return row[0]
                return None
            except sqlite3.OperationalError:
                return None

    def set_user_image_model(self, user_id: str, model_key: str) -> bool:
        """
        Сохраняет выбранную модель генерации изображений в БД
        """
        if USE_SUPABASE and supabase:
            try:
                result = supabase.table("user_settings").select("user_id").eq("user_id", user_id).execute()

                if result.data and len(result.data) > 0:
                    supabase.table("user_settings").update({
                        "image_model": model_key,
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user_id).execute()
                else:
                    supabase.table("user_settings").insert({
                        "user_id": user_id,
                        "image_model": model_key,
                        "selected_model": "groq-llama"  # Default text model
                    }).execute()

                logger.info(f"💾 Сохранена image_model для {user_id}: {model_key}")
                
                # Инвалидируем кэш
                invalidate_user_cache(user_id)
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения image_model: {e}")
                return False
        else:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute("SELECT user_id FROM user_settings WHERE user_id = ?", (user_id,))
                exists = cursor.fetchone()

                if exists:
                    cursor.execute("""
                        UPDATE user_settings
                        SET image_model = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (model_key, user_id))
                else:
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, image_model, selected_model)
                        VALUES (?, ?, 'groq-llama')
                    """, (user_id, model_key))

                conn.commit()
                conn.close()
                logger.info(f"💾 Сохранена image_model для {user_id}: {model_key}")
                
                # Инвалидируем кэш
                invalidate_user_cache(user_id)
                return True
            except sqlite3.OperationalError:
                return False

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
