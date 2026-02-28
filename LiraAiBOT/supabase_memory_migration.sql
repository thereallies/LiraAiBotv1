-- ============================================
-- LiraAI Bot - Долговременная память
-- ============================================

-- Таблица истории сообщений (долговременная память)
CREATE TABLE IF NOT EXISTS dialog_history (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_count INTEGER DEFAULT 0,
    feedback_score INTEGER CHECK (feedback_score IN (-1, 0, 1)) DEFAULT 0
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_dialog_history_user_id ON dialog_history(user_id);
CREATE INDEX IF NOT EXISTS idx_dialog_history_created_at ON dialog_history(created_at);
CREATE INDEX IF NOT EXISTS idx_dialog_history_user_created ON dialog_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dialog_history_feedback ON dialog_history(feedback_score) WHERE feedback_score != 0;

-- Таблица для feedback (оценки ответов)
CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    message_id BIGINT REFERENCES dialog_history(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score IN (-1, 1)),  -- -1 = 👎, 1 = 👍
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для feedback
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_message_id ON feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_feedback_score ON feedback(score);

-- RLS (Row Level Security) - отключаем для простоты
ALTER TABLE dialog_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE feedback DISABLE ROW LEVEL SECURITY;

-- ============================================
-- Функции для очистки старой истории

-- Функция: Удалить сообщения старше N дней
CREATE OR REPLACE FUNCTION cleanup_old_dialogs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM dialog_history
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Функция: Получить статистику по истории пользователя
CREATE OR REPLACE FUNCTION get_user_dialog_stats(target_user_id TEXT)
RETURNS TABLE (
    total_messages BIGINT,
    user_messages BIGINT,
    assistant_messages BIGINT,
    first_message_date TIMESTAMP,
    last_message_date TIMESTAMP,
    avg_message_length DOUBLE PRECISION,
    positive_feedback BIGINT,
    negative_feedback BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_messages,
        COUNT(*) FILTER (WHERE role = 'user')::BIGINT as user_messages,
        COUNT(*) FILTER (WHERE role = 'assistant')::BIGINT as assistant_messages,
        MIN(created_at) as first_message_date,
        MAX(created_at) as last_message_date,
        AVG(LENGTH(content))::DOUBLE PRECISION as avg_message_length,
        COUNT(*) FILTER (WHERE feedback_score = 1)::BIGINT as positive_feedback,
        COUNT(*) FILTER (WHERE feedback_score = -1)::BIGINT as negative_feedback
    FROM dialog_history
    WHERE user_id = target_user_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Инструкции:
-- 1. Зайди в Supabase Dashboard -> SQL Editor
-- 2. Вставь этот SQL и нажми "Run"
-- 3. Проверь что таблицы созданы
