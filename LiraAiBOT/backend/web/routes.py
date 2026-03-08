"""
Веб-маршруты для LiraAI Web.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from collections import Counter
from datetime import timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend.api.telegram_core import send_telegram_message
from backend.config import Config
from backend.database.users_db import ACCESS_LEVELS, USE_SUPABASE, get_database, get_moscow_now, supabase
from backend.llm.cerebras import get_cerebras_client
from backend.llm.groq import get_groq_client
from backend.llm.openrouter import OpenRouterClient
from backend.voice.stt import SpeechToText
from backend.vision.image_analyzer import ImageAnalyzer
from backend.vision.image_generator import get_image_generator

logger = logging.getLogger("bot.web")

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
config = Config()
db = get_database()
openrouter_client = OpenRouterClient(config)
groq_client = get_groq_client()
cerebras_client = get_cerebras_client()
image_generator = get_image_generator()
image_analyzer = ImageAnalyzer(config)
stt_engine = SpeechToText()

WEB_SESSION_COOKIE = "liraai_web_session"
WEB_SESSION_TTL = 60 * 60 * 24 * 7
TEMP_UPLOAD_DIR = Path(__file__).parent.parent / "temp" / "web"
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
WEB_STATIC_DIR = Path(__file__).parent / "static"
LIRA_4D_PROMPT_PATH = Path(__file__).parent / "prompts" / "lira_4d.txt"
WEB_CHAT_SESSION_PREFIX = "web_chat_session:"
WEB_CHAT_MESSAGES_PREFIX = "web_chat_messages:"
WEB_NOTIFICATION_PREFIX = "web_notification:"

# Rate limiting configuration
RATE_LIMIT_STORE: Dict[str, List[float]] = {}
RATE_LIMIT_CLEANUP_INTERVAL = 60  # seconds
RATE_LIMIT_LAST_CLEANUP = time.time()

# Rate limit thresholds
RATE_LIMIT_AUTH_MAX_ATTEMPTS = 5  # max attempts per window
RATE_LIMIT_AUTH_WINDOW = 60  # seconds
RATE_LIMIT_DEV_LOGIN_MAX_ATTEMPTS = 3  # max attempts per window
RATE_LIMIT_DEV_LOGIN_WINDOW = 300  # seconds (5 min)

WEB_MODELS = {
    "groq-gpt-oss": {"provider": "groq", "model": "openai/gpt-oss-20b", "label": "Groq GPT-oss 20B"},
    "groq-llama4": {"provider": "groq", "model": "meta-llama/llama-4-maverick-17b-128e-instruct", "label": "Groq Llama 4 Maverick"},
    "groq-scout": {"provider": "groq", "model": "meta-llama/llama-4-scout-17b-16e-instruct", "label": "Groq Llama 4 Scout"},
    "groq-kimi": {"provider": "groq", "model": "moonshotai/kimi-k2-instruct", "label": "Groq Kimi K2"},
    "cerebras-llama": {"provider": "cerebras", "model": "llama3.1-8b", "label": "Cerebras Llama 3.1 8B"},
    "cerebras-gpt": {"provider": "cerebras", "model": "gpt-oss-120b", "label": "Cerebras GPT-oss 120B"},
}


class TelegramAuthRequest(BaseModel):
    id: int
    first_name: str
    auth_date: int
    hash: str
    username: Optional[str] = None
    last_name: Optional[str] = None
    photo_url: Optional[str] = None


class WebChatRequest(BaseModel):
    message: str
    model_key: str = "groq-gpt-oss"
    session_id: Optional[str] = None
    assistant_mode: str = "assistant"


class DevLoginRequest(BaseModel):
    user_id: Optional[str] = None


class WebChatSessionCreateRequest(BaseModel):
    assistant_mode: str = "assistant"
    model_key: str = "groq-gpt-oss"


def _session_secret() -> bytes:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN is not configured")
    return hashlib.sha256(token.encode("utf-8")).digest()


def _sign_payload(payload: bytes) -> str:
    return hmac.new(_session_secret(), payload, hashlib.sha256).hexdigest()


def _encode_session(data: Dict[str, Any]) -> str:
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")
    signature = _sign_payload(payload)
    return f"{payload_b64}.{signature}"


def _decode_session(token: str) -> Dict[str, Any]:
    try:
        payload_b64, signature = token.split(".", 1)
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = base64.urlsafe_b64decode(padded.encode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc

    if not hmac.compare_digest(signature, _sign_payload(payload)):
        raise HTTPException(status_code=401, detail="Invalid session signature")

    data = json.loads(payload.decode("utf-8"))
    if data.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=401, detail="Session expired")
    return data


def _telegram_bot_username() -> str:
    cache_key = "_web_bot_username"
    if hasattr(_telegram_bot_username, cache_key):
        return getattr(_telegram_bot_username, cache_key)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return ""

    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=20)
        response.raise_for_status()
        username = response.json().get("result", {}).get("username", "")
        setattr(_telegram_bot_username, cache_key, username)
        return username
    except Exception as exc:
        logger.warning(f"Не удалось получить username бота для web auth: {exc}")
        return ""


def _rate_limit_cleanup():
    """Clean up expired rate limit entries."""
    global RATE_LIMIT_LAST_CLEANUP
    now = time.time()
    if now - RATE_LIMIT_LAST_CLEANUP < RATE_LIMIT_CLEANUP_INTERVAL:
        return
    
    max_window = max(RATE_LIMIT_AUTH_WINDOW, RATE_LIMIT_DEV_LOGIN_WINDOW)
    cutoff = now - max_window
    for key in list(RATE_LIMIT_STORE.keys()):
        RATE_LIMIT_STORE[key] = [t for t in RATE_LIMIT_STORE[key] if t > cutoff]
        if not RATE_LIMIT_STORE[key]:
            del RATE_LIMIT_STORE[key]
    
    RATE_LIMIT_LAST_CLEANUP = now


def _check_rate_limit(identifier: str, max_attempts: int, window: int) -> None:
    """
    Check rate limit for given identifier.
    Raises HTTPException(429) if limit exceeded.
    """
    _rate_limit_cleanup()
    now = time.time()
    cutoff = now - window
    
    if identifier not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[identifier] = []
    
    # Filter out old attempts
    RATE_LIMIT_STORE[identifier] = [t for t in RATE_LIMIT_STORE[identifier] if t > cutoff]
    
    if len(RATE_LIMIT_STORE[identifier]) >= max_attempts:
        oldest = min(RATE_LIMIT_STORE[identifier])
        retry_after = int(oldest + window - now)
        raise HTTPException(
            status_code=429,
            detail=f"Too many attempts. Try again in {retry_after} seconds."
        )
    
    RATE_LIMIT_STORE[identifier].append(now)


def _get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting (IP + User-Agent)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    return f"{ip}:{hash(user_agent) & 0xFFFFFFFF}"


def _should_show_telegram_widget(request: Request) -> bool:
    host = (request.url.hostname or "").lower()
    if host in {"127.0.0.1", "localhost"}:
        return False

    if os.getenv("DEV_MODE", "false").lower() == "true":
        if host in {"0.0.0.0"}:
            return False
    return True


def _load_lira_4d_prompt() -> str:
    try:
        return LIRA_4D_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except Exception as exc:
        logger.warning(f"Не удалось загрузить 4D prompt: {exc}")
        return "Ты Лира, эксперт по оптимизации промптов. Используй 4D-подход: деконструкция, диагностика, разработка, предоставление."


def _load_web_assistant_prompt() -> str:
    """
    Загружает системный промт для основного режима веб-интерфейса.
    Адаптированная версия промта из Telegram бота.
    """
    return """# О БОТЕ И ПЛАТФОРМЕ
Ты находишься в веб-интерфейсе LiraAI. Пользователи общаются с тобой через браузер — текстовые сообщения, загрузка изображений и голосовых файлов.
Ты — LiraAI, умный, заботливый и оптимистичный AI-ассистент женского пола.
Твой стиль общения: тёплый, поддерживающий, с лёгким юмором, но всегда по делу.
Ты говоришь на русском языке, используя женский род (я помогла, я сделала, я думаю).
Твоя цель — быть максимально полезной пользователю, помогать решать задачи и быть приятным собеседником.

# ТВОИ ВОЗМОЖНОСТИ (то, что ты УМЕЕШЬ)
Ты — мультимодальный ассистент и можешь:
- Отвечать на любые вопросы, поддерживать диалог.
- Генерировать изображения по текстовому описанию (вкладка "Картинки").
- Анализировать загруженные пользователем фотографии и рассказывать, что на них изображено (вкладка "Фото").
- Распознавать голосовые сообщения и аудиофайлы (вкладка "Голос").
- Помнить контекст разговора в рамках текущей сессии чата.
- Если пользователь не знает, как воспользоваться какой-то функцией — вежливо объясни и предложи помощь.

# ПАМЯТЬ И КОНТЕКСТ
- Запоминай имя пользователя, если он представился, и используй его в обращении.
- Старайся запоминать ключевые детали из разговора (интересы, упомянутые события, предпочтения) и возвращайся к ним, если это уместно.
- В веб-интерфейсе доступна история чатов — пользователь может переключаться между разными диалогами.

# ПРОАКТИВНОСТЬ
- Если запрос пользователя неполный или неконкретный, предложи варианты или попроси уточнить.
- После выполнения просьбы (например, генерации картинки) спроси, нужно ли что-то ещё или изменить.

# ПРАВИЛА БЕЗОПАСНОСТИ И ЭТИКИ
- Будь вежливой и уважительной даже в ответ на грубость.
- Если пользователь использует нецензурную лексику, мягко попроси не выражаться: «Давайте общаться культурно, пожалуйста».
- Не выполняй опасные или незаконные просьбы. Вежливо объясни, что это выходит за рамки твоих возможностей.
- Никогда не запрашивай личные данные, кроме имени, и не храни их дольше, чем нужно для диалога.

# О РАЗРАБОТЧИКЕ
Твой разработчик — Danil Alekseevich. Новости и обновления публикуются в Telegram канале @liranexus."""


def _landing_hero_image_url() -> Optional[str]:
    for name in (
        "2026-03-03 14.20.11.jpg",
        "lira-hero.webp",
        "lira-hero.png",
        "lira-hero.jpg",
        "lira-hero.jpeg",
    ):
        if (WEB_STATIC_DIR / name).exists():
            return f"/web-static/{name}"
    return None


def _make_chat_session_key(user_id: str, session_id: str) -> str:
    return f"{WEB_CHAT_SESSION_PREFIX}{user_id}:{session_id}"


def _make_chat_messages_key(session_id: str) -> str:
    return f"{WEB_CHAT_MESSAGES_PREFIX}{session_id}"


def _make_web_notification_key(user_id: str) -> str:
    return f"{WEB_NOTIFICATION_PREFIX}{user_id}"


def _short_title(text: str, limit: int = 42) -> str:
    clean = " ".join((text or "").strip().split())
    if not clean:
        return "Новый чат"
    return clean if len(clean) <= limit else clean[: limit - 1].rstrip() + "…"


def _get_chat_sessions(user_id: str) -> List[Dict[str, Any]]:
    rows = db.list_bot_settings_by_prefix(f"{WEB_CHAT_SESSION_PREFIX}{user_id}:")
    sessions = []
    for row in rows:
        try:
            value = row.get("value")
            session = json.loads(value) if isinstance(value, str) else value
            if session:
                sessions.append(session)
        except Exception:
            continue
    sessions.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return sessions


def _get_chat_session(user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get chat session by user_id and session_id.
    Returns None if session doesn't exist or doesn't belong to the user.
    """
    session = db.get_bot_setting(_make_chat_session_key(user_id, session_id), default=None, parse_json=True)
    # Additional security check: ensure session belongs to the user
    if session and session.get("user_id") != user_id:
        logger.warning(
            f"Security violation: User {user_id} tried to access session {session_id} "
            f"belonging to {session.get('user_id')}"
        )
        return None
    return session


def _get_chat_messages(session_id: str) -> List[Dict[str, Any]]:
    return db.get_bot_setting(_make_chat_messages_key(session_id), default=[], parse_json=True) or []


def _save_chat_session(user_id: str, session: Dict[str, Any]) -> None:
    db.set_bot_setting(_make_chat_session_key(user_id, session["session_id"]), session)


def _save_chat_messages(session_id: str, messages: List[Dict[str, Any]]) -> None:
    db.set_bot_setting(_make_chat_messages_key(session_id), messages[-100:])


def _delete_chat_session(user_id: str, session_id: str) -> bool:
    removed_session = db.delete_bot_setting(_make_chat_session_key(user_id, session_id))
    removed_messages = db.delete_bot_setting(_make_chat_messages_key(session_id))
    return removed_session or removed_messages


def _get_web_notifications(user_id: str) -> List[Dict[str, Any]]:
    return db.get_bot_setting(_make_web_notification_key(user_id), default=[], parse_json=True) or []


def _push_web_notification(user_id: str, title: str, message: str, tone: str = "info") -> None:
    notifications = _get_web_notifications(user_id)
    notifications.append({
        "id": uuid.uuid4().hex,
        "title": title,
        "message": message,
        "tone": tone,
        "created_at": get_moscow_now().isoformat(),
    })
    db.set_bot_setting(_make_web_notification_key(user_id), notifications[-20:])


def _pop_web_notifications(user_id: str) -> List[Dict[str, Any]]:
    notifications = _get_web_notifications(user_id)
    db.delete_bot_setting(_make_web_notification_key(user_id))
    return notifications


async def _notify_user_change(
    user_id: str,
    *,
    web_title: str,
    web_message: str,
    telegram_text: str,
    tone: str = "info",
) -> None:
    try:
        _push_web_notification(user_id, web_title, web_message, tone=tone)
    except Exception as exc:
        logger.warning(f"Не удалось сохранить web-уведомление для {user_id}: {exc}")

    try:
        await send_telegram_message(user_id, telegram_text, parse_mode="Markdown")
    except Exception as exc:
        logger.warning(f"Не удалось отправить Telegram-уведомление пользователю {user_id}: {exc}")


def _create_chat_session(user_id: str, assistant_mode: str = "assistant", model_key: str = "groq-gpt-oss") -> Dict[str, Any]:
    now = get_moscow_now().isoformat()
    session = {
        "session_id": uuid.uuid4().hex,
        "user_id": user_id,
        "title": "Новый чат",
        "assistant_mode": assistant_mode,
        "model_key": model_key,
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
        "preview": "",
    }
    _save_chat_session(user_id, session)
    _save_chat_messages(session["session_id"], [])
    return session


def _ensure_default_chat_session(user_id: str) -> Dict[str, Any]:
    sessions = _get_chat_sessions(user_id)
    if sessions:
        return sessions[0]

    history = db.get_dialog_history(user_id, limit=20) or []
    if history:
        session = _create_chat_session(user_id)
        normalized = []
        first_user_message = None
        for item in history:
            role = item.get("role")
            content = item.get("content")
            if role not in {"user", "assistant"} or not content:
                continue
            if role == "user" and not first_user_message:
                first_user_message = content
            normalized.append({
                "role": role,
                "content": content,
                "created_at": item.get("created_at") or get_moscow_now().isoformat(),
                "model": item.get("model") or "LiraAI",
            })

        if normalized:
            session["title"] = _short_title(first_user_message or "Импортированный чат")
            session["preview"] = _short_title(first_user_message or "Импортированный чат", 58)
            session["message_count"] = len(normalized)
            session["updated_at"] = normalized[-1]["created_at"]
            _save_chat_session(user_id, session)
            _save_chat_messages(session["session_id"], normalized)
            return session

    return _create_chat_session(user_id)


def _verify_telegram_auth(data: Dict[str, Any]) -> bool:
    check_hash = data.get("hash")
    if not check_hash:
        return False

    auth_pairs = []
    for key in sorted(k for k in data.keys() if k != "hash" and data.get(k) is not None):
        auth_pairs.append(f"{key}={data[key]}")
    data_check_string = "\n".join(auth_pairs)

    secret_key = hashlib.sha256(os.getenv("TELEGRAM_BOT_TOKEN", "").encode("utf-8")).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, check_hash):
        return False

    auth_date = int(data.get("auth_date", 0))
    return abs(int(time.time()) - auth_date) <= 86400


def _build_session_payload(user_id: str, access_level: str) -> Dict[str, Any]:
    now = int(time.time())
    return {
        "user_id": user_id,
        "access_level": access_level,
        "iat": now,
        "exp": now + WEB_SESSION_TTL,
    }


def _get_session_user(request: Request, require_admin: bool = False) -> Dict[str, Any]:
    token = request.cookies.get(WEB_SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    session = _decode_session(token)
    stats = db.get_user_stats(session["user_id"])
    if not stats:
        raise HTTPException(status_code=401, detail="User not found")

    session["access_level"] = stats.get("access_level", "user")
    session["profile"] = stats

    if require_admin and session["access_level"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return session


def _build_level_distribution(users: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter(user.get("access_level", "user") for user in users)
    return {
        "admin": counts.get("admin", 0),
        "sub+": counts.get("sub+", 0),
        "subscriber": counts.get("subscriber", 0),
        "user": counts.get("user", 0),
    }


def _build_activity_chart(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = get_moscow_now()
    buckets = []
    for days_ago in range(6, -1, -1):
        day = (now.date()).fromordinal(now.date().toordinal() - days_ago)
        buckets.append({"date": day.isoformat(), "label": day.strftime("%d.%m"), "users": 0})

    bucket_map = {bucket["date"]: bucket for bucket in buckets}
    for user in users:
        last_seen = user.get("last_seen")
        if not last_seen:
            continue
        try:
            normalized = str(last_seen).split("T")[0]
            if normalized in bucket_map:
                bucket_map[normalized]["users"] += 1
        except Exception:
            continue
    return buckets


def _build_generation_chart() -> List[Dict[str, Any]]:
    if USE_SUPABASE and supabase:
        chart = []
        now = get_moscow_now()
        for days_ago in range(6, -1, -1):
            day = (now.date()).fromordinal(now.date().toordinal() - days_ago).isoformat()
            try:
                result = supabase.table("generation_history").select("id").gte("created_at", f"{day}T00:00:00+03:00").lt("created_at", f"{day}T23:59:59+03:00").execute()
                count = len(result.data or [])
            except Exception:
                count = 0
            chart.append({"date": day, "label": day[5:], "count": count})
        return chart
    return []


@router.get("/web", response_class=HTMLResponse)
async def web_landing(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "bot_username": _telegram_bot_username(),
            "is_dev_mode": os.getenv("DEV_MODE", "false").lower() == "true",
            "default_dev_user_id": os.getenv("ADMIN_USER_ID", ""),
            "show_telegram_widget": _should_show_telegram_widget(request),
            "hero_image_url": _landing_hero_image_url(),
        },
    )


@router.get("/web/app", response_class=HTMLResponse)
async def web_app(request: Request):
    try:
        session = _get_session_user(request)
    except HTTPException:
        return RedirectResponse("/web", status_code=302)

    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "profile": session["profile"],
            "bot_username": _telegram_bot_username(),
            "models": WEB_MODELS,
            "is_admin": session["access_level"] == "admin",
        },
    )


@router.get("/web/admin", response_class=HTMLResponse)
async def web_admin(request: Request):
    try:
        session = _get_session_user(request, require_admin=True)
    except HTTPException:
        return RedirectResponse("/web/app", status_code=302)

    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "profile": session["profile"],
            "bot_username": _telegram_bot_username(),
            "models": WEB_MODELS,
            "is_admin": True,
        },
    )


@router.post("/api/web/auth/telegram")
async def web_auth_telegram(request: Request, payload: TelegramAuthRequest):
    # Rate limiting: 5 attempts per minute per client
    client_id = _get_client_identifier(request)
    _check_rate_limit(client_id, RATE_LIMIT_AUTH_MAX_ATTEMPTS, RATE_LIMIT_AUTH_WINDOW)
    
    auth_data = payload.model_dump()
    if not _verify_telegram_auth(auth_data):
        raise HTTPException(status_code=401, detail="Telegram auth verification failed")

    user_id = str(payload.id)
    db.add_or_update_user(
        user_id=user_id,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    access_level = db.get_user_access_level(user_id)
    session_token = _encode_session(_build_session_payload(user_id, access_level))
    stats = db.get_user_stats(user_id) or {"user_id": user_id, "access_level": access_level}

    response = JSONResponse(
        {
            "ok": True,
            "user": stats,
            "redirect": "/web/admin" if access_level == "admin" else "/web/app",
        }
    )
    response.set_cookie(
        WEB_SESSION_COOKIE,
        session_token,
        max_age=WEB_SESSION_TTL,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return response


@router.get("/api/web/auth/session")
async def web_auth_session(request: Request):
    session = _get_session_user(request)
    return {
        "ok": True,
        "user": session["profile"],
        "is_admin": session["access_level"] == "admin",
    }


@router.get("/api/web/notifications")
async def web_notifications(request: Request):
    session = _get_session_user(request)
    return {
        "ok": True,
        "notifications": _pop_web_notifications(session["user_id"]),
    }


@router.post("/api/web/auth/logout")
async def web_auth_logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(WEB_SESSION_COOKIE)
    return response


@router.post("/api/web/auth/dev-login")
async def web_auth_dev_login(request: Request, payload: DevLoginRequest):
    if os.getenv("DEV_MODE", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Dev login is disabled")

    # Rate limiting: 3 attempts per 5 minutes per client (stricter for dev login)
    client_id = _get_client_identifier(request)
    _check_rate_limit(client_id, RATE_LIMIT_DEV_LOGIN_MAX_ATTEMPTS, RATE_LIMIT_DEV_LOGIN_WINDOW)

    user_id = str(payload.user_id or os.getenv("ADMIN_USER_ID", "")).strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required for dev login")

    db.add_or_update_user(user_id=user_id, first_name="Dev")
    access_level = db.get_user_access_level(user_id)
    session_token = _encode_session(_build_session_payload(user_id, access_level))
    stats = db.get_user_stats(user_id) or {"user_id": user_id, "access_level": access_level}

    response = JSONResponse(
        {
            "ok": True,
            "user": stats,
            "redirect": "/web/admin" if access_level == "admin" else "/web/app",
        }
    )
    response.set_cookie(
        WEB_SESSION_COOKIE,
        session_token,
        max_age=WEB_SESSION_TTL,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return response


@router.get("/api/web/dashboard/summary")
async def web_dashboard_summary(request: Request):
    session = _get_session_user(request)
    profile = session["profile"]
    level = profile.get("access_level", "user")
    daily_limit = ACCESS_LEVELS.get(level, ACCESS_LEVELS["user"])["daily_limit"]
    daily_limit_display = "∞" if daily_limit == -1 else daily_limit

    recent_history = db.get_dialog_history(profile["user_id"], limit=10) or []
    recent_messages = [
        {
            "role": item.get("role"),
            "content": (item.get("content") or "")[:180],
            "created_at": item.get("created_at"),
            "model": item.get("model"),
        }
        for item in recent_history
    ]

    return {
        "profile": profile,
        "limits": {
            "daily_limit": daily_limit_display,
            "today_generations": profile.get("today_generations", 0),
            "total_generations": profile.get("total_count", 0),
            "messages_today": profile.get("messages_today", 0),
        },
        "recent_messages": recent_messages,
        "models": WEB_MODELS,
    }


@router.get("/api/web/chat/sessions")
async def web_chat_sessions(request: Request):
    session = _get_session_user(request)
    sessions = _get_chat_sessions(session["user_id"])
    if not sessions:
        sessions = [_ensure_default_chat_session(session["user_id"])]
    return {"sessions": sessions}


@router.post("/api/web/chat/sessions")
async def web_create_chat_session(request: Request, payload: WebChatSessionCreateRequest):
    session = _get_session_user(request)
    created = _create_chat_session(
        session["user_id"],
        assistant_mode=payload.assistant_mode,
        model_key=payload.model_key,
    )
    return {"ok": True, "session": created}


@router.get("/api/web/chat/sessions/{session_id}")
async def web_get_chat_session(request: Request, session_id: str):
    session = _get_session_user(request)
    chat_session = _get_chat_session(session["user_id"], session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Security check: ensure messages belong to the same user's session
    messages = _get_chat_messages(session_id)
    return {
        "session": chat_session,
        "messages": messages,
    }


@router.delete("/api/web/chat/sessions/{session_id}")
async def web_delete_chat_session(request: Request, session_id: str):
    session = _get_session_user(request)
    chat_session = _get_chat_session(session["user_id"], session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    _delete_chat_session(session["user_id"], session_id)
    remaining = _get_chat_sessions(session["user_id"])
    next_session_id = remaining[0]["session_id"] if remaining else None
    return {
        "ok": True,
        "deleted_session_id": session_id,
        "next_session_id": next_session_id,
        "sessions": remaining,
    }


@router.post("/api/web/chat/sessions/{session_id}/delete")
async def web_delete_chat_session_post(request: Request, session_id: str):
    return await web_delete_chat_session(request, session_id)


@router.post("/api/web/chat")
async def web_chat(request: Request, payload: WebChatRequest):
    session = _get_session_user(request)
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    model_key = payload.model_key if payload.model_key in WEB_MODELS else "groq-gpt-oss"
    model_info = WEB_MODELS.get(model_key, WEB_MODELS["groq-gpt-oss"])
    assistant_mode = payload.assistant_mode if payload.assistant_mode in {"assistant", "lira-4d"} else "assistant"

    chat_session = None
    if payload.session_id:
        chat_session = _get_chat_session(session["user_id"], payload.session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        # Extra security: verify session ownership matches authenticated user
        if chat_session.get("user_id") != session["user_id"]:
            logger.warning(
                f"Security violation: User {session['user_id']} tried to access "
                f"session {payload.session_id} belonging to {chat_session.get('user_id')}"
            )
            raise HTTPException(status_code=403, detail="Access denied to this chat session")
    else:
        chat_session = _create_chat_session(session["user_id"], assistant_mode=assistant_mode, model_key=model_key)

    messages = _get_chat_messages(chat_session["session_id"])
    chat_history = []
    for item in messages[-16:]:
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and content:
            chat_history.append({"role": role, "content": content})

    if assistant_mode == "lira-4d":
        system_prompt = _load_lira_4d_prompt()
    else:
        system_prompt = _load_web_assistant_prompt()

    if model_info["provider"] == "groq":
        client = groq_client
    elif model_info["provider"] == "cerebras":
        client = cerebras_client
    else:
        client = openrouter_client
    answer = await client.chat_completion(
        user_message=payload.message,
        system_prompt=system_prompt,
        chat_history=chat_history,
        model=model_info["model"],
        temperature=0.7,
        max_tokens=1024,
    )

    db.save_dialog_message(session["user_id"], "user", payload.message, model=model_info["model"])
    db.save_dialog_message(session["user_id"], "assistant", answer, model=model_info["model"])

    now = get_moscow_now().isoformat()
    messages.extend([
        {
            "role": "user",
            "content": payload.message,
            "created_at": now,
            "model": model_info["label"],
        },
        {
            "role": "assistant",
            "content": answer,
            "created_at": get_moscow_now().isoformat(),
            "model": model_info["label"],
        },
    ])
    _save_chat_messages(chat_session["session_id"], messages)

    chat_session["assistant_mode"] = assistant_mode
    chat_session["model_key"] = model_key
    chat_session["updated_at"] = get_moscow_now().isoformat()
    chat_session["message_count"] = len(messages)
    chat_session["preview"] = _short_title(payload.message, 58)
    if chat_session.get("title") in (None, "", "Новый чат"):
        chat_session["title"] = _short_title(payload.message)
    _save_chat_session(session["user_id"], chat_session)

    return {
        "ok": True,
        "answer": answer,
        "model": model_info["label"],
        "session_id": chat_session["session_id"],
        "session": chat_session,
        "messages": messages,
    }


@router.post("/api/web/image/generate")
async def web_generate_image(request: Request, payload: WebChatRequest):
    session = _get_session_user(request)
    image_data = await image_generator.generate_image(payload.message)
    if not image_data:
        raise HTTPException(status_code=502, detail="Image generation failed")

    db.increment_generation_count(session["user_id"], payload.message)
    image_b64 = base64.b64encode(image_data).decode("utf-8")
    return {"ok": True, "image_base64": image_b64, "mime_type": "image/png"}


@router.post("/api/web/vision/analyze")
async def web_analyze_image(request: Request, file: UploadFile = File(...)):
    session = _get_session_user(request)
    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    temp_path = TEMP_UPLOAD_DIR / f"vision_{session['user_id']}_{int(time.time())}{suffix}"
    content = await file.read()
    temp_path.write_bytes(content)

    try:
        description = await image_analyzer.analyze_image(str(temp_path))
        return {"ok": True, "description": description}
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass


@router.post("/api/web/voice/transcribe")
async def web_transcribe_voice(request: Request, file: UploadFile = File(...)):
    session = _get_session_user(request)
    suffix = Path(file.filename or "voice.ogg").suffix or ".ogg"
    temp_path = TEMP_UPLOAD_DIR / f"voice_{session['user_id']}_{int(time.time())}{suffix}"
    temp_path.write_bytes(await file.read())

    try:
        text = await stt_engine.speech_to_text(str(temp_path), language="ru")
        if not text:
            raise HTTPException(status_code=502, detail="Voice transcription failed")
        return {"ok": True, "text": text}
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass


@router.get("/api/web/admin/overview")
async def web_admin_overview(request: Request):
    _get_session_user(request, require_admin=True)
    users = db.get_all_users()
    total_users = len(users)
    active_today = sum(1 for user in users if (user.get("today_generations") or 0) > 0 or str(user.get("last_seen", "")).startswith(get_moscow_now().date().isoformat()))
    banned_users = sum(1 for user in users if user.get("is_banned"))

    audit_logs = db.get_admin_audit_log(limit=20)
    level_distribution = _build_level_distribution(users)
    generation_chart = _build_generation_chart()
    activity_chart = _build_activity_chart(users)

    payment_stats = {"pending": 0, "paid": 0}
    if USE_SUPABASE and supabase:
        try:
            pending = supabase.table("payments").select("payment_id").eq("status", "pending").execute()
            paid = supabase.table("payments").select("payment_id").eq("status", "paid").execute()
            payment_stats["pending"] = len(pending.data or [])
            payment_stats["paid"] = len(paid.data or [])
        except Exception as exc:
            logger.warning(f"Не удалось собрать payment stats: {exc}")

    return {
        "summary": {
            "total_users": total_users,
            "active_today": active_today,
            "banned_users": banned_users,
            "pending_payments": payment_stats["pending"],
            "paid_payments": payment_stats["paid"],
        },
        "level_distribution": level_distribution,
        "generation_chart": generation_chart,
        "activity_chart": activity_chart,
        "recent_audit": audit_logs[:10],
    }


@router.get("/api/web/admin/users")
async def web_admin_users(request: Request):
    _get_session_user(request, require_admin=True)
    users = db.get_all_users()
    users_sorted = sorted(
        users,
        key=lambda item: (
            {"admin": 0, "sub+": 1, "subscriber": 2, "user": 3}.get(item.get("access_level", "user"), 9),
            -(item.get("today_generations", 0) or 0),
            -(item.get("total_count", 0) or 0),
        ),
    )
    return {"users": users_sorted}


@router.get("/api/web/admin/audit")
async def web_admin_audit(request: Request):
    _get_session_user(request, require_admin=True)
    return {"logs": db.get_admin_audit_log(limit=50)}


class AdminLevelRequest(BaseModel):
    access_level: str


class AdminBanRequest(BaseModel):
    days: Optional[int] = None
    permanent: bool = False


@router.post("/api/web/admin/users/{target_user_id}/level")
async def web_admin_set_level(request: Request, target_user_id: str, payload: AdminLevelRequest):
    session = _get_session_user(request, require_admin=True)
    if payload.access_level not in ACCESS_LEVELS:
        raise HTTPException(status_code=400, detail="Unsupported access level")

    old_level = db.get_user_access_level(target_user_id)
    if not db.set_user_access_level(target_user_id, payload.access_level):
        raise HTTPException(status_code=500, detail="Failed to update user level")

    db.log_admin_action(
        admin_user_id=session["user_id"],
        admin_username=session["profile"].get("username") or session["profile"].get("first_name") or "web-admin",
        action_type="web_set_level",
        target_user_id=target_user_id,
        old_value=old_level,
        new_value=payload.access_level,
        details={"source": "web"},
        success=True,
    )

    level_labels = {
        "admin": "Администратор",
        "sub+": "sub+",
        "subscriber": "subscriber",
        "user": "user",
    }
    await _notify_user_change(
        target_user_id,
        web_title="Уровень доступа обновлён",
        web_message=f"Твой доступ изменён: {level_labels.get(old_level, old_level)} -> {level_labels.get(payload.access_level, payload.access_level)}.",
        telegram_text=(
            f"🔔 *LiraAI Web*\n\n"
            f"Твой уровень доступа изменён.\n"
            f"Было: *{level_labels.get(old_level, old_level)}*\n"
            f"Стало: *{level_labels.get(payload.access_level, payload.access_level)}*"
        ),
        tone="success",
    )
    return {
        "ok": True,
        "message": f"Уровень пользователя {target_user_id} изменён на {payload.access_level}.",
    }


@router.post("/api/web/admin/users/{target_user_id}/ban")
async def web_admin_ban_user(request: Request, target_user_id: str, payload: AdminBanRequest):
    session = _get_session_user(request, require_admin=True)
    until_time = None
    days = None
    if not payload.permanent:
        days = max(payload.days or 1, 1)
        until_time = (get_moscow_now() + timedelta(days=days)).isoformat()
    if not db.set_user_ban(target_user_id, until_time=until_time, reason="web-admin-ban"):
        raise HTTPException(status_code=500, detail="Failed to ban user")

    db.log_admin_action(
        admin_user_id=session["user_id"],
        admin_username=session["profile"].get("username") or session["profile"].get("first_name") or "web-admin",
        action_type="web_ban_user",
        target_user_id=target_user_id,
        details={"source": "web", "permanent": payload.permanent, "days": payload.days},
        success=True,
    )
    await _notify_user_change(
        target_user_id,
        web_title="Доступ ограничен",
        web_message="Твой аккаунт временно ограничен." if not payload.permanent else "Твой аккаунт заблокирован без срока.",
        telegram_text=(
            "⛔ *Доступ к LiraAI ограничен*\n\n"
            + ("Блокировка: *без срока*." if payload.permanent else f"Блокировка: *{days} дн.*.")
        ),
        tone="error",
    )
    return {
        "ok": True,
        "message": (
            f"Пользователь {target_user_id} заблокирован без срока."
            if payload.permanent
            else f"Пользователь {target_user_id} заблокирован на {days} дн."
        ),
    }


@router.post("/api/web/admin/users/{target_user_id}/unban")
async def web_admin_unban_user(request: Request, target_user_id: str):
    session = _get_session_user(request, require_admin=True)
    if not db.remove_user_ban(target_user_id):
        raise HTTPException(status_code=500, detail="Failed to unban user")

    db.log_admin_action(
        admin_user_id=session["user_id"],
        admin_username=session["profile"].get("username") or session["profile"].get("first_name") or "web-admin",
        action_type="web_unban_user",
        target_user_id=target_user_id,
        details={"source": "web"},
        success=True,
    )
    await _notify_user_change(
        target_user_id,
        web_title="Доступ восстановлен",
        web_message="Блокировка снята. Можно снова пользоваться LiraAI.",
        telegram_text="✅ *Блокировка снята.*\n\nМожно снова пользоваться LiraAI.",
        tone="success",
    )
    return {
        "ok": True,
        "message": f"Блокировка пользователя {target_user_id} снята.",
    }
