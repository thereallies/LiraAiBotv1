-- ============================================
-- Таблица аудита действий администраторов
-- ============================================

-- Создаём таблицу для логирования всех действий администраторов
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id BIGSERIAL PRIMARY KEY,
    admin_user_id TEXT NOT NULL,              -- ID администратора
    admin_username TEXT,                       -- Username администратора
    action_type TEXT NOT NULL,                 -- Тип действия
    target_user_id TEXT,                       -- ID целевого пользователя (если есть)
    target_username TEXT,                      -- Username целевого пользователя
    old_value TEXT,                            -- Старое значение (например, старый уровень)
    new_value TEXT,                            -- Новое значение (например, новый уровень)
    details JSONB,                             -- Дополнительные детали (JSON)
    ip_address TEXT,                           -- IP адрес (если доступен)
    chat_id TEXT,                              -- ID чата где выполнено действие
    message_id BIGINT,                         -- ID сообщения с командой
    created_at TIMESTAMPTZ DEFAULT NOW(),      -- Время выполнения
    success BOOLEAN DEFAULT TRUE               -- Успешно ли выполнено
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_admin_audit_admin_id ON admin_audit_log(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_target_id ON admin_audit_log(target_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_action_type ON admin_audit_log(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created_at ON admin_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_success ON admin_audit_log(success);

-- Комментарии к таблице
COMMENT ON TABLE admin_audit_log IS 'Журнал аудита действий администраторов';
COMMENT ON COLUMN admin_audit_log.admin_user_id IS 'ID администратора выполнившего действие';
COMMENT ON COLUMN admin_audit_log.action_type IS 'Тип действия: set_level, remove_level, add_user, remove_user, view_history, etc.';
COMMENT ON COLUMN admin_audit_log.target_user_id IS 'ID пользователя над которым выполнено действие';
COMMENT ON COLUMN admin_audit_log.old_value IS 'Старое значение (уровень доступа, имя и т.д.)';
COMMENT ON COLUMN admin_audit_log.new_value IS 'Новое значение после изменения';
COMMENT ON COLUMN admin_audit_log.details IS 'Дополнительные детали в формате JSON';
COMMENT ON COLUMN admin_audit_log.created_at IS 'Время выполнения действия (MSK)';
COMMENT ON COLUMN admin_audit_log.success IS 'Флаг успешного выполнения действия';

-- ============================================
-- Функция для получения статистики администратора
-- ============================================
CREATE OR REPLACE FUNCTION get_admin_stats(admin_id TEXT)
RETURNS TABLE (
    total_actions BIGINT,
    successful_actions BIGINT,
    failed_actions BIGINT,
    level_changes BIGINT,
    users_added BIGINT,
    users_removed BIGINT,
    history_views BIGINT,
    last_action TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT AS total_actions,
        COUNT(*) FILTER (WHERE success = TRUE)::BIGINT AS successful_actions,
        COUNT(*) FILTER (WHERE success = FALSE)::BIGINT AS failed_actions,
        COUNT(*) FILTER (WHERE action_type IN ('set_level', 'remove_level'))::BIGINT AS level_changes,
        COUNT(*) FILTER (WHERE action_type = 'add_user')::BIGINT AS users_added,
        COUNT(*) FILTER (WHERE action_type = 'remove_user')::BIGINT AS users_removed,
        COUNT(*) FILTER (WHERE action_type = 'view_history')::BIGINT AS history_views,
        MAX(created_at) AS last_action
    FROM admin_audit_log
    WHERE admin_user_id = admin_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Функция для получения последних действий
-- ============================================
CREATE OR REPLACE FUNCTION get_recent_admin_actions(
    p_limit INTEGER DEFAULT 50,
    p_admin_id TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    admin_user_id TEXT,
    admin_username TEXT,
    action_type TEXT,
    target_user_id TEXT,
    target_username TEXT,
    old_value TEXT,
    new_value TEXT,
    details JSONB,
    created_at TIMESTAMPTZ,
    success BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        aal.id,
        aal.admin_user_id,
        aal.admin_username,
        aal.action_type,
        aal.target_user_id,
        aal.target_username,
        aal.old_value,
        aal.new_value,
        aal.details,
        aal.created_at,
        aal.success
    FROM admin_audit_log aal
    WHERE (p_admin_id IS NULL OR aal.admin_user_id = p_admin_id)
    ORDER BY aal.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- RLS (Row Level Security) - опционально
-- ============================================
-- Включаем RLS если нужна дополнительная безопасность
-- ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;

-- Политика: только админы могут читать логи
-- CREATE POLICY admin_read_audit ON admin_audit_log
--     FOR SELECT
--     USING (EXISTS (
--         SELECT 1 FROM users 
--         WHERE users.user_id = admin_audit_log.admin_user_id 
--         AND users.access_level = 'admin'
--     ));

-- ============================================
-- Примеры вставки данных (для тестирования)
-- ============================================
-- INSERT INTO admin_audit_log (admin_user_id, admin_username, action_type, target_user_id, old_value, new_value, details)
-- VALUES 
--     ('123456789', 'admin_user', 'set_level', '987654321', 'user', 'subscriber', '{"chat_id": "-1001234567890"}'),
--     ('123456789', 'admin_user', 'add_user', '111222333', NULL, NULL, '{"chat_id": "-1001234567890"}');

-- ============================================
-- Представление для удобного просмотра
-- ============================================
CREATE OR REPLACE VIEW admin_audit_log_view AS
SELECT 
    aal.id,
    aal.admin_user_id,
    COALESCE(au.username, 'Unknown') AS admin_username,
    aal.action_type,
    aal.target_user_id,
    COALESCE(tu.username, 'N/A') AS target_username,
    aal.old_value,
    aal.new_value,
    aal.details,
    aal.created_at,
    aal.success,
    CASE 
        WHEN aal.action_type = 'set_level' THEN '🔧 Изменение уровня'
        WHEN aal.action_type = 'remove_level' THEN '⬇️ Сброс уровня'
        WHEN aal.action_type = 'add_user' THEN '➕ Добавление'
        WHEN aal.action_type = 'remove_user' THEN '❌ Удаление'
        WHEN aal.action_type = 'view_history' THEN '👁️ Просмотр истории'
        WHEN aal.action_type = 'view_stats' THEN '📊 Просмотр статистики'
        WHEN aal.action_type = 'maintenance_mode' THEN '🔧 Режим тех.работ'
        ELSE aal.action_type
    END AS action_display
FROM admin_audit_log aal
LEFT JOIN users au ON aal.admin_user_id = au.user_id
LEFT JOIN users tu ON aal.target_user_id = tu.user_id
ORDER BY aal.created_at DESC;

-- ============================================
-- Grant permissions (если нужно)
-- ============================================
-- GRANT SELECT ON admin_audit_log TO authenticated;
-- GRANT ALL ON admin_audit_log TO service_role;
