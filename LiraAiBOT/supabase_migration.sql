-- ============================================
-- LiraAI Bot - Supabase Database Schema
-- ============================================

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    access_level TEXT DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица лимитов генерации изображений
CREATE TABLE IF NOT EXISTS generation_limits (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    daily_count INTEGER DEFAULT 0,
    last_reset DATE DEFAULT CURRENT_DATE,
    total_count INTEGER DEFAULT 0
);

-- Таблица истории генераций
CREATE TABLE IF NOT EXISTS generation_history (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    prompt TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица уровней доступа (квоты)
CREATE TABLE IF NOT EXISTS access_quotas (
    level_name TEXT PRIMARY KEY,
    daily_limit INTEGER NOT NULL,
    description TEXT
);

-- Таблица настроек бота
CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_access_level ON users(access_level);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_generation_history_user_id ON generation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_history_created_at ON generation_history(created_at);

-- Заполняем уровни доступа
INSERT INTO access_quotas (level_name, daily_limit, description) VALUES
    ('admin', -1, 'Администратор (безлимит)'),
    ('subscriber', 5, 'Подписчик (5 в день)'),
    ('user', 3, 'Пользователь (3 в день)')
ON CONFLICT (level_name) DO NOTHING;

-- RLS (Row Level Security) - отключаем для простоты
-- Включи если нужна дополнительная безопасность
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE generation_limits DISABLE ROW LEVEL SECURITY;
ALTER TABLE generation_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE access_quotas DISABLE ROW LEVEL SECURITY;
ALTER TABLE bot_settings DISABLE ROW LEVEL SECURITY;

-- ============================================
-- Инструкции:
-- 1. Зайди в Supabase Dashboard -> SQL Editor
-- 2. Вставь этот SQL и нажми "Run"
-- 3. Получи anon key в Settings -> API
-- 4. Добавь SUPABASE_KEY в .env
-- ============================================
