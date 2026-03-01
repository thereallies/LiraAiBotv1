-- SQL миграция для добавления таблицы user_settings
-- Выполнить в Supabase SQL Editor: https://xmdvjrgpqqdoofamkzut.supabase.co/project/_/sql

-- Создаём таблицу настроек пользователей
CREATE TABLE IF NOT EXISTS public.user_settings (
    user_id TEXT PRIMARY KEY,
    selected_model TEXT DEFAULT 'groq-llama',
    image_model TEXT DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Добавляем индекс для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON public.user_settings(user_id);

-- Включаем Row Level Security (RLS)
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

-- Создаём политику для чтения (пользователи могут читать свои настройки)
CREATE POLICY "Users can view own settings"
    ON public.user_settings
    FOR SELECT
    USING (true);  -- Разрешаем чтение для всех авторизованных

-- Создаём политику для записи (сервисный ключ может писать)
CREATE POLICY "Service key can insert settings"
    ON public.user_settings
    FOR INSERT
    WITH CHECK (true);

-- Создаём политику для обновления
CREATE POLICY "Service key can update settings"
    ON public.user_settings
    FOR UPDATE
    USING (true);

-- Создаём политику для удаления
CREATE POLICY "Service key can delete settings"
    ON public.user_settings
    FOR DELETE
    USING (true);

-- Комментарии для документации
COMMENT ON TABLE public.user_settings IS 'Настройки пользователей: выбор модели для текста и генерации изображений';
COMMENT ON COLUMN public.user_settings.selected_model IS 'Выбранная модель для текстового общения';
COMMENT ON COLUMN public.user_settings.image_model IS 'Выбранная модель для генерации изображений';

-- Проверяем создание
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'user_settings'
ORDER BY ordinal_position;
