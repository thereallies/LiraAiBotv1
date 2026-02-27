#!/usr/bin/env python3
"""
Скрипт для парсинга диалога с Антонина Лебединска:
1. Находит диалог по имени
2. Парсит все сообщения
3. Скачивает и распознает голосовые сообщения через STT
4. Суммаризирует разговор через LLM
"""
import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaVoice, MessageMediaAudio, MessageMediaDocument

# Импортируем STT и LLM из проекта
from backend.voice.stt import SpeechToText
from backend.llm.openrouter import OpenRouterClient
from backend.config import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger("parse_dialog")

# Загружаем переменные окружения
load_dotenv()

# Настройки Telegram
TG_API_ID = int(os.getenv("TG_API_ID", "24120142"))
TG_API_HASH = os.getenv("TG_API_HASH", "5792c2ada7d1f4d1d3f91938a5caa7a7")
SESSION_FILE = os.getenv("SESSION_FILE", ".session_antonina")

# Создаем директории
OUTPUT_DIR = Path(__file__).parent / "data" / "antonina_dialog"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_AUDIO_DIR = Path(__file__).parent / "temp" / "antonina_audio"
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class DialogParser:
    """Парсер диалога с распознаванием голоса и суммаризацией"""
    
    def __init__(self):
        self.client = TelegramClient(SESSION_FILE, TG_API_ID, TG_API_HASH)
        self.stt = SpeechToText()
        self.config = Config()
        self.llm_client = OpenRouterClient(self.config)
        self.messages_data = []
        
    async def find_dialog(self, search_name: str) -> Optional[Any]:
        """Находит диалог по имени"""
        try:
            logger.info(f"🔍 Ищем диалог с '{search_name}'...")
            dialogs = await self.client.get_dialogs(limit=None)
            
            for dialog in dialogs:
                name = dialog.name.lower()
                search_lower = search_name.lower()
                
                # Проверяем точное совпадение или частичное
                if search_lower in name or name in search_lower:
                    logger.info(f"✅ Найден диалог: {dialog.name} (ID: {dialog.id})")
                    return dialog
                
                # Также проверяем по имени пользователя
                if hasattr(dialog.entity, 'first_name') and dialog.entity.first_name:
                    if search_lower in dialog.entity.first_name.lower():
                        logger.info(f"✅ Найден диалог по имени: {dialog.name} (ID: {dialog.id})")
                        return dialog
            
            logger.warning(f"❌ Диалог с '{search_name}' не найден")
            logger.info("📋 Доступные диалоги (первые 20):")
            for i, dialog in enumerate(dialogs[:20]):
                logger.info(f"  {i+1}. {dialog.name}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска диалога: {e}")
            return None
    
    async def download_voice_message(self, message: Any, index: int) -> Optional[str]:
        """Скачивает голосовое сообщение"""
        try:
            if not (message.voice or message.audio):
                return None
            
            # Определяем расширение
            ext = ".ogg" if message.voice else ".mp3"
            audio_path = TEMP_AUDIO_DIR / f"voice_{index}{ext}"
            
            # Скачиваем файл
            await self.client.download_media(message, file=str(audio_path))
            logger.info(f"📥 Скачано голосовое сообщение {index}: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            logger.error(f"Ошибка скачивания голосового {index}: {e}")
            return None
    
    async def parse_dialog(self, dialog: Any, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Парсит все сообщения из диалога"""
        try:
            logger.info(f"📥 Парсим сообщения из диалога '{dialog.name}'...")
            
            messages_data = []
            voice_count = 0
            
            async for message in self.client.iter_messages(dialog, limit=limit):
                msg_data = {
                    "id": message.id,
                    "date": message.date.isoformat() if message.date else None,
                    "from_id": message.from_id.user_id if message.from_id else None,
                    "text": message.text or "",
                    "is_voice": bool(message.voice),
                    "is_audio": bool(message.audio),
                    "voice_text": None
                }
                
                # Если это голосовое сообщение - скачиваем и распознаем
                if message.voice or message.audio:
                    voice_count += 1
                    logger.info(f"🎤 Обрабатываю голосовое сообщение {voice_count}...")
                    
                    audio_path = await self.download_voice_message(message, message.id)
                    if audio_path:
                        try:
                            # Распознаем речь
                            voice_text = self.stt.speech_to_text(audio_path, language="ru")
                            msg_data["voice_text"] = voice_text
                            logger.info(f"✅ Распознано: {voice_text[:50]}...")
                            
                            # Удаляем временный файл
                            try:
                                os.remove(audio_path)
                            except:
                                pass
                                
                        except Exception as e:
                            logger.error(f"Ошибка распознавания голоса: {e}")
                
                messages_data.append(msg_data)
                
                if len(messages_data) % 50 == 0:
                    logger.info(f"📊 Обработано {len(messages_data)} сообщений...")
            
            logger.info(f"✅ Всего обработано {len(messages_data)} сообщений, из них {voice_count} голосовых")
            return messages_data
            
        except Exception as e:
            logger.error(f"Ошибка парсинга диалога: {e}")
            return []
    
    def save_messages(self, messages: List[Dict[str, Any]], dialog_name: str):
        """Сохраняет сообщения в файлы"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON файл
        json_path = OUTPUT_DIR / f"antonina_messages_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Сохранено в JSON: {json_path}")
        
        # Текстовый файл для чтения
        txt_path = OUTPUT_DIR / f"antonina_messages_{timestamp}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"=== ДИАЛОГ С {dialog_name.upper()} ===\n")
            f.write(f"Дата парсинга: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего сообщений: {len(messages)}\n\n")
            
            for msg in messages:
                f.write(f"\n--- Сообщение {msg['id']} ({msg['date']}) ---\n")
                if msg["text"]:
                    f.write(f"Текст: {msg['text']}\n")
                if msg["voice_text"]:
                    f.write(f"Голосовое: {msg['voice_text']}\n")
                if msg["is_voice"] or msg["is_audio"]:
                    f.write(f"[Голосовое сообщение]\n")
        
        logger.info(f"💾 Сохранено в TXT: {txt_path}")
        return json_path, txt_path
    
    async def summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Суммаризирует разговор через LLM"""
        try:
            logger.info("🤖 Суммаризирую разговор через LLM...")
            
            # Формируем текст разговора
            conversation_text = []
            for msg in messages:
                date = msg.get("date", "")
                text = msg.get("text", "")
                voice_text = msg.get("voice_text", "")
                
                if text:
                    conversation_text.append(f"[{date}] {text}")
                elif voice_text:
                    conversation_text.append(f"[{date}] [Голосовое] {voice_text}")
            
            full_conversation = "\n".join(conversation_text)
            
            # Ограничиваем размер (берем последние 8000 токенов примерно)
            if len(full_conversation) > 20000:
                full_conversation = "...\n" + full_conversation[-20000:]
            
            prompt = f"""Проанализируй следующий диалог и создай краткую суммаризацию:

{full_conversation}

Создай структурированную суммаризацию на русском языке, которая включает:
1. Основные темы разговора
2. Ключевые моменты и решения
3. Важные даты и события
4. Эмоциональный тон беседы
5. Выводы и итоги

Суммаризация должна быть информативной, но краткой (500-800 слов)."""
            
            summary = await self.llm_client.chat_completion(
                user_message=prompt,
                system_prompt="",
                temperature=0.7,
                max_tokens=2000
            )
            
            logger.info("✅ Суммаризация создана")
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка суммаризации: {e}")
            return f"Ошибка создания суммаризации: {e}"
    
    async def run(self, search_name: str = "Антонина Лебединска", limit: Optional[int] = None):
        """Главная функция"""
        try:
            logger.info("🚀 Запуск парсера диалога...")
            
            # Подключаемся к Telegram
            await self.client.start()
            logger.info("✅ Подключено к Telegram")
            
            # Находим диалог
            dialog = await self.find_dialog(search_name)
            if not dialog:
                logger.error("❌ Диалог не найден")
                return
            
            # Парсим сообщения
            messages = await self.parse_dialog(dialog, limit=limit)
            if not messages:
                logger.warning("⚠️ Сообщения не найдены")
                return
            
            # Сохраняем сообщения
            json_path, txt_path = self.save_messages(messages, dialog.name)
            
            # Суммаризируем
            summary = await self.summarize_conversation(messages)
            
            # Сохраняем суммаризацию
            summary_path = OUTPUT_DIR / f"antonina_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"=== СУММАРИЗАЦИЯ ДИАЛОГА С {dialog.name.upper()} ===\n\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Всего сообщений: {len(messages)}\n")
                f.write(f"Голосовых сообщений: {sum(1 for m in messages if m.get('is_voice') or m.get('is_audio'))}\n\n")
                f.write("=" * 80 + "\n\n")
                f.write(summary)
            
            logger.info(f"💾 Суммаризация сохранена: {summary_path}")
            
            # Выводим краткую информацию
            print("\n" + "=" * 80)
            print("✅ ПАРСИНГ ЗАВЕРШЕН")
            print("=" * 80)
            print(f"📊 Всего сообщений: {len(messages)}")
            print(f"🎤 Голосовых сообщений: {sum(1 for m in messages if m.get('is_voice') or m.get('is_audio'))}")
            print(f"📄 JSON файл: {json_path}")
            print(f"📄 TXT файл: {txt_path}")
            print(f"📝 Суммаризация: {summary_path}")
            print("\n" + "=" * 80)
            print("КРАТКАЯ СУММАРИЗАЦИЯ:")
            print("=" * 80)
            print(summary[:500] + "..." if len(summary) > 500 else summary)
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
        finally:
            await self.client.disconnect()
            logger.info("🔌 Отключено от Telegram")


async def main():
    parser = DialogParser()
    
    # Можно указать лимит сообщений (None = все)
    await parser.run(
        search_name="Антонина Лебединска",
        limit=None  # None = все сообщения, или укажите число
    )


if __name__ == "__main__":
    asyncio.run(main())


