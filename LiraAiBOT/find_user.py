"""
Скрипт для поиска пользователя по username
"""
import os
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

USERNAME = "evgrafovvl"

print(f"🔍 Поиск пользователя @{USERNAME}...")

try:
    result = supabase.table("users").select("*").eq("username", USERNAME).execute()
    
    if result.data and len(result.data) > 0:
        user = result.data[0]
        print(f"\n✅ Пользователь найден:")
        print(f"   ID: {user['user_id']}")
        print(f"   Username: @{user.get('username', 'N/A')}")
        print(f"   Имя: {user.get('first_name', 'N/A')} {user.get('last_name', 'N/A')}")
        print(f"   Уровень: {user.get('access_level', 'user')}")
        print(f"   В боте с: {user.get('created_at', 'N/A')}")
    else:
        print(f"❌ Пользователь @{USERNAME} не найден!")
        
        # Покажем всех пользователей
        print("\n📋 Все пользователи:")
        all_users = supabase.table("users").select("user_id, username, access_level").execute()
        for u in all_users.data:
            print(f"   {u['user_id']}: @{u.get('username', 'N/A')} - {u.get('access_level', 'user')}")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
