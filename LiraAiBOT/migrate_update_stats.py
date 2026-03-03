"""
Миграция: Обновление статистики генераций для всех пользователей

Считает количество генераций за сегодня из generation_history
и обновляет generation_limits
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Загружаем .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL или SUPABASE_KEY не настроены!")
    exit(1)

# Создаём клиент
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print(f"✅ Подключено к Supabase: {SUPABASE_URL}")

# Получаем всех пользователей
print("\n📊 Получаем список всех пользователей...")
users_result = supabase.table("users").select("user_id, access_level").execute()

if not users_result.data:
    print("❌ Пользователи не найдены!")
    exit(1)

users = users_result.data
print(f"✅ Найдено пользователей: {len(users)}")

today = datetime.now().date().isoformat()
updated_count = 0
error_count = 0

# Квоты по уровням доступа
ACCESS_LEVELS = {
    "admin": -1,
    "subscriber": 5,
    "user": 3
}

print(f"\n🔄 Обновляем статистику за {today}...")
print("=" * 60)

for user in users:
    user_id = user["user_id"]
    access_level = user.get("access_level", "user")
    daily_limit = ACCESS_LEVELS.get(access_level, 3)
    
    try:
        # Считаем генерации за сегодня из истории
        history_result = supabase.table("generation_history").select("id", count="exact").eq("user_id", user_id).gte("created_at", today).execute()
        daily_count = history_result.count if hasattr(history_result, 'count') else 0
        
        # Считаем всего генераций
        total_result = supabase.table("generation_history").select("id", count="exact").eq("user_id", user_id).execute()
        total_count = total_result.count if hasattr(total_result, 'count') else 0
        
        # Проверяем есть ли запись в generation_limits
        limits_result = supabase.table("generation_limits").select("user_id").eq("user_id", user_id).execute()
        
        if not limits_result.data or len(limits_result.data) == 0:
            # Создаём запись
            supabase.table("generation_limits").insert({
                "user_id": user_id,
                "daily_count": daily_count,
                "total_count": total_count,
                "last_reset": today
            }).execute()
            print(f"✅ {user_id}: Создана запись (daily={daily_count}, total={total_count})")
        else:
            # Обновляем запись
            supabase.table("generation_limits").update({
                "daily_count": daily_count,
                "total_count": total_count,
                "last_reset": today
            }).eq("user_id", user_id).execute()
            print(f"✅ {user_id}: Обновлено (daily={daily_count}, total={total_count}, limit={daily_limit})")
        
        updated_count += 1
        
    except Exception as e:
        print(f"❌ {user_id}: Ошибка - {e}")
        error_count += 1

print("=" * 60)
print(f"\n📊 Итоги миграции:")
print(f"  ✅ Обновлено пользователей: {updated_count}")
print(f"  ❌ Ошибок: {error_count}")
print(f"  📅 Дата сброса: {today}")
print("\n✅ Миграция завершена!")
