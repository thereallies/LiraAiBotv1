-- ============================================
-- Таблица платежей для ЮMoney интеграции
-- ============================================

-- Создаём таблицу для хранения платежей
CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT,
    amount INTEGER NOT NULL DEFAULT 100,
    status TEXT DEFAULT 'pending',  -- pending, success, failed
    yoomoney_operation_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at DESC);

-- Комментарии к таблице
COMMENT ON TABLE payments IS 'Платежи через ЮMoney для повышения до sub+';
COMMENT ON COLUMN payments.payment_id IS 'Уникальный ID платежа';
COMMENT ON COLUMN payments.user_id IS 'ID пользователя Telegram';
COMMENT ON COLUMN payments.chat_id IS 'ID чата для уведомлений';
COMMENT ON COLUMN payments.amount IS 'Сумма платежа в рублях';
COMMENT ON COLUMN payments.status IS 'Статус: pending, success, failed';
COMMENT ON COLUMN payments.yoomoney_operation_id IS 'ID операции от ЮMoney';
COMMENT ON COLUMN payments.created_at IS 'Время создания платежа';
COMMENT ON COLUMN payments.updated_at IS 'Время обновления статуса';

-- ============================================
-- Функция для обновления updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Примеры данных (для тестирования)
-- ============================================
-- INSERT INTO payments (payment_id, user_id, chat_id, amount, status)
-- VALUES ('test-payment-123', '1658547011', '1658547011', 100, 'pending');

-- ============================================
-- Представление для удобного просмотра
-- ============================================
CREATE OR REPLACE VIEW payments_view AS
SELECT 
    p.payment_id,
    p.user_id,
    COALESCE(u.username, 'Unknown') AS username,
    p.chat_id,
    p.amount,
    p.status,
    p.yoomoney_operation_id,
    p.created_at,
    p.updated_at,
    CASE 
        WHEN p.status = 'pending' THEN '⏳ Ожидает оплаты'
        WHEN p.status = 'success' THEN '✅ Успешно оплачен'
        WHEN p.status = 'failed' THEN '❌ Не оплачен'
        ELSE p.status
    END AS status_display
FROM payments p
LEFT JOIN users u ON p.user_id = u.user_id
ORDER BY p.created_at DESC;
