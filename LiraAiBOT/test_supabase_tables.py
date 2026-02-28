#!/usr/bin/env python3
"""Проверка таблиц Supabase перед запуском"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Подключение к Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

print("🔍 Проверка таблиц Supabase...\n")

# Проверяем users
try:
    result = supabase.table("users").select("user_id").eq("user_id", "1658547011").execute()
    print(f"✅ Таблица users: {len(result.data)} пользователей")
except Exception as e:
    print(f"❌ Таблица users: {e}")

# Проверяем dialog_history
try:
    result = supabase.table("dialog_history").select("id").limit(1).execute()
    print(f"✅ Таблица dialog_history: существует")
except Exception as e:
    print(f"❌ Таблица dialog_history: НЕ СУЩЕСТВУЕТ")
    print(f"   Нужно выполнить миграцию!")

print("\n" + "="*50)
print("📝 ИНСТРУКЦИЯ ПО СОЗДАНИЮ dialog_history:")
print("="*50)
print("""
1. Зайди в https://supabase.com/dashboard/project/xmdvjrgpqqdoofamkzut/sql/new

2. Вставь SQL из файла: supabase_memory_migration.sql

3. Или выполни этот SQL:

CREATE TABLE IF NOT EXISTS dialog_history (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    model TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_count INTEGER DEFAULT 0,
    feedback_score INTEGER DEFAULT 0
);

CREATE INDEX idx_dialog_history_user_id ON dialog_history(user_id);
CREATE INDEX idx_dialog_history_created_at ON dialog_history(created_at);
""")
