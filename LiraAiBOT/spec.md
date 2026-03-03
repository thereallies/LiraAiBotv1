# 🚀 Промпт для Qwen: Добавление уровня `sub+` и оплаты через ЮMoney в Telegram боте

## 📌 Контекст
У вас есть Telegram бот на Python с библиотекой `python-telegram-bot` (версия 20+). Бот уже имеет:
- Таблицу `users` в Supabase (или SQLite) с полями: `user_id` (TEXT), `access_level` (TEXT), `username`, `first_name`, и т.д.
- Таблицу `admin_audit_log` для логирования действий администраторов (с полями: `admin_user_id`, `admin_username`, `action_type`, `target_user_id`, `old_value`, `new_value`, `details`, `created_at`, `success`).
- Уровни доступа: `user` (обычный пользователь, 10 генераций в день), `subscriber` (безлимитный подписчик), `admin` (администратор).
- **Уровень `sub+` пока не реализован** – его нужно добавить.

## 🎯 Задача
Реализовать:
1. Добавление уровня `sub+` с дневным лимитом 30 генераций.
2. Механизм оплаты 100 рублей через ЮMoney для пользователей уровня `user` при исчерпании дневного лимита, после успешной оплаты пользователь автоматически получает уровень `sub+`.
3. Логирование повышения уровня в `admin_audit_log` с указанием `admin_user_id = 'system'`.

## 📋 Детальные требования

### 1. Логика уровней и лимитов
- **Функция `get_daily_limit(level: str) -> int | None`**:
  - `'user'` → 10
  - `'sub+'` → 30
  - `'subscriber'` → `None` (безлимит)
  - `'admin'` → `None` (безлимит)

- **Таблица использования** (если её нет, нужно создать):
  - Название: `usage_log` или поле `daily_usage` в `users`.
  - Если создаёте отдельную таблицу: `usage_log` с полями `user_id`, `date`, `count`.
  - Методы работы с использованием:
    - `get_today_usage(user_id) -> int` – возвращает количество использований за сегодня.
    - `increment_usage(user_id)` – увеличивает счётчик на 1.

- **В команде генерации (например, `/generate`)**:
  - Получить пользователя, его уровень, лимит.
  - Получить сегодняшнее использование.
  - Если `использовано < лимита` (или лимит `None`), разрешить генерацию, увеличить счётчик.
  - Если лимит достигнут **и уровень пользователя `'user'`**, отправить сообщение с предложением оплатить (см. п.2).
  - Для других уровней при достижении лимита (если лимит не `None`) – просто сообщить о превышении без предложения оплаты.

### 2. Интерфейс предложения оплаты
- При исчерпании лимита у `user` отправить сообщение:
  ```
  ❌ Вы исчерпали дневной лимит (10 генераций).
  Оплатите 100 рублей и получите уровень sub+ с лимитом 30 генераций в день!
  ```
- Под сообщением – inline-кнопка с `WebAppInfo`, ведущая на URL:  
  `https://yourdomain.com/pay?user_id={user_id}&chat_id={chat_id}&sign={signature}`
  - `signature` = HMAC-SHA256 от `user_id` с использованием секретного ключа (например, `BOT_TOKEN`). Это для защиты от подделки.

### 3. Веб-сервер на FastAPI
Создать файл `payment_server.py` с эндпоинтами:

#### **GET `/pay`**
- Параметры: `user_id`, `chat_id`, `sign`.
- Проверить подпись: если не совпадает – вернуть ошибку 403.
- Сгенерировать уникальный `payment_id` (например, `uuid4`).
- Сохранить в таблицу `payments` запись:
  - `payment_id` (PRIMARY KEY)
  - `user_id`
  - `chat_id`
  - `amount = 100`
  - `status = 'pending'`
  - `created_at = now()`
- Вернуть HTML-страницу (шаблон `pay.html`) с вставленным `payment_id`.

#### **POST `/yoomoney-webhook`**
- Эндпоинт принимает уведомление от ЮMoney (HTTP POST с параметрами формы).
- Проверить подпись уведомления с использованием `YOOMONEY_SECRET` (секрет, указанный в настройках кошелька). Алгоритм проверки описан в [документации ЮMoney](https://yoomoney.ru/docs/payment-notifications/notification-http).
- Извлечь параметр `label` – это `payment_id`.
- Найти запись в `payments` по `payment_id`.
- Если платеж успешен (параметр `codepro` = false, `unaccepted` = false, `operation_id` присутствует и т.д. – нужно ориентироваться на документацию):
  - Обновить статус записи на `'success'`.
  - Получить `user_id` из записи.
  - Обновить уровень пользователя в `users` на `'sub+'` (если текущий уровень `'user'`, иначе возможно уже обновлён – обработать).
  - Записать действие в `admin_audit_log`:
    ```python
    db.log_admin_action(
        admin_user_id='system',
        admin_username='System',
        action_type='set_level',
        target_user_id=user_id,
        old_value='user',
        new_value='sub+',
        success=True,
        details={'payment_id': payment_id, 'amount': 100}
    )
    ```
- Если платеж неуспешен – обновить статус на `'failed'`.
- Вернуть HTTP 200 (чтобы ЮMoney не повторял уведомление).

#### **GET `/payment-success`**
- Простая страница, которая показывает сообщение "Оплата прошла успешно! Вы можете закрыть это окно." и через 3 секунды автоматически закрывает окно (JavaScript `window.close()`).

### 4. HTML-шаблон WebApp (`templates/pay.html`)
- Страница с простым дизайном.
- Заголовок: "Оплата подписки sub+".
- Текст: "Нажмите кнопку ниже для оплаты 100 рублей через ЮMoney. После оплаты ваш уровень будет повышен автоматически."
- Кнопка "Перейти к оплате", при клике выполняется редирект на URL ЮMoney:
  ```
  https://yoomoney.ru/quickpay/confirm.xml?
    receiver={{ YOOMONEY_WALLET }}&
    quickpay-form=button&
    paymentType=AC&
    sum=100&
    label={{ payment_id }}&
    successURL={{ BASE_URL }}/payment-success?payment_id={{ payment_id }}
  ```
- Можно добавить обработку ошибок и закрытие окна после возврата с successURL.

### 5. Таблицы базы данных
Если их нет, создать SQL (для Supabase/SQLite):

**Таблица `payments`:**
```sql
CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT,
    amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
```

**Таблица `usage_log` (пример):**
```sql
CREATE TABLE usage_log (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    count INTEGER DEFAULT 0,
    UNIQUE(user_id, usage_date)
);
```

Методы работы с БД (предполагается, что у вас уже есть класс `Database` с методами). Если нет, нужно их добавить:
- `get_user(user_id)`
- `update_user_access_level(user_id, new_level)`
- `log_admin_action(...)`
- `get_today_usage(user_id)`
- `increment_usage(user_id)`
- `create_payment(payment_id, user_id, chat_id, amount)`
- `update_payment_status(payment_id, status)`
- `get_payment(payment_id)`

### 6. Безопасность
- **Подпись для WebApp**: при генерации ссылки `/pay` создавать HMAC-SHA256 от `user_id` с ключом = `BOT_TOKEN`. На эндпоинте `/pay` проверять эту подпись. Это предотвратит создание ссылок злоумышленниками от имени других пользователей.
- **Проверка webhook от ЮMoney**: использовать секретный ключ, указанный в настройках кошелька. В документации ЮMoney сказано: можно проверять подпись по параметру `sha1_hash` (если включены уведомления с секретом). Либо проверять IP-адреса отправителя. Реализовать проверку.
- **HTTPS обязательно** для продакшена.

### 7. Конфигурация (переменные окружения)
- `YOOMONEY_WALLET` – номер кошелька ЮMoney.
- `YOOMONEY_SECRET` – секретный ключ для проверки уведомлений.
- `BASE_URL` – базовый URL вашего сервера (например, `https://yourdomain.com`).
- `BOT_TOKEN` – токен Telegram бота (используется для подписи).
- `DATABASE_URL` – для подключения к БД (если нужно).

### 8. Зависимости
- `fastapi`
- `uvicorn[standard]`
- `jinja2` (для шаблонов)
- `python-telegram-bot[job-queue]`
- `httpx` (для отправки запросов, если нужно)
- `python-dotenv` (для загрузки .env)
- `asyncpg` (если Supabase/PostgreSQL)
- `aiosqlite` (если SQLite)
- `hmac`, `hashlib` (встроенные)

## 📁 Структура ответа Qwen
Ожидается, что Qwen предоставит:

1. **Обновлённый код `telegram_polling.py`** – фрагмент с командой генерации и проверкой лимитов, отправкой предложения оплаты.
2. **Полный код `payment_server.py`** – FastAPI приложение с эндпоинтами `/pay`, `/yoomoney-webhook`, `/payment-success`.
3. **Шаблон `templates/pay.html`** – HTML страница WebApp.
4. **Примеры методов работы с БД** (если их нужно дополнить).
5. **Инструкцию по настройке webhook в ЮMoney**.
6. **Пример файла `.env`** с переменными.
7. **Список зависимостей** (`requirements.txt`).

Код должен быть асинхронным, хорошо структурированным, с комментариями на русском или английском. Все эндпоинты должны обрабатывать ошибки и возвращать соответствующие HTTP-статусы.

## 🔍 Примечания
- Используйте существующие методы работы с БД из вашего проекта (предполагается, что они есть). Если нужно добавить новые методы, опишите их.
- При реализации проверки подписи webhook от ЮMoney обратитесь к официальной документации: [HTTP-уведомления](https://yoomoney.ru/docs/payment-notifications/notification-http).
- Убедитесь, что после успешной оплаты уровень обновляется немедленно и пользователь может пользоваться новым лимитом без перезапуска бота.
- Продумайте случай, когда пользователь уже имеет уровень `sub+` или выше – не предлагать оплату, даже если лимит исчерпан (у `sub+` лимит 30, он может быть исчерпан – тогда просто сообщение об исчерпании без предложения).

---

**Пожалуйста, предоставьте код, готовый к интеграции в существующий проект.**