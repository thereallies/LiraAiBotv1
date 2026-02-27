"""
Модуль с маршрутами API.
"""
import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.llm.openrouter import OpenRouterClient
from backend.config import Config

logger = logging.getLogger("bot.api")

# Создаем роутер
router = APIRouter()

# Инициализируем компоненты
config = Config()
llm_client = OpenRouterClient(config)

# Модели данных
class MessageRequest(BaseModel):
    """Модель запроса сообщения"""
    user_id: str
    message: str

class MessageResponse(BaseModel):
    """Модель ответа на сообщение"""
    message: str

class ImageGenerateRequest(BaseModel):
    """Модель запроса для генерации изображения"""
    prompt: str
    width: int = 512
    height: int = 512


@router.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """Обработка текстового сообщения"""
    try:
        response = await llm_client.chat_completion(
            user_message=request.message,
            system_prompt="",
            temperature=0.7
        )
        
        return MessageResponse(message=response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image/generate")
async def generate_image(request: ImageGenerateRequest):
    """Генерация изображения"""
    try:
        from backend.vision.image_generator import get_image_generator
        generator = get_image_generator()
        
        image_data = await generator.generate_image(
            prompt=request.prompt,
            width=request.width,
            height=request.height
        )
        
        if not image_data:
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать изображение")
        
        # Возвращаем изображение как bytes
        from fastapi.responses import Response
        return Response(content=image_data, media_type="image/png")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

