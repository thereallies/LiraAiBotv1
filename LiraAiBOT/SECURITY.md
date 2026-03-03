# 🔒 Политика безопасности (Security Policy)

## 📋 Поддерживаемые версии

| Версия | Поддержка безопасности |
|--------|------------------------|
| 2.0.x  | ✅ Активная поддержка  |
| 1.5.x  | ⚠️ Ограниченная поддержка |
| < 1.5  | ❌ Не поддерживается   |

---

## 🐛 Сообщение об уязвимости

### Если вы обнаружили уязвимость безопасности:

**⚠️ НЕ создавайте публичный Issue на GitHub!**

Вместо этого отправьте информацию на:

- **Email**: [ваш email]
- **Telegram**: [@liranexus](https://t.me/liranexus)

### Что включать в отчёт:

1. **Описание уязвимости**
   - Тип уязвимости (XSS, SQL Injection, Auth Bypass, etc.)
   - Затронутые компоненты

2. **Шаги для воспроизведения**
   - Подробная инструкция
   - Примеры запросов (если применимо)

3. **Возможные последствия**
   - Что может сделать злоумышленник
   - Критичность уязвимости

4. **Рекомендации по исправлению** (опционально)
   - Ваши предложения по фиксу

---

## 📅 Процесс ответа

| Этап | Время ответа |
|------|--------------|
| Подтверждение получения | 24-48 часов |
| Оценка уязвимости | 3-5 дней |
| Исправление | 7-14 дней |
| Публикация advisory | После релиза патча |

---

## 🔐 Рекомендации по безопасности

### Для пользователей

1. **API ключи**
   - Никогда не коммитьте `.env` файл
   - Используйте разные ключи для dev/prod
   - Регулярно обновляйте ключи

2. **База данных**
   - Включите RLS (Row Level Security) в Supabase
   - Используйте service_role ключ только на сервере
   - Ограничьте доступ по IP

3. **Платежи**
   - Проверяйте подпись webhook от ЮMoney
   - Используйте HTTPS для продакшена
   - Храните YOOMONEY_SECRET в секрете

4. **Telegram бот**
   - Ограничьте права бота в группах
   - Используйте webhook с проверкой IP
   - Включите логирование всех действий

### Для разработчиков

1. **Код**
   - Проверяйте входные данные (validation)
   - Используйте parameterized queries для SQL
   - Избегайте eval() и exec()

2. **Зависимости**
   - Регулярно обновляйте пакеты
   - Проверяйте `pip audit`
   - Используйте `requirements.txt` с версиями

3. **Логирование**
   - Не логируйте чувствительные данные
   - Не логируйте API ключи
   - Не логируйте токены пользователей

---

## 🛡️ Реализованные меры безопасности

### В проекте

- ✅ HMAC-SHA256 подпись WebApp URL
- ✅ Проверка подписи webhook от ЮMoney
- ✅ Audit Log всех действий администраторов
- ✅ Проверка прав доступа для админ команд
- ✅ RLS (Row Level Security) для Supabase
- ✅ `.env` в `.gitignore`
- ✅ Разделение ключей для разных окружений

### Для базы данных

```sql
-- Включите RLS для чувствительных таблиц
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;

-- Политика: только админы могут читать audit log
CREATE POLICY admin_read_audit ON admin_audit_log
    FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM users 
        WHERE users.user_id = admin_audit_log.admin_user_id 
        AND users.access_level = 'admin'
    ));
```

---

## 📚 Ресурсы

### Документация

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://docs.python.org/3/library/security.html)
- [Supabase Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Telegram Bot Security](https://core.telegram.org/bots/security)

### Инструменты

- `pip audit` - Проверка уязвимостей в зависимостях
- `bandit` - Security linter для Python
- `safety` - Проверка пакетов на уязвимости

---

## 📞 Контакты

**Security Team**: [ваш email]  
**Telegram**: [@liranexus](https://t.me/liranexus)

---

**Последнее обновление**: 2026-03-03  
**Версия документа**: 1.0.0
