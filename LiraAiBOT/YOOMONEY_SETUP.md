# 💳 Настройка оплаты через ЮMoney

## 📋 Обзор

Реализована система оплаты для повышения уровня доступа с `user` до `sub+` (30 генераций/день).

**Стоимость**: 100 рублей  
**Лимит sub+**: 30 генераций в день  
**Лимит user**: 3 генерации в день

---

## 🚀 Быстрая настройка

### 1. Выполните миграцию базы данных

```sql
-- В Supabase Dashboard -> SQL Editor
-- Выполните файл: supabase_payments_migration.sql
```

### 2. Настройте переменные окружения

Добавьте в `.env`:

```bash
# === ЮMoney оплата ===
YOOMONEY_WALLET=410011234567890  # Ваш номер кошелька ЮMoney
YOOMONEY_SECRET=your_secret_key  # Секретный ключ для уведомлений
BASE_URL=https://yourdomain.com  # URL вашего сервера (HTTPS обязательно!)
```

### 3. Получите данные кошелька ЮMoney

1. Откройте [ЮMoney для разработчиков](https://yoomoney.ru/myservices/online)
2. Создайте форму оплаты (QuickPay)
3. Скопируйте номер кошелька (`YOOMONEY_WALLET`)
4. В настройках уведомлений укажите:
   - **URL уведомлений**: `https://yourdomain.com/yoomoney-webhook`
   - **Секретный ключ**: сгенерируйте и сохраните (`YOOMONEY_SECRET`)

### 4. Запустите платежный сервер

```bash
cd /Users/iluyshin.d/Desktop/LiraAiBOT/backend
python3 payment_server.py
```

Или через PM2 (продакшен):

```bash
pm2 start backend/payment_server.py --name liraai-payment --interpreter python3
```

---

## 📁 Структура файлов

```
LiraAiBOT/
├── backend/
│   ├── payment_server.py       # FastAPI сервер для оплаты
│   ├── templates/
│   │   └── pay.html            # WebApp страница оплаты
│   └── database/
│       └── users_db.py         # + методы для платежей
├── supabase_payments_migration.sql  # Миграция БД
└── .env                        # Переменные окружения
```

---

## 🔧 Как это работает

### 1. Пользователь исчерпывает лимит

Когда пользователь уровня `user` исчерпывает 3 генерации:
- Бот показывает сообщение с кнопкой "💳 Оплатить sub+ (100₽)"
- Кнопка ведёт на WebApp: `/pay?user_id=XXX&chat_id=YYY&sign=ZZZ`

### 2. WebApp оплата

- Пользователь нажимает "Оплатить подписку"
- Открывается ЮMoney с суммой 100₽
- После оплаты ЮMoney отправляет webhook на `/yoomoney-webhook`

### 3. Обработка webhook

- Сервер проверяет подпись уведомления
- Обновляет статус платежа на `success`
- Повышает уровень пользователя до `sub+`
- Логирует в `admin_audit_log` как `system`
- Отправляет уведомление пользователю

### 4. Пользователь получает sub+

- Уровень повышен автоматически
- Лимит: 30 генераций в день
- Уведомление в Telegram

---

## 📊 Таблицы базы данных

### `payments`

| Поле | Тип | Описание |
|------|-----|----------|
| `payment_id` | TEXT | Уникальный ID платежа |
| `user_id` | TEXT | ID пользователя Telegram |
| `chat_id` | TEXT | ID чата для уведомлений |
| `amount` | INTEGER | Сумма (100₽) |
| `status` | TEXT | `pending`, `success`, `failed` |
| `yoomoney_operation_id` | TEXT | ID операции от ЮMoney |
| `created_at` | TIMESTAMPTZ | Время создания |
| `updated_at` | TIMESTAMPTZ | Время обновления |

### `admin_audit_log` (новые записи)

| `action_type` | Описание |
|---------------|----------|
| `payment_success` | Успешная оплата |
| `set_level` (admin_user_id='system') | Автоматическое повышение |

---

## 🔐 Безопасность

### Подпись WebApp URL

```python
signature = HMAC-SHA256(user_id, key=BOT_TOKEN)
```

Проверяется в `/pay` для предотвращения подделки.

### Подпись webhook от ЮMoney

```python
params_string = ";".join([notification_type, operation_id, amount, ...])
expected_hash = HMAC-SHA1(params_string, key=YOOMONEY_SECRET)
```

Сравнивается с `sha1_hash` от ЮMoney.

### HTTPS обязательно

Для продакшена используйте HTTPS:
- Let's Encrypt (бесплатно)
- Cloudflare Tunnel
- Reverse proxy (nginx)

---

## 🧪 Тестирование

### 1. Создайте тестовый платёж

```bash
curl "http://localhost:8001/pay?user_id=1658547011&chat_id=1658547011&sign=$(python3 -c "import hmac,hashlib,os; print(hmac.new(os.environ['TELEGRAM_BOT_TOKEN'].encode(), b'1658547011', hashlib.sha256).hexdigest())")"
```

### 2. Проверьте статус

```sql
SELECT * FROM payments WHERE user_id = '1658547011' ORDER BY created_at DESC LIMIT 5;
```

### 3. Проверьте уровень

```sql
SELECT user_id, access_level FROM users WHERE user_id = '1658547011';
```

---

## 📝 Админ команды

### Просмотр платежей

```sql
SELECT * FROM payments_view LIMIT 20;
```

### Статистика по платежам

```sql
SELECT 
    status,
    COUNT(*) as count,
    SUM(amount) as total_amount
FROM payments
GROUP BY status;
```

---

## 🐛 Устранение неполадок

### Платежи не создаются

1. Проверьте Supabase подключение
2. Выполнена ли миграция?
3. Проверьте логи: `tail -f logs/payment_server.log`

### Webhook не работает

1. Проверьте URL в настройках ЮMoney
2. Проверьте `YOOMONEY_SECRET`
3. Проверьте доступность сервера из интернета

### Уровень не повышается

1. Проверьте `admin_audit_log`
2. Проверьте текущий уровень: `SELECT access_level FROM users WHERE user_id=XXX`
3. Проверьте логи payment_server

---

## 📞 Контакты

**Разработчик**: Danil Alekseevich  
**Канал**: [@liranexus](https://t.me/liranexus)

---

**Версия**: 1.0.0  
**Дата**: 2026-03-03  
**Статус**: ✅ Готово к использованию
