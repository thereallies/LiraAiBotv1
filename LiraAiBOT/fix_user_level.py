"""
Скрипт для обновления уровня доступа пользователя
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
print(f"✅ Подключено к Supabase: {SUPABASE_URL}")

# ID пользователя и новый уровень
USER_ID = "7752488661"  # @evgrafovvl
NEW_LEVEL = "subscriber"

print(f"\n🔄 Обновление пользователя {USER_ID}...")
print(f"   Новый уровень: {NEW_LEVEL}")

try:
    # Обновляем уровень доступа
    result = supabase.table("users").update({
        "access_level": NEW_LEVEL
    }).eq("user_id", USER_ID).execute()
    
    if result.data and len(result.data) > 0:
        print(f"✅ Уровень доступа обновлён!")
        print(f"   {result.data[0]}")
    else:
        print(f"❌ Пользователь не найден!")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n✅ Готово!")
