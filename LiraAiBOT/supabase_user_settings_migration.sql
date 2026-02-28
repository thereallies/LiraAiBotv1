-- ============================================
-- LiraAI Bot - Таблица настроек пользователей
-- ============================================

-- Таблица настроек пользователей (выбор модели и т.д.)
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    selected_model TEXT DEFAULT 'groq-llama',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- RLS отключаем для простоты
ALTER TABLE user_settings DISABLE ROW LEVEL SECURITY;

-- ============================================
-- Инструкции:
-- 1. Зайди в Supabase Dashboard -> SQL Editor
-- 2. Вставь этот SQL и нажми "Run"
-- 3. Проверь что таблица создана
