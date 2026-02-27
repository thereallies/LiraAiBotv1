#!/usr/bin/env python3
"""Быстрая миграция пользователей в Supabase"""
import sqlite3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Подключение к Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Подключение к SQLite
conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()

# Получаем всех пользователей из SQLite
cursor.execute("SELECT user_id, username, first_name, last_name, access_level, created_at, last_seen FROM users")
users = cursor.fetchall()
conn.close()

print(f"📦 Найдено {len(users)} пользователей в SQLite\n")

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
        supabase.table("users").upsert(data).execute()
        print(f"  ✅ {user[0]} ({user[2]} {user[3] or ''}) - {user[4]}")
        success += 1
    except Exception as e:
        print(f"  ❌ {user[0]}: {e}")
        failed += 1

print(f"\n✅ Готово: {success} успешно, {failed} ошибок")

# Проверка
result = supabase.table("users").select("user_id", count="exact").execute()
print(f"📊 Всего в Supabase: {result.count}")
