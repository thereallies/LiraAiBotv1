"""
Система диалога между ботами в группе.
Два бота общаются друг с другом как доброжелательные соседи.
"""
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger("bot.dialogue")

# Хранилище последних сообщений для отслеживания диалога
last_bot_message = {}  # bot_token -> {timestamp, text, chat_id}
dialogue_state = {}  # chat_id -> {last_speaker, last_message_time, conversation_history}


class BotDialogueManager:
    """Управляет диалогом между ботами (2 основных + 1 с веб-поиском)"""
    
    def __init__(self):
        self.bot_configs = {}  # bot_token -> {model, name, system_prompt}
        self.message_timeout = 180  # секунд между ответами (3 минуты)
        self.max_history = 15  # Максимум сообщений в истории (увеличено для лучшего контекста)
        self.third_bot_timeout = 180  # секунд - минимальный интервал для 3-го бота (3 минуты)
        
    def register_bot(self, bot_token: str, model: str, bot_name: str, system_prompt: str):
        """Регистрирует бота в системе диалога"""
        self.bot_configs[bot_token] = {
            "model": model,
            "name": bot_name,
            "system_prompt": system_prompt
        }
        logger.info(f"Зарегистрирован бот {bot_name} с моделью {model}")
    
    def get_other_bot_config(self, current_token: str) -> Optional[Dict]:
        """Получает конфигурацию первого другого бота (для обратной совместимости)"""
        for token, config in self.bot_configs.items():
            if token != current_token:
                return config
        return None
    
    def get_all_other_bots(self, current_token: str) -> List[Dict]:
        """Получает конфигурации всех других ботов"""
        others = []
        for token, config in self.bot_configs.items():
            if token != current_token:
                others.append({"token": token, **config})
        return others
    
    def get_third_bot_token(self) -> Optional[str]:
        """Получает токен 3-го бота (Perplexity) если он зарегистрирован"""
        for token, config in self.bot_configs.items():
            if "perplexity" in config.get("model", "").lower() or config.get("name", "").lower() == "перплексити":
                return token
        return None
    
    def should_respond(
        self,
        chat_id: str,
        message_text: str,
        sender_token: str,
        current_time: datetime,
        current_bot_token: str = None
    ) -> bool:
        """
        Определяет должен ли бот ответить на сообщение другого бота
        
        Args:
            chat_id: ID чата
            message_text: Текст сообщения
            sender_token: Токен бота который отправил сообщение
            current_time: Текущее время
            current_bot_token: Токен текущего бота (для которого проверяем)
            
        Returns:
            True если нужно ответить
        """
        # Инициализируем состояние диалога если нужно
        if chat_id not in dialogue_state:
            dialogue_state[chat_id] = {
                "last_speaker": None,
                "last_message_time": None,
                "conversation_history": []
            }
            logger.info(f"✅ Первое сообщение в чате {chat_id}, можно отвечать")
            return True  # Первое сообщение - отвечаем
        
        state = dialogue_state[chat_id]
        
        # Не отвечаем если последний говоривший - это мы сами
        if state["last_speaker"] == current_bot_token:
            logger.debug(f"⏸ Последний говоривший - я сам, не отвечаю")
            return False
        
        # Если последний говоривший - другой бот (отправитель), можем отвечать
        if state["last_speaker"] == sender_token:
            # Проверяем таймаут от последнего сообщения
            if state["last_message_time"]:
                time_diff = (current_time - state["last_message_time"]).total_seconds()
                if time_diff < self.message_timeout:
                    logger.info(f"⏳ Таймаут не прошел ({time_diff:.1f}s < {self.message_timeout}s), ждем...")
                    return False
            logger.info(f"✅ Таймаут прошел, отвечаю на сообщение от другого бота!")
            return True
        
        # Если последний говоривший НЕ отправитель, но и не мы - можем отвечать если прошло достаточно времени
        if state["last_speaker"] and state["last_speaker"] != current_bot_token:
            # Если последний говорил кто-то другой (не отправитель, не мы) - проверяем общий таймаут
            if state["last_message_time"]:
                time_diff = (current_time - state["last_message_time"]).total_seconds()
                # Если прошло достаточно времени (больше 80% таймаута) - можем вступить в разговор
                if time_diff < (self.message_timeout * 0.8):  # 80% от таймаута
                    logger.info(f"⏳ Недостаточно времени с последнего сообщения ({time_diff:.1f}s)")
                    return False
        
        # Если никто еще не говорил или говорил кто-то другой - отвечаем
        logger.info(f"✅ Условия для ответа выполнены")
        return True
    
    def update_dialogue_state(
        self,
        chat_id: str,
        bot_token: str,
        message_text: str,
        current_time: datetime
    ):
        """Обновляет состояние диалога после отправки сообщения"""
        if chat_id not in dialogue_state:
            dialogue_state[chat_id] = {
                "last_speaker": None,
                "last_message_time": None,
                "conversation_history": []
            }
        
        state = dialogue_state[chat_id]
        state["last_speaker"] = bot_token
        state["last_message_time"] = current_time
        
        # Добавляем в историю
        bot_name = self.bot_configs.get(bot_token, {}).get("name", "Бот")
        state["conversation_history"].append({
            "speaker": bot_name,
            "text": message_text,
            "time": current_time.isoformat()
        })
        
        # Ограничиваем историю
        if len(state["conversation_history"]) > self.max_history:
            state["conversation_history"] = state["conversation_history"][-self.max_history:]
    
    def build_conversation_context(self, chat_id: str, other_bot_name: str) -> str:
        """Строит контекст разговора для промпта"""
        if chat_id not in dialogue_state:
            return ""
        
        state = dialogue_state[chat_id]
        history = state.get("conversation_history", [])
        
        if not history:
            return ""
        
        # Формируем последние 8-10 сообщений для лучшего контекста
        recent = history[-10:] if len(history) > 10 else history
        context_lines = []
        
        # Добавляем инструкцию для избежания повторений
        if len(recent) > 3:
            context_lines.append("ВНИМАНИЕ: Проанализируй историю диалога выше. Твой ответ должен:")
            context_lines.append("- Развивать тему, а не повторять предыдущие мысли")
            context_lines.append("- Добавлять новую информацию или задавать новые вопросы")
            context_lines.append("- Избегать простых приветствий, если они уже были")
            context_lines.append("")
            context_lines.append("История диалога:")
        
        for msg in recent:
            context_lines.append(f"{msg['speaker']}: {msg['text']}")
        
        return "\n".join(context_lines)
    
    def detect_looping(self, chat_id: str, min_similarity: float = 0.7) -> bool:
        """Определяет зациклился ли диалог на основе похожести последних сообщений"""
        if chat_id not in dialogue_state:
            return False
        
        state = dialogue_state[chat_id]
        history = state.get("conversation_history", [])
        
        if len(history) < 3:
            return False
        
        # Берем последние 3-4 сообщения
        recent_messages = [msg['text'].lower().strip() for msg in history[-4:]]
        
        # Простая проверка на повторения
        unique_messages = set(recent_messages)
        if len(unique_messages) < 2:  # Все сообщения одинаковые
            logger.warning(f"🔁 Обнаружено зацикливание: все последние сообщения идентичны")
            return True
        
        # Проверка на очень похожие сообщения (начинаются одинаково)
        if len(recent_messages) >= 2:
            first_words = [msg.split()[0:3] for msg in recent_messages if msg.split()]
            if len(set(' '.join(words) for words in first_words)) < 2:
                logger.warning(f"🔁 Обнаружено зацикливание: сообщения начинаются одинаково")
                return True
        
        return False
    
    def extract_topics(self, chat_id: str) -> List[str]:
        """Извлекает темы из истории диалога для предложения новых направлений"""
        if chat_id not in dialogue_state:
            return []
        
        state = dialogue_state[chat_id]
        history = state.get("conversation_history", [])
        
        if not history:
            return []
        
        # Ключевые слова для определения тем
        topic_keywords = {
            "технологии": ["искусственный интеллект", "ai", "технологи", "компьютер", "программирование"],
            "наука": ["наука", "исследование", "открытие", "ученый"],
            "новости": ["новость", "событие", "происшествие", "информация"],
            "развлечения": ["фильм", "музыка", "игра", "хобби"],
            "философия": ["смысл", "жизнь", "сознание", "бытие", "философия"],
        }
        
        topics = []
        recent_text = " ".join([msg['text'].lower() for msg in history[-5:]])
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in recent_text for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def should_third_bot_intervene(
        self, 
        chat_id: str, 
        current_time: datetime,
        min_messages_before: int = 2
    ) -> bool:
        """Определяет должен ли 3-й бот вмешаться в диалог"""
        third_bot_token = self.get_third_bot_token()
        if not third_bot_token:
            return False
        
        if chat_id not in dialogue_state:
            return False
        
        state = dialogue_state[chat_id]
        history = state.get("conversation_history", [])
        
        # Нужно минимум N сообщений от других ботов
        if len(history) < min_messages_before:
            return False
        
        # Проверяем не говорил ли 3-й бот недавно
        last_third_bot_message_time = None
        for msg in reversed(history):
            if msg.get("speaker", "").lower() == "перплексити":
                # Находим время последнего сообщения 3-го бота
                try:
                    last_third_bot_message_time = datetime.fromisoformat(msg.get("time", ""))
                except:
                    pass
                break
        
        if last_third_bot_message_time:
            time_since_last = (current_time - last_third_bot_message_time).total_seconds()
            if time_since_last < self.third_bot_timeout:
                return False
        
        # Проверяем зацикливание
        if self.detect_looping(chat_id):
            logger.info(f"🔍 3-й бот должен вмешаться: обнаружено зацикливание")
            return True
        
        # Перплексити теперь активируется только через упоминание @llmdebat3bot
        # Убираем автоактивацию по ключевым словам
        
        # Проверяем застой (короткие ответы подряд)
        if len(history) >= 3:
            recent_lengths = [len(msg['text']) for msg in history[-3:]]
            if all(length < 50 for length in recent_lengths):  # Все ответы очень короткие
                logger.info(f"🔍 3-й бот должен вмешаться: обнаружен застой (короткие ответы)")
                return True
        
        return False


# Глобальный менеджер диалога
dialogue_manager = BotDialogueManager()

