# ⚙️ Переменные окружения для Bothost

**Полный список всех необходимых переменных для развёртывания LiraAI MultiAssistant на Bothost.**

---

## 📋 Содержание

1. [Основные API ключи](#1-основные-api-ключи)
2. [Telegram](#2-telegram)
3. [LLM провайдеры](#3-llm-провайдеры)
4. [Генерация изображений](#4-генерация-изображений)
5. [Голосовые функции](#5-голосовые-функции)
6. [База данных](#6-база-данных)
7. [ЮMoney оплата](#7-юmoney-оплата)
8. [Настройки безопасности](#8-настройки-безопасности)
9. [Прочие настройки](#9-прочие-настройки)

---

## 1. Основные API ключи

### OPENROUTER_API_KEY
**Обязательно**: ✅ Да  
**Описание**: Основной API ключ для OpenRouter (Solar, Trinity, GLM)  
**Пример**: `sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`  
**Где получить**: https://openrouter.ai/keys

### OPENROUTER_API_KEY1, OPENROUTER_API_KEY2...
**Обязательно**: ❌ Нет  
**Описание**: Дополнительные ключи OpenRouter для ротации  
**Пример**: `sk-or-v1-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy`

### OPENROUTER_API_KEY_PAID
**Обязательно**: ❌ Нет  
**Описание**: Платный ключ OpenRouter с повышенными лимитами  
**Пример**: `sk-or-v1-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz`

---

## 2. Telegram

### TELEGRAM_BOT_TOKEN
**Обязательно**: ✅ Да  
**Описание**: Токен Telegram бота от @BotFather  
**Пример**: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`  
**Где получить**: https://t.me/BotFather

### TELEGRAM_BOT_TOKEN2, TELEGRAM_BOT_TOKEN3...
**Обязательно**: ❌ Нет  
**Описание**: Дополнительные токены для нескольких ботов  
**Пример**: `0987654321:ZYXwvuTSRqpoNMLkjihGFEdcba`

### TELEGRAM_GROUP_ID, TELEGRAM_GROUP_ID1...
**Обязательно**: ❌ Нет  
**Описание**: ID групп для FeedbackBot (заполняются автоматически)  
**Пример**: `-1001234567890`

---

## 3. LLM провайдеры

### GROQ_API_KEY
**Обязательно**: ✅ Да (рекомендуется)  
**Описание**: API ключ для Groq (быстрые модели Llama)  
**Пример**: `gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`  
**Где получить**: https://console.groq.com/keys

### GROQ_BASE_URL
**Обязательно**: ❌ Нет  
**Описание**: Базовый URL Groq API  
**Значение по умолчанию**: `https://api.groq.com/openai/v1`

### CEREBRAS_API_KEY
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ для Cerebras (сверхбыстрые модели)  
**Пример**: `csk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`  
**Где получить**: https://cloud.cerebras.ai/

---

## 4. Генерация изображений

### POLZA_API_KEY
**Обязательно**: ✅ Да (для Z-Image)  
**Описание**: API ключ Polza.ai для генерации изображений  
**Пример**: `pza_xxxxxxxxxxxxxxxxxxxxxxxxxx`  
**Где получить**: https://polza.ai/

### GEMINI_API_KEY
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ Google Gemini для генерации изображений  
**Пример**: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX`  
**Где получить**: https://makersuite.google.com/app/apikey

### REPLICATE_API_TOKEN
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API токен Replicate для FLUX и других моделей  
**Пример**: `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`  
**Где получить**: https://replicate.com/account/api-tokens

### HF_API_KEY / HF_TOKEN
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ Hugging Face  
**Пример**: `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`  
**Где получить**: https://huggingface.co/settings/tokens

### KIE_API_KEY
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ KIE.AI (Nano Banana 2)  
**Пример**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### SILICONFLOW_API_KEY
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ SiliconFlow (FLUX)  
**Пример**: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### SILICONFLOW_BASE_URL
**Обязательно**: ❌ Нет  
**Описание**: Базовый URL SiliconFlow API  
**Значение по умолчанию**: `https://api.siliconflow.cn/v1`

### POLLINATIONS_GEN_API_KEY
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ Pollinations Gen (Nano Banana Pro)  
**Пример**: `sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### POLLINATIONS_GEN_BASE_URL
**Обязательно**: ❌ Нет  
**Описание**: Базовый URL Pollinations Gen API  
**Значение по умолчанию**: `https://gen.pollinations.ai`

---

## 5. Голосовые функции

### ELEVEN_API_KEY
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ ElevenLabs для TTS (высокое качество)  
**Пример**: `xi_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`  
**Где получить**: https://elevenlabs.io/api-key

### ELEVEN_VOICE_ID
**Обязательно**: ❌ Нет  
**Описание**: ID голоса ElevenLabs по умолчанию  
**Пример**: `XXXXXXXXXXXXXXXXXXXX`

### ELEVEN_VOICE_ID_MALE
**Обязательно**: ❌ Нет  
**Описание**: ID мужского голоса

### ELEVEN_VOICE_ID_FEMALE
**Обязательно**: ❌ Нет  
**Описание**: ID женского голоса

### ELEVEN_MODEL_ID
**Обязательно**: ❌ Нет  
**Описание**: Модель ElevenLabs  
**Значение по умолчанию**: `eleven_multilingual_v2`

### ELEVEN_PROXIES
**Обязательно**: ❌ Нет  
**Описание**: Прокси для ElevenLabs (через запятую)

---

## 6. База данных

### USE_SUPABASE
**Обязательно**: ✅ Да (для продакшена)  
**Описание**: Использовать Supabase вместо SQLite  
**Значения**: `true` или `false`  
**Значение по умолчанию**: `false`

### SUPABASE_URL
**Обязательно**: ✅ Да (если USE_SUPABASE=true)  
**Описание**: URL проекта Supabase  
**Пример**: `https://xxxxxxxxxxxxx.supabase.co`  
**Где получить**: https://supabase.com/dashboard/project/_/settings/api

### SUPABASE_KEY
**Обязательно**: ✅ Да (если USE_SUPABASE=true)  
**Описание**: Service Role ключ Supabase  
**Пример**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`  
**Где получить**: https://supabase.com/dashboard/project/_/settings/api

### EMBEDDING_API_KEY
**Обязательно**: ❌ Нет (опционально)  
**Описание**: API ключ для эмбеддингов (OpenAI)  
**Пример**: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 7. ЮMoney оплата

### YOOMONEY_WALLET
**Обязательно**: ✅ Да (для оплаты)  
**Описание**: Номер кошелька ЮMoney для приёма платежей  
**Пример**: `4100119485670330`  
**Где получить**: https://yoomoney.ru/transfer/myservices/online

### YOOMONEY_SECRET
**Обязательно**: ✅ Да (для webhook)  
**Описание**: Секретный ключ для проверки уведомлений от ЮMoney  
**Пример**: `6CA85A92063C69296718B0B72E654352C8677A1E...`  
**Где получить**: В настройках формы оплаты ЮMoney

### YOOMONEY_CLIENT_SECRET
**Обязательно**: ❌ Нет (опционально)  
**Описание**: OAuth2 client_secret для расширенной интеграции  
**Пример**: `055EB2D15B8BFA1E74B09AE0EC93342A...`

### BASE_URL
**Обязательно**: ✅ Да (для WebApp)  
**Описание**: Базовый URL вашего сервера для платежного WebApp  
**Пример**: `http://5.129.239.185:8001` или `https://yourdomain.com`  
**Важно**: Для продакшена используйте HTTPS!

---

## 8. Настройки безопасности

### ADMIN_USER_ID
**Обязательно**: ✅ Да  
**Описание**: Telegram ID администратора бота  
**Пример**: `1658547011`  
**Как узнать**: Отправьте боту @userinfobot в Telegram

### CORS_ORIGINS
**Обязательно**: ❌ Нет  
**Описание**: Разрешённые CORS источники (через запятую)  
**Значение по умолчанию**: `*` (все разрешены)  
**Пример**: `https://yoursite.com,https://admin.yoursite.com`

### DEBUG
**Обязательно**: ❌ Нет  
**Описание**: Режим отладки (подробные логи)  
**Значения**: `true` или `false`  
**Значение по умолчанию**: `false`

---

## 9. Прочие настройки

### LLM_API
**Обязательно**: ❌ Нет  
**Описание**: Дополнительный LLM API (кастомный)

### ENABLE_AUTONOMOUS_GROUP_CHAT
**Обязательно**: ❌ Нет  
**Описание**: Включить автономный режим в группах  
**Значения**: `true` или `false`  
**Значение по умолчанию**: `false`

### AUTONOMOUS_INTERVAL_HOURS
**Обязательно**: ❌ Нет  
**Описание**: Интервал автономных сообщений (часы)  
**Значение по умолчанию**: `1`

### MAX_CONVERSATION_EXCHANGES
**Обязательно**: ❌ Нет  
**Описание**: Максимальное количество сообщений в диалоге  
**Значение по умолчанию**: `50`

### FEEDBACK_BOT_ENABLED
**Обязательно**: ❌ Нет  
**Описание**: Включить FeedbackBot режим  
**Значения**: `true` или `false`  
**Значение по умолчанию**: `false`

### FEEDBACK_BOT_GROUP_IDS
**Обязательно**: ❌ Нет  
**Описание**: ID групп для FeedbackBot (через запятую)  
**Пример**: `-1001234567890,-1009876543210`

### FEEDBACK_KNOWLEDGE_DIR
**Обязательно**: ❌ Нет  
**Описание**: Путь к директории знаний FeedbackBot  
**Значение по умолчанию**: `data/feedback_knowledge`

---

## 📝 Полный пример .env файла

```bash
# === ОСНОВНЫЕ API КЛЮЧИ ===
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# OPENROUTER_API_KEY1=sk-or-v1-yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
# OPENROUTER_API_KEY_PAID=sk-or-v1-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
# TELEGRAM_BOT_TOKEN2=0987654321:ZYXwvuTSRqpoNMLkjihGFEdcba
# TELEGRAM_GROUP_ID=-1001234567890

# === GROQ ===
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_BASE_URL=https://api.groq.com/openai/v1

# === CEREBRAS ===
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ===
POLZA_API_KEY=pza_xxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# KIE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
# POLLINATIONS_GEN_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# POLLINATIONS_GEN_BASE_URL=https://gen.pollinations.ai

# === ГОЛОСОВЫЕ ФУНКЦИИ ===
# ELEVEN_API_KEY=xi_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ELEVEN_VOICE_ID=XXXXXXXXXXXXXXXXXXXX
# ELEVEN_VOICE_ID_MALE=XXXXXXXXXXXXXXXXXXXX
# ELEVEN_VOICE_ID_FEMALE=XXXXXXXXXXXXXXXXXXXX
# ELEVEN_MODEL_ID=eleven_multilingual_v2
# ELEVEN_PROXIES=proxy1.com,proxy2.com

# === ЭМБЕДДИНГИ ===
# EMBEDDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === НАСТРОЙКИ БЕЗОПАСНОСТИ ===
ADMIN_USER_ID=1658547011
CORS_ORIGINS=*
DEBUG=false

# === SUPABASE ===
USE_SUPABASE=true
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# === ЮMoney ОПЛАТА ===
YOOMONEY_WALLET=4100119485670330
YOOMONEY_SECRET=6CA85A92063C69296718B0B72E654352C8677A1E...
# YOOMONEY_CLIENT_SECRET=055EB2D15B8BFA1E74B09AE0EC93342A...
BASE_URL=http://your-server-ip:8001

# === ПРОЧЕЕ ===
# LLM_API=
# ENABLE_AUTONOMOUS_GROUP_CHAT=false
# AUTONOMOUS_INTERVAL_HOURS=1
# MAX_CONVERSATION_EXCHANGES=50
# FEEDBACK_BOT_ENABLED=false
# FEEDBACK_BOT_GROUP_IDS=-1001234567890
# FEEDBACK_KNOWLEDGE_DIR=data/feedback_knowledge
```

---

## 🔐 Рекомендации по безопасности

### 1. Никогда не коммитьте .env в Git

```bash
# .env уже в .gitignore - проверьте!
cat .gitignore | grep .env
```

### 2. Используйте разные ключи для dev/prod

```bash
# .env.development
OPENROUTER_API_KEY=sk-or-dev-xxx

# .env.production
OPENROUTER_API_KEY=sk-or-prod-yyy
```

### 3. Регулярно обновляйте ключи

```bash
# Раз в 3-6 месяцев
# 1. Создайте новый ключ в панели провайдера
# 2. Обновите в .env
# 3. Перезапустите бота
pm2 restart liraai-bot
```

### 4. Ограничьте права доступа

```bash
# Только владелец может читать .env
chmod 600 .env
chown your_user:your_user .env
```

### 5. Используйте secrets manager (опционально)

Для продакшена рассмотрите:
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault

---

## 📞 Где получить ключи

| Сервис | URL | Время получения |
|--------|-----|-----------------|
| Telegram | https://t.me/BotFather | 2 мин |
| OpenRouter | https://openrouter.ai/keys | 5 мин |
| Groq | https://console.groq.com/keys | 5 мин |
| Supabase | https://supabase.com | 10 мин |
| ЮMoney | https://yoomoney.ru | 15 мин |
| Polza.ai | https://polza.ai | 5 мин |
| Gemini | https://makersuite.google.com | 10 мин |
| ElevenLabs | https://elevenlabs.io | 5 мин |

---

## ✅ Чек-лист перед запуском

- [ ] `TELEGRAM_BOT_TOKEN` установлен
- [ ] `OPENROUTER_API_KEY` установлен
- [ ] `GROQ_API_KEY` установлен (рекомендуется)
- [ ] `POLZA_API_KEY` установлен (для генерации)
- [ ] `SUPABASE_URL` и `SUPABASE_KEY` установлены
- [ ] `USE_SUPABASE=true` (для продакшена)
- [ ] `ADMIN_USER_ID` установлен
- [ ] `BASE_URL` установлен (для WebApp)
- [ ] `YOOMONEY_WALLET` установлен (для оплаты)
- [ ] `.env` имеет права `chmod 600`

---

**Версия**: 2.0.0  
**Дата обновления**: 2026-03-03  
**Статус**: ✅ Актуально для LiraAI MultiAssistant v2.0
