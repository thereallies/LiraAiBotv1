"""
Обновленная функция handle_image_generation с лимитами
"""
import aiohttp
import re
import os
from backend.database.users_db import get_database


async def handle_image_generation_new(chat_id: str, user_id: str, prompt: str, 
                                       send_telegram_message, send_telegram_photo, temp_dir):
    """Обрабатывает запрос на генерацию изображения с проверкой лимитов"""
    try:
        from backend.api.telegram_core import logger
        logger.info(f"🎨 Генерация изображения для пользователя {user_id}: {prompt}")
        
        # Проверяем лимиты
        db = get_database()
        
        # Добавляем/обновляем пользователя
        db.add_or_update_user(user_id)
        
        # Проверяем лимит генерации
        limit_info = db.check_generation_limit(user_id)
        
        if not limit_info["allowed"]:
            # Лимит превышен
            await send_telegram_message(
                chat_id,
                f"❌ Превышен дневной лимит генерации изображений.\n\n"
                f"Использовано: {limit_info['daily_count']}/{limit_info['daily_limit']}\n"
                f"Всего: {limit_info['total_count']}\n\n"
                f"Лимит сбросится: {limit_info['reset_time']}"
            )
            return
        
        await send_telegram_message(chat_id, "🎨 Генерирую изображение...\n\nПодождите немного, это займет 10-30 секунд.")

        # Простая транслитерация
        translit = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            ' ': ' ',
        }
        prompt_en = ''.join(translit.get(c, c) for c in prompt.lower())
        prompt_clean = re.sub(r'[^a-z ]', '', prompt_en).strip()[:50]
        if not prompt_clean:
            prompt_clean = 'beautiful landscape'

        # Генерация через Replicate
        replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
        
        if replicate_token:
            logger.info(f"🎨 Пробуем Replicate (Flux Dev): {prompt_clean}")
            
            try:
                from backend.vision.replicate import get_replicate_client
                
                replicate = get_replicate_client()
                image_data = await replicate.generate_image(
                    prompt=prompt_clean,
                    timeout=90
                )
                
                if image_data and len(image_data) > 10000:
                    logger.info(f"✅ Replicate успешно: {len(image_data)} байт")

                    image_path = temp_dir / f"generated_{os.getpid()}.png"
                    with open(image_path, "wb") as f:
                        f.write(image_data)

                    await send_telegram_photo(chat_id, str(image_path), caption=f"🎨 {prompt}\n\n🤖 Replicate (Flux Dev)")

                    # Увеличиваем счетчик
                    db.increment_generation_count(user_id, prompt)

                    try:
                        os.remove(image_path)
                    except:
                        pass
                    return
                    
            except Exception as e:
                logger.warning(f"⚠️ Replicate ошибка: {e}")
        
        # Fallback на Pollinations
        logger.info(f"🎨 Fallback на Pollinations: {prompt_clean}")
        url = f"https://image.pollinations.ai/prompt/{prompt_clean.replace(' ', '_')}"
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    image_data = await response.read()
                    
                    if len(image_data) > 10000:
                        image_path = temp_dir / f"generated_{os.getpid()}.png"
                        with open(image_path, "wb") as f:
                            f.write(image_data)

                        await send_telegram_photo(chat_id, str(image_path), caption=f"🎨 {prompt}\n\n🌸 Pollinations.ai")

                        db.increment_generation_count(user_id, prompt)

                        try:
                            os.remove(image_path)
                        except:
                            pass
                        return

        await send_telegram_message(chat_id, "❌ Не удалось сгенерировать изображение.\n\nПопробуйте позже или другое описание.")

    except Exception as e:
        from backend.api.telegram_core import logger
        logger.error(f"Ошибка при генерации изображения: {e}", exc_info=True)
        await send_telegram_message(chat_id, f"❌ Ошибка: {str(e)}")
