"""
Скрипт для миграции данных из SQLite в Supabase.
"""
import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем .env
load_dotenv()

# Пути
DB_PATH = Path(__file__).parent / "data" / "bot.db"

# Supabase клиент
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL или SUPABASE_KEY не настроены в .env")
    exit(1)

# Инициализируем клиент
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase клиент инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации Supabase: {e}")
    exit(1)


def get_sqlite_connection():
    """Получает соединение с SQLite"""
    if not DB_PATH.exists():
        print(f"❌ База данных не найдена: {DB_PATH}")
        return None
    return sqlite3.connect(str(DB_PATH))


def migrate_users():
    """Мигрирует таблицу users"""
    print("\n📦 Миграция таблицы users...")
    
    conn = get_sqlite_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, last_name, access_level, created_at, last_seen FROM users")
    users = cursor.fetchall()
    conn.close()
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            data = {
                "user_id": user[0],
                "username": user[1],
                "first_name": user[2],
                "last_name": user[3],
                "access_level": user[4],
                "created_at": user[5],
                "last_seen": user[6]
            }
            
            # Вставляем или обновляем
            supabase.table("users").upsert(data).execute()
            success += 1
            print(f"  ✅ {user[0]} ({user[2]} {user[3] or ''})")
        except Exception as e:
            print(f"  ❌ Ошибка для {user[0]}: {e}")
            failed += 1
    
    print(f"✅ Users: {success} успешно, {failed} ошибок")
    return success


def migrate_generation_limits():
    """Мигрирует таблицу generation_limits"""
    print("\n📦 Миграция таблицы generation_limits...")
    
    conn = get_sqlite_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, daily_count, last_reset, total_count FROM generation_limits")
    limits = cursor.fetchall()
    conn.close()
    
    success = 0
    failed = 0
    
    for limit in limits:
        try:
            data = {
                "user_id": limit[0],
                "daily_count": limit[1],
                "last_reset": limit[2],
                "total_count": limit[3]
            }
            
            supabase.table("generation_limits").upsert(data).execute()
            success += 1
        except Exception as e:
            print(f"  ❌ Ошибка для {limit[0]}: {e}")
            failed += 1
    
    print(f"✅ Generation Limits: {success} успешно, {failed} ошибок")
    return success


def migrate_generation_history():
    """Мигрирует таблицу generation_history"""
    print("\n📦 Миграция таблицы generation_history...")
    
    conn = get_sqlite_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, prompt, created_at FROM generation_history")
    history = cursor.fetchall()
    conn.close()
    
    success = 0
    failed = 0
    
    for record in history:
        try:
            data = {
                "id": record[0],
                "user_id": record[1],
                "prompt": record[2],
                "created_at": record[3]
            }
            
            # Проверяем существует ли запись
            existing = supabase.table("generation_history").select("id").eq("id", data["id"]).execute()
            
            if existing.data:
                # Обновляем
                supabase.table("generation_history").update(data).eq("id", data["id"]).execute()
            else:
                # Вставляем
                supabase.table("generation_history").insert(data).execute()
            
            success += 1
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            failed += 1
    
    print(f"✅ Generation History: {success} успешно, {failed} ошибок")
    return success


def migrate_bot_settings():
    """Мигрирует таблицу bot_settings"""
    print("\n📦 Миграция таблицы bot_settings...")
    
    conn = get_sqlite_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM bot_settings")
    settings = cursor.fetchall()
    conn.close()
    
    success = 0
    failed = 0
    
    for setting in settings:
        try:
            data = {
                "key": setting[0],
                "value": setting[1]
            }
            
            supabase.table("bot_settings").upsert(data).execute()
            success += 1
        except Exception as e:
            print(f"  ❌ Ошибка для {setting[0]}: {e}")
            failed += 1
    
    print(f"✅ Bot Settings: {success} успешно, {failed} ошибок")
    return success


def verify_migration():
    """Проверяет миграцию"""
    print("\n🔍 Проверка миграции...")
    
    try:
        # Считаем пользователей в Supabase
        result = supabase.table("users").select("user_id", count="exact").execute()
        supabase_count = result.count
        
        # Считаем в SQLite
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        sqlite_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"  SQLite пользователей: {sqlite_count}")
        print(f"  Supabase пользователей: {supabase_count}")
        
        if supabase_count == sqlite_count:
            print("✅ Миграция успешна!")
        else:
            print(f"⚠️ Расхождение: {sqlite_count} vs {supabase_count}")
        
        return supabase_count == sqlite_count
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False


def main():
    """Основная функция"""
    print("🚀 LiraAI Bot - Миграция SQLite → Supabase\n")
    print(f"SQLite: {DB_PATH}")
    print(f"Supabase: {SUPABASE_URL}\n")
    
    # Мигрируем таблицы
    migrate_users()
    migrate_generation_limits()
    migrate_generation_history()
    migrate_bot_settings()
    
    # Проверяем
    verify_migration()
    
    print("\n" + "=" * 50)
    print("✅ Миграция завершена!")
    print("=" * 50)
    print("\n📝 Следующие шаги:")
    print("1. Проверь SUPABASE_KEY в .env (anon/public key)")
    print("2. Установи USE_SUPABASE=true в .env")
    print("3. Установи пакет: pip install supabase")
    print("4. Перезапусти бота")


if __name__ == "__main__":
    main()
