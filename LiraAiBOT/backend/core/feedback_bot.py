"""
Модуль для обработки обратной связи через LiraAI MultiAssistent.
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import re

from backend.config import Config
from backend.llm.openrouter import OpenRouterClient

logger = logging.getLogger("bot.feedback_bot")

# Примерная оценка токенов (1 токен ≈ 4 символа для русского текста)
TOKENS_PER_CHAR = 0.25
MAX_KNOWLEDGE_TOKENS = 8000  # Используем первые 8000 токенов базы знаний


class FeedbackBotHandler:
    """Обработчик для LiraAI MultiAssistent - эксперта по обратной связи"""
    
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config()
        self.config = config
        
        # Путь к базе знаний
        self.knowledge_dir = Path(__file__).parent.parent / "data" / "feedback_knowledge"
        
        # Загружаем системный промпт и базу знаний
        self.system_prompt = self._load_system_prompt()
        self.knowledge_base = self._load_knowledge_base()
        
        # Создаем LLM клиент
        self.llm_client = OpenRouterClient(config)
        
        logger.info("FeedbackBotHandler инициализирован")
    
    def _load_system_prompt(self) -> str:
        """Загружает системный промпт из файла"""
        prompt_path = self.knowledge_dir / "bot_system_prompt_ru.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Извлекаем системный промпт из блока между ```
            # Ищем блок между ``` после "## СИСТЕМНЫЙ ПРОМПТ"
            # Паттерн: ## СИСТЕМНЫЙ ПРОМПТ, затем ```, затем контент, затем ```
            match = re.search(r'## СИСТЕМНЫЙ ПРОМПТ\s*\n\s*```\s*\n(.*?)\n\s*```', content, re.DOTALL)
            if match:
                prompt = match.group(1).strip()
            else:
                # Альтернативный паттерн: ищем просто между ```
                match2 = re.search(r'```\s*\n(.*?)\n\s*```', content, re.DOTALL)
                if match2:
                    prompt = match2.group(1).strip()
                else:
                    # Если не нашли блок, берем весь контент после заголовка
                    parts = content.split('## СИСТЕМНЫЙ ПРОМПТ', 1)
                    if len(parts) > 1:
                        prompt = parts[1].strip()
                        # Убираем лишние символы в начале и конце
                        prompt = re.sub(r'^```\s*', '', prompt)
                        prompt = re.sub(r'\s*```$', '', prompt)
                    else:
                        prompt = content.strip()
            
            logger.info(f"Системный промпт загружен ({len(prompt)} символов)")
            return prompt
        except Exception as e:
            logger.error(f"Ошибка загрузки системного промпта: {e}")
            return "Ты - LiraAI MultiAssistent, эксперт по обратной связи для лидеров и менеджеров."
    
    def _load_knowledge_base(self) -> str:
        """Загружает базу знаний (первые N токенов)"""
        knowledge_path = self.knowledge_dir / "base_knowledge_ru.txt"
        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ограничиваем размер (примерно 8000 токенов)
            max_chars = int(MAX_KNOWLEDGE_TOKENS / TOKENS_PER_CHAR)
            if len(content) > max_chars:
                content = content[:max_chars]
                # Обрезаем по последнему завершенному разделу
                last_section = content.rfind('\n##')
                if last_section > max_chars * 0.8:  # Если нашли раздел в последних 20%
                    content = content[:last_section]
            
            logger.info(f"База знаний загружена ({len(content)} символов, ~{int(len(content) * TOKENS_PER_CHAR)} токенов)")
            return content
        except Exception as e:
            logger.error(f"Ошибка загрузки базы знаний: {e}")
            return ""
    
    def _determine_mode(self, user_message: str) -> str:
        """Определяет режим работы бота по контексту сообщения"""
        message_lower = user_message.lower()
        
        # Ключевые слова для определения режима
        mode_keywords = {
            "анализ": ["анализ", "ситуация", "помоги", "как дать", "нужно дать"],
            "коучинг": ["подготовь", "подготовка", "скоро", "через", "минут", "сейчас"],
            "развитие": ["научи", "обучение", "навык", "развить", "улучшить"],
            "q&a": ["что такое", "когда", "какая разница", "чем отличается", "?"],
            "культура": ["культура", "команда", "организация", "внедрить", "построить"]
        }
        
        # Подсчитываем совпадения
        scores = {}
        for mode, keywords in mode_keywords.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[mode] = score
        
        if scores:
            # Возвращаем режим с наибольшим количеством совпадений
            return max(scores, key=scores.get)
        
        # По умолчанию - анализ ситуации
        return "анализ"
    
    def _build_full_system_prompt(self, mode: str) -> str:
        """Строит полный системный промпт с базой знаний и режимом"""
        # Базовый системный промпт
        full_prompt = self.system_prompt
        
        # Добавляем базу знаний
        if self.knowledge_base:
            full_prompt += f"\n\n## БАЗА ЗНАНИЙ ПО ОБРАТНОЙ СВЯЗИ:\n\n{self.knowledge_base[:5000]}\n"
            # Ограничиваем размер базы знаний в промпте, чтобы не превысить лимиты
        
        # Добавляем информацию о режиме
        mode_descriptions = {
            "анализ": "РЕЖИМ: АНАЛИЗ СИТУАЦИИ - Помоги пользователю проанализировать ситуацию с обратной связью, задай уточняющие вопросы, предложи модель и конкретные фразы.",
            "коучинг": "РЕЖИМ: КОУЧИНГ В РЕАЛЬНОМ ВРЕМЕНИ - Пользователь готовится к разговору. Дай краткие, практичные советы для подготовки.",
            "развитие": "РЕЖИМ: РАЗВИТИЕ НАВЫКОВ - Помоги пользователю развить навыки обратной связи через обучение моделям и практику.",
            "q&a": "РЕЖИМ: ВОПРОС И ОТВЕТ - Ответь на прямой вопрос четко и кратко с практичными примерами.",
            "культура": "РЕЖИМ: ПОСТРОЕНИЕ КУЛЬТУРЫ - Помоги построить культуру обратной связи в организации/команде."
        }
        
        if mode in mode_descriptions:
            full_prompt += f"\n\n{mode_descriptions[mode]}"
        
        return full_prompt
    
    async def process_feedback_query(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Обрабатывает запрос пользователя по обратной связи
        
        Args:
            user_message: Сообщение пользователя
            chat_history: История диалога в формате [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            Ответ бота
        """
        try:
            logger.info(f"[FeedbackBot] 🔍 Анализирую запрос пользователя: {len(user_message)} символов")
            
            # Определяем режим работы
            mode = self._determine_mode(user_message)
            logger.info(f"[FeedbackBot] 🎯 Определен режим работы: {mode}")
            
            # Строим полный системный промпт
            system_prompt = self._build_full_system_prompt(mode)
            logger.debug(f"[FeedbackBot] Системный промпт: {len(system_prompt)} символов")
            
            # Формируем историю сообщений для LLM (без текущего сообщения)
            history_for_llm = None
            if chat_history:
                # Берем последние 10 сообщений для экономии токенов
                history_for_llm = chat_history[-10:]
                logger.info(f"[FeedbackBot] 📚 Использую историю: {len(history_for_llm)} сообщений из {len(chat_history)}")
            else:
                logger.debug(f"[FeedbackBot] История диалога отсутствует")
            
            # Вызываем LLM
            logger.info(f"[FeedbackBot] 🤖 Отправляю запрос в LLM (модель: {self.llm_client.default_model})...")
            response = await self.llm_client.chat_completion(
                user_message=user_message,
                system_prompt=system_prompt,
                chat_history=history_for_llm,
                temperature=0.7
            )
            logger.info(f"[FeedbackBot] ✅ Получен ответ от LLM: {len(response)} символов")
            
            return response
            
        except Exception as e:
            logger.error(f"[FeedbackBot] ❌ Ошибка при обработке запроса обратной связи: {e}", exc_info=True)
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз."

