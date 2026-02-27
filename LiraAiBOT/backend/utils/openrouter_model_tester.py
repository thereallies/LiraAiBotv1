"""
Утилита для поиска и тестирования рабочих моделей OpenRouter.
Экономно использует платный ключ только для платных моделей.
"""
import asyncio
import logging
import json
import aiohttp
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import Config, OPENROUTER_API_KEYS
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("bot.model_tester")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_PAID = os.environ.get("OPENROUTER_API_KEY_PAID", "")


class OpenRouterModelTester:
    """Тестирует модели OpenRouter через все доступные ключи"""
    
    def __init__(self):
        self.config = Config()
        self.free_keys = OPENROUTER_API_KEYS.copy()
        self.paid_key = OPENROUTER_API_KEY_PAID if OPENROUTER_API_KEY_PAID else None
        
        # Результаты тестирования
        self.results = {
            "working_models": [],
            "free_models": [],
            "paid_models": [],
            "failed_models": [],
            "tested_at": datetime.now().isoformat()
        }
        
        logger.info(f"Инициализирован тестер: {len(self.free_keys)} бесплатных ключей, платный: {'есть' if self.paid_key else 'нет'}")
    
    async def get_models_list(self) -> List[Dict[str, Any]]:
        """Получает список всех доступных моделей через OpenRouter API"""
        try:
            # Используем первый ключ для получения списка моделей
            key = self.free_keys[0] if self.free_keys else None
            if not key:
                logger.error("Нет ключей для получения списка моделей")
                return []
            
            url = f"{OPENROUTER_API_URL}/models"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("data", [])
                        logger.info(f"Получено {len(models)} моделей из OpenRouter API")
                        return models
                    else:
                        error = await response.text()
                        logger.error(f"Ошибка получения моделей: {error}")
                        return []
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {e}")
            return []
    
    def is_paid_model(self, model_id: str) -> bool:
        """Определяет является ли модель платной"""
        # Платные модели обычно не имеют :free в конце
        paid_indicators = [
            "gpt-4", "gpt-4-turbo", "gpt-4o", "claude-3", "claude-3-opus",
            "grok", "grok-2", "o1", "o1-preview", "o3"
        ]
        
        # Проверяем наличие :free
        if ":free" in model_id.lower():
            return False
        
        # Проверяем индикаторы платных моделей
        model_lower = model_id.lower()
        for indicator in paid_indicators:
            if indicator in model_lower:
                return True
        
        return False
    
    async def test_model(
        self,
        model_id: str,
        api_key: str,
        is_paid: bool = False
    ) -> Dict[str, Any]:
        """
        Тестирует одну модель через конкретный ключ
        
        Args:
            model_id: ID модели
            api_key: API ключ для тестирования
            is_paid: Является ли модель платной
            
        Returns:
            Результат тестирования
        """
        result = {
            "model": model_id,
            "key_index": None,
            "status": "unknown",
            "error": None,
            "response_time": None,
            "is_paid": is_paid
        }
        
        try:
            # Минимальный тестовый запрос для экономии токенов
            test_prompt = "ping"
            
            url = f"{OPENROUTER_API_URL}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/liraai-multiassistent",
                "X-Title": "Telegram Bot Model Tester"
            }
            
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": test_prompt}
                ],
                "max_tokens": 10,  # Минимум токенов для теста
                "temperature": 0.1
            }
            
            start_time = asyncio.get_event_loop().time()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    result["response_time"] = round(response_time, 2)
                    
                    if response.status == 200:
                        data = await response.json()
                        result["status"] = "working"
                        result["response_preview"] = data.get("choices", [{}])[0].get("message", {}).get("content", "")[:50]
                        logger.info(f"✅ {model_id} - работает (время: {response_time:.2f}s)")
                        return result
                    elif response.status == 401:
                        result["status"] = "auth_error"
                        error_data = await response.json()
                        result["error"] = error_data.get("error", {}).get("message", "Unauthorized")
                        logger.warning(f"❌ {model_id} - ошибка авторизации")
                        return result
                    elif response.status == 429:
                        result["status"] = "rate_limit"
                        result["error"] = "Rate limit exceeded"
                        logger.warning(f"⚠️ {model_id} - rate limit")
                        return result
                    else:
                        error_text = await response.text()
                        result["status"] = "error"
                        result["error"] = error_text[:200]
                        logger.warning(f"❌ {model_id} - ошибка {response.status}")
                        return result
                        
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "Request timeout"
            logger.warning(f"⏱️ {model_id} - timeout")
            return result
        except Exception as e:
            result["status"] = "exception"
            result["error"] = str(e)[:200]
            logger.error(f"💥 {model_id} - исключение: {e}")
            return result
    
    async def test_models_batch(
        self,
        models: List[Dict[str, Any]],
        max_models: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Тестирует список моделей через все доступные ключи
        
        Args:
            models: Список моделей из API
            max_models: Максимальное количество моделей для тестирования (None = все)
            
        Returns:
            Результаты тестирования
        """
        if max_models:
            models = models[:max_models]
        
        logger.info(f"Начинаю тестирование {len(models)} моделей...")
        
        tested_count = 0
        
        for model_data in models:
            model_id = model_data.get("id", "")
            if not model_id:
                continue
            
            # Определяем тип модели
            is_paid = self.is_paid_model(model_id)
            
            tested_count += 1
            logger.info(f"[{tested_count}/{len(models)}] Тестирую {model_id} ({'платная' if is_paid else 'бесплатная'})...")
            
            # Для платных моделей используем только платный ключ (экономим токены)
            if is_paid:
                if self.paid_key:
                    result = await self.test_model(model_id, self.paid_key, is_paid=True)
                    result["key_type"] = "paid"
                    if result["status"] == "working":
                        self.results["paid_models"].append(result)
                        self.results["working_models"].append(result)
                    else:
                        self.results["failed_models"].append(result)
                else:
                    logger.warning(f"⚠️ Платная модель {model_id} пропущена (нет платного ключа)")
                    self.results["failed_models"].append({
                        "model": model_id,
                        "status": "skipped",
                        "error": "No paid key available",
                        "is_paid": True
                    })
            else:
                # Для бесплатных моделей пробуем все бесплатные ключи с ротацией
                working = False
                for i, key in enumerate(self.free_keys):
                    result = await self.test_model(model_id, key, is_paid=False)
                    result["key_index"] = i
                    result["key_type"] = "free"
                    
                    if result["status"] == "working":
                        self.results["free_models"].append(result)
                        self.results["working_models"].append(result)
                        working = True
                        break  # Если модель работает - не пробуем другие ключи
                    elif result["status"] == "rate_limit":
                        # При rate limit пробуем следующий ключ
                        continue
                    else:
                        # Другие ошибки - пробуем следующий ключ
                        continue
                
                if not working:
                    self.results["failed_models"].append({
                        "model": model_id,
                        "status": "failed",
                        "error": "All keys failed",
                        "is_paid": False
                    })
            
            # Небольшая пауза между тестами
            await asyncio.sleep(0.5)
        
        logger.info(f"Тестирование завершено: {len(self.results['working_models'])} рабочих моделей")
        return self.results
    
    async def save_results(self, filepath: Optional[Path] = None):
        """Сохраняет результаты тестирования в JSON файл"""
        if filepath is None:
            filepath = Path(__file__).parent.parent.parent / "data" / "openrouter_models_test.json"
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Результаты сохранены в {filepath}")
        
        # Также сохраняем краткий отчет
        report_path = filepath.parent / "openrouter_models_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=== ОТЧЕТ ПО ТЕСТИРОВАНИЮ МОДЕЛЕЙ OPENROUTER ===\n\n")
            f.write(f"Дата тестирования: {self.results['tested_at']}\n\n")
            f.write(f"Всего рабочих моделей: {len(self.results['working_models'])}\n")
            f.write(f"Бесплатных: {len(self.results['free_models'])}\n")
            f.write(f"Платных: {len(self.results['paid_models'])}\n")
            f.write(f"Не рабочих: {len(self.results['failed_models'])}\n\n")
            
            f.write("=== РАБОЧИЕ БЕСПЛАТНЫЕ МОДЕЛИ ===\n")
            for model in self.results["free_models"]:
                f.write(f"- {model['model']} (ключ #{model.get('key_index', '?')}, время: {model.get('response_time', 0):.2f}s)\n")
            
            f.write("\n=== РАБОЧИЕ ПЛАТНЫЕ МОДЕЛИ ===\n")
            for model in self.results["paid_models"]:
                f.write(f"- {model['model']} (время: {model.get('response_time', 0):.2f}s)\n")
            
            f.write("\n=== НЕ РАБОТАЮЩИЕ МОДЕЛИ ===\n")
            for model in self.results["failed_models"][:20]:  # Первые 20
                f.write(f"- {model['model']}: {model.get('error', 'unknown')}\n")
        
        logger.info(f"✅ Отчет сохранен в {report_path}")


async def main():
    """Основная функция для запуска тестирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    )
    
    tester = OpenRouterModelTester()
    
    # Получаем список моделей
    logger.info("Получаю список моделей из OpenRouter API...")
    models = await tester.get_models_list()
    
    if not models:
        logger.error("Не удалось получить список моделей")
        return
    
    # Фильтруем популярные и интересные модели для тестирования
    # Сначала тестируем бесплатные модели
    free_models = [m for m in models if tester.is_paid_model(m.get("id", "")) == False]
    paid_models = [m for m in models if tester.is_paid_model(m.get("id", "")) == True]
    
    logger.info(f"Найдено: {len(free_models)} бесплатных, {len(paid_models)} платных моделей")
    
    # Тестируем сначала бесплатные (до 50 штук для быстроты)
    logger.info("Тестирую бесплатные модели...")
    await tester.test_models_batch(free_models[:50])
    
    # Затем платные (экономно, до 10 штук)
    if tester.paid_key and paid_models:
        logger.info("Тестирую платные модели (экономно, до 10 штук)...")
        await tester.test_models_batch(paid_models[:10])
    
    # Сохраняем результаты
    await tester.save_results()
    
    # Выводим итоги
    print("\n" + "="*50)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*50)
    print(f"Рабочих моделей: {len(tester.results['working_models'])}")
    print(f"  - Бесплатных: {len(tester.results['free_models'])}")
    print(f"  - Платных: {len(tester.results['paid_models'])}")
    print(f"Не рабочих: {len(tester.results['failed_models'])}")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())

