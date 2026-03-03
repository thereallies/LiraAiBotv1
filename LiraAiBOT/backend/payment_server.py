"""
Платежный сервер для интеграции с ЮMoney.
Обработка платежей для повышения уровня до sub+.
"""
import os
import hmac
import hashlib
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger("payment_server")

# Инициализация FastAPI
app = FastAPI(title="LiraAI Payment Server")

# Конфигурация
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "")
YOOMONEY_SECRET = os.getenv("YOOMONEY_SECRET", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Пути
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Создаем директории если нет
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Шаблоны и статика
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Supabase клиент
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase клиент инициализирован")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Supabase: {e}")


# ============================================
# Вспомогательные функции
# ============================================

def generate_signature(user_id: str) -> str:
    """Генерирует HMAC-SHA256 подпись для user_id"""
    message = user_id.encode('utf-8')
    key = BOT_TOKEN.encode('utf-8')
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return signature


def verify_signature(user_id: str, signature: str) -> bool:
    """Проверяет подпись"""
    expected = generate_signature(user_id)
    return hmac.compare_digest(expected, signature)


def get_user_access_level(user_id: str) -> Optional[str]:
    """Получает уровень доступа пользователя"""
    if not supabase:
        return None
    try:
        result = supabase.table("users").select("access_level").eq("user_id", user_id).execute()
        if result.data:
            return result.data[0].get("access_level", "user")
        return None
    except Exception as e:
        logger.error(f"Ошибка получения уровня доступа: {e}")
        return None


def update_user_access_level(user_id: str, new_level: str) -> bool:
    """Обновляет уровень доступа пользователя"""
    if not supabase:
        return False
    try:
        # Получаем текущий уровень
        current = supabase.table("users").select("access_level").eq("user_id", user_id).execute()
        old_level = current.data[0].get("access_level", "user") if current.data else "user"
        
        # Обновляем уровень
        supabase.table("users").update({"access_level": new_level}).eq("user_id", user_id).execute()
        
        # Логируем в audit log
        supabase.table("admin_audit_log").insert({
            "admin_user_id": "system",
            "admin_username": "System",
            "action_type": "set_level",
            "target_user_id": user_id,
            "old_value": old_level,
            "new_value": new_level,
            "details": {"payment_auto": True},
            "success": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"✅ Уровень пользователя {user_id} изменён: {old_level} → {new_level}")
        return True
    except Exception as e:
        logger.error(f"Ошибка обновления уровня: {e}")
        return False


def log_admin_action(
    admin_user_id: str,
    action_type: str,
    target_user_id: str,
    old_value: str = None,
    new_value: str = None,
    details: dict = None,
    success: bool = True
):
    """Логирует действие администратора"""
    if not supabase:
        return
    try:
        supabase.table("admin_audit_log").insert({
            "admin_user_id": admin_user_id,
            "admin_username": "System",
            "action_type": action_type,
            "target_user_id": target_user_id,
            "old_value": old_value,
            "new_value": new_value,
            "details": details or {},
            "success": success,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Ошибка логирования: {e}")


# ============================================
# Эндпоинты
# ============================================

@app.get("/")
async def root():
    """Главная страница"""
    return {"message": "LiraAI Payment Server", "status": "running"}


@app.get("/pay", response_class=HTMLResponse)
async def pay_page(
    user_id: str = Query(...),
    chat_id: str = Query(...),
    sign: str = Query(...)
):
    """
    Страница оплаты через ЮMoney WebApp.
    Проверяет подпись и создаёт платёж.
    """
    # Проверяем подпись
    if not verify_signature(user_id, sign):
        logger.warning(f"❌ Неверная подпись для user_id={user_id}")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Проверяем текущий уровень пользователя
    current_level = get_user_access_level(user_id)
    if current_level not in ("user", "subscriber"):
        # Уже имеет sub+ или admin - не предлагаем оплату
        logger.info(f"Пользователь {user_id} имеет уровень {current_level} - оплата не требуется")
        return HTMLResponse(
            content="<html><body><h2>⚠️ Оплата недоступна</h2><p>Ваш уровень доступа не позволяет приобрести sub+.</p></body></html>",
            status_code=400
        )
    
    # Генерируем payment_id
    payment_id = str(uuid.uuid4())
    
    # Сохраняем платёж в базу
    if supabase:
        try:
            supabase.table("payments").insert({
                "payment_id": payment_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "amount": 100,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            logger.info(f"💳 Создан платёж {payment_id} для user_id={user_id}")
        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
    
    # Рендерим шаблон
    return templates.TemplateResponse(
        "pay.html",
        {
            "request": {},
            "payment_id": payment_id,
            "yoomoney_wallet": YOOMONEY_WALLET,
            "base_url": BASE_URL,
            "user_id": user_id
        }
    )


@app.post("/yoomoney-webhook")
async def yoomoney_webhook(request: Request):
    """
    Webhook от ЮMoney для обработки уведомлений об оплате.
    """
    try:
        # Получаем данные формы
        form_data = await request.form()
        
        # Извлекаем параметры
        notification_type = form_data.get("notification_type", "")
        operation_id = form_data.get("operation_id", "")
        amount = form_data.get("amount", "")
        currency = form_data.get("currency", "")
        datetime_value = form_data.get("datetime", "")
        sender = form_data.get("sender", "")
        codepro = form_data.get("codepro", "false")
        label = form_data.get("label", "")  # Это наш payment_id
        sha1_hash = form_data.get("sha1_hash", "")
        
        logger.info(f"📬 Получено уведомление от ЮMoney: label={label}, operation_id={operation_id}")
        
        # Проверяем тип уведомления
        if notification_type != "p2p-incoming":
            logger.warning(f"Неизвестный тип уведомления: {notification_type}")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # Проверяем подпись (если используется secret)
        if YOOMONEY_SECRET:
            # Формируем строку для проверки подписи
            params = [
                notification_type,
                operation_id,
                amount,
                currency,
                datetime_value,
                sender,
                codepro,
                label
            ]
            params_string = ";".join(str(p) for p in params)
            
            # Вычисляем HMAC-SHA1
            expected_hash = hmac.new(
                YOOMONEY_SECRET.encode('utf-8'),
                params_string.encode('utf-8'),
                hashlib.sha1
            ).hexdigest()
            
            if not hmac.compare_digest(expected_hash, sha1_hash):
                logger.warning(f"❌ Неверная подпись уведомления")
                raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Находим платёж по label (payment_id)
        if not supabase or not label:
            logger.error("Supabase не подключен или label отсутствует")
            return JSONResponse(content={"status": "error"}, status_code=500)
        
        payment_result = supabase.table("payments").select("*").eq("payment_id", label).execute()
        
        if not payment_result.data:
            logger.warning(f"❌ Платёж {label} не найден")
            return JSONResponse(content={"status": "not_found"}, status_code=404)
        
        payment = payment_result.data[0]
        
        # Проверяем не обработан ли уже платёж
        if payment.get("status") == "success":
            logger.info(f"✅ Платёж {label} уже обработан")
            return JSONResponse(content={"status": "already_processed"}, status_code=200)
        
        # Проверяем успешность платежа
        is_success = (
            codepro == "false" and
            operation_id and
            amount and
            float(amount) >= 100
        )
        
        if is_success:
            # Обновляем статус платежа
            supabase.table("payments").update({
                "status": "success",
                "yoomoney_operation_id": operation_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("payment_id", label).execute()
            
            user_id = payment.get("user_id")
            chat_id = payment.get("chat_id")
            
            # Получаем текущий уровень пользователя
            current_level = get_user_access_level(user_id)
            
            # Повышаем до sub+ только если текущий уровень 'user' или 'subscriber'
            if current_level in ("user", "subscriber"):
                update_user_access_level(user_id, "sub+")
                
                # Отправляем уведомление пользователю
                try:
                    import aiohttp
                    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    async with aiohttp.ClientSession() as session:
                        await session.post(telegram_url, json={
                            "chat_id": chat_id or user_id,
                            "text": f"✅ **Оплата прошла успешно!**\n\n"
                                   f"Ваш уровень повышен до **sub+**!\n\n"
                                   f"🎉 Теперь у вас **30 генераций изображений в день**!\n\n"
                                   f"Спасибо за поддержку LiraAI! 💜"
                        })
                    logger.info(f"📤 Отправлено уведомление пользователю {user_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления: {e}")
            else:
                logger.info(f"Пользователь {user_id} уже имеет уровень {current_level}")
            
            # Логируем успешную оплату
            log_admin_action(
                admin_user_id="system",
                action_type="payment_success",
                target_user_id=user_id,
                old_value=payment.get("status"),
                new_value="success",
                details={
                    "payment_id": label,
                    "operation_id": operation_id,
                    "amount": amount
                }
            )
            
            logger.info(f"✅ Платёж {label} успешно обработан")
        else:
            # Платёж неуспешен
            supabase.table("payments").update({
                "status": "failed",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("payment_id", label).execute()
            
            logger.warning(f"❌ Платёж {label} не прошёл")
        
        return JSONResponse(content={"status": "ok"}, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
        return JSONResponse(content={"status": "error"}, status_code=500)


@app.get("/payment-success", response_class=HTMLResponse)
async def payment_success(payment_id: str = Query(None)):
    """
    Страница успешной оплаты.
    Показывает сообщение и закрывается через 3 секунды.
    """
    html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Оплата успешна</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            h1 {
                font-size: 2em;
                margin-bottom: 20px;
            }
            p {
                font-size: 1.2em;
                opacity: 0.9;
            }
            .checkmark {
                font-size: 4em;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="checkmark">✅</div>
            <h1>Оплата прошла успешно!</h1>
            <p>Ваш уровень повышен до <strong>sub+</strong>.</p>
            <p>Теперь у вас 30 генераций в день!</p>
            <p style="margin-top: 30px; font-size: 0.9em;">Окно закроется автоматически...</p>
        </div>
        <script>
            setTimeout(function() {
                window.close();
            }, 3000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health")
async def health_check():
    """Проверка здоровья сервера"""
    return {
        "status": "healthy",
        "supabase": "connected" if supabase else "disconnected",
        "yoomoney_wallet": "configured" if YOOMONEY_WALLET else "not configured"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "payment_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
