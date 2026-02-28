"""
Обработчик генерации изображений через Gemini Image API.
Используется в telegram_polling.py
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger("bot.image_gen")


async def generate_image_with_gemini(
    chat_id: str,
    user_id: str,
    prompt: str,
    gemini_image_client,
    llm_client,
    temp_dir: Path,
    send_telegram_message,
    send_telegram_photo,
    get_database
):
    """
    Генерирует изображение через Gemini Image API с проверкой лимитов и уровней доступа
    
    Args:
        chat_id: ID чата
        user_id: ID пользователя
        prompt: Описание изображения
        gemini_image_client: Клиент Gemini Image
        llm_client: Клиент LLM для перевода
        temp_dir: Директория для временных файлов
        send_telegram_message: Функция отправки сообщений
        send_telegram_photo: Функция отправки фото
        get_database: Функция получения БД
    """
    try:
        logger.info(f"🎨 Генерация изображения для пользователя {user_id}: {prompt}")

        # Проверяем лимиты и уровень доступа
        db = get_database()
        db.add_or_update_user(user_id)
        
        # Получаем уровень доступа
        access_level = db.get_user_access_level(user_id)
        
        # Проверяем лимиты
        limit_info = db.check_generation_limit(user_id)

        if not limit_info["allowed"]:
            await send_telegram_message(
                chat_id,
                f"❌ Превышен дневной лимит генерации изображений.\n\n"
                f"Использовано: {limit_info['daily_count']}/{limit_info['daily_limit']}\n"
                f"Всего: {limit_info['total_count']}\n\n"
                f"Лимит сбросится: {limit_info['reset_time']}"
            )
            return

        # Получаем модель пользователя (или дефолтную для уровня)
        from telegram_polling import user_image_models
        model_key = user_image_models.get(user_id)
        
        # Проверяем доступность модели для уровня доступа
        available_models = gemini_image_client.get_models_for_user(access_level)
        
        if not model_key or model_key not in available_models:
            # Используем дефолтную модель для уровня
            model_key = list(available_models.keys())[0] if available_models else "imagen-4.0-generate"
            user_image_models[user_id] = model_key
        
        model_info = available_models.get(model_key, {})
        model_name = model_info.get("description", model_key)

        # Информируем о лимитах
        if limit_info['daily_limit'] == -1:
            limit_text = "📊 Доступно генераций: **Безлимит** (администратор)"
        else:
            available = limit_info['daily_limit'] - limit_info['daily_count']
            limit_text = f"📊 Доступно генераций: {available}/{limit_info['daily_limit']}"

        await send_telegram_message(
            chat_id,
            f"🎨 Генерирую изображение...\n\n"
            f"📊 Модель: **{model_name}**\n"
            f"{limit_text}\n"
            f"Всего использовано: {limit_info['total_count']}\n\n"
            f"Подождите немного, это займет 10-30 секунд."
        )

        # Переводим промпт на английский через LLM
        translated = prompt
        try:
            translate_prompt = f"Translate to English ONLY, no other text: '{prompt}'"
            translated = await llm_client.chat_completion(
                user_message=translate_prompt,
                system_prompt="Translate image descriptions to English. Return ONLY the translation, nothing else.",
                model="upstage/solar-pro-3:free",
                max_tokens=100,
                temperature=0.1
            )
            translated = translated.strip().strip('"\'').strip()
            if not translated or len(translated) < 3:
                translated = prompt
            logger.info(f"🎨 Оригинал: {prompt} → Перевод: {translated}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка перевода: {e}, используем оригинал")
            translated = prompt

        # Улучшаем промпт
        enhanced_prompt = f"{translated}, high quality, detailed, artistic, professional photography, 8k, masterpiece"

        # Генерация через Gemini Image API
        try:
            image_data = await gemini_image_client.generate_image(
                prompt=enhanced_prompt,
                model_key=model_key,
                timeout=90
            )

            if image_data and len(image_data) > 10000:
                logger.info(f"✅ Gemini Image успешно: {len(image_data)} байт")

                image_path = temp_dir / f"generated_{os.getpid()}.png"
                with open(image_path, "wb") as f:
                    f.write(image_data)

                await send_telegram_photo(
                    chat_id, 
                    str(image_path), 
                    caption=f"🎨 {prompt}\n\n📊 Модель: {model_name}\n👤 Уровень: {access_level}"
                )

                # Сохраняем в БД
                db.increment_generation_count(user_id, prompt)

                try:
                    os.remove(image_path)
                except:
                    pass
                return
            else:
                logger.warning(f"⚠️ Gemini вернул пустое изображение")

        except Exception as e:
            logger.error(f"❌ Ошибка Gemini Image: {e}", exc_info=True)
            await send_telegram_message(
                chat_id,
                f"❌ **Ошибка генерации**\n\n"
                f"Не удалось создать изображение.\n\n"
                f"Попробуйте:\n"
                f"1. Другое описание\n"
                f"2. Другую модель (/menu → Генерация)\n"
                f"3. Позже"
            )
            return

        await send_telegram_message(
            chat_id,
            "❌ Не удалось сгенерировать изображение.\n\nПопробуйте позже или другое описание."
        )

    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}", exc_info=True)
        await send_telegram_message(chat_id, f"❌ Ошибка: {str(e)}")
