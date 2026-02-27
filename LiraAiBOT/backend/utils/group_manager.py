"""
Утилита для управления группами Telegram ботов.
Автоматически сохраняет ID групп в .env файл.
"""
import os
import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger("bot.group_manager")

# Путь к .env файлу
ENV_FILE = Path(__file__).parent.parent.parent / ".env"


def load_group_ids_from_env() -> Set[str]:
    """Загружает ID групп из .env файла"""
    group_ids = set()
    
    if not ENV_FILE.exists():
        return group_ids
    
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TELEGRAM_GROUP_ID") and "=" in line:
                    # Поддержка TELEGRAM_GROUP_ID, TELEGRAM_GROUP_ID1, и т.д.
                    value = line.split("=", 1)[1].strip()
                    if value and not value.startswith("#"):
                        group_ids.add(value)
    except Exception as e:
        logger.error(f"Ошибка при чтении .env файла: {e}")
    
    return group_ids


def save_group_id_to_env(group_id: str) -> bool:
    """
    Сохраняет ID группы в .env файл.
    
    Args:
        group_id: ID группы для сохранения
        
    Returns:
        True если успешно сохранено, False если уже существует
    """
    if not group_id or not group_id.strip():
        return False
    
    group_id = group_id.strip()
    
    # Загружаем существующие ID
    existing_ids = load_group_ids_from_env()
    
    # Если уже существует - не сохраняем
    if group_id in existing_ids:
        logger.debug(f"ID группы {group_id} уже существует в .env")
        return False
    
    # Добавляем новый ID
    existing_ids.add(group_id)
    
    try:
        # Читаем весь файл
        lines = []
        group_ids_in_file = set()
        
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
                # Удаляем старые TELEGRAM_GROUP_ID строки
                lines = [line for line in lines if not line.strip().startswith("TELEGRAM_GROUP_ID")]
        
        # Добавляем все ID групп в конец файла
        if not any("=== TELEGRAM GROUPS ===" in line for line in lines):
            lines.append("\n# === TELEGRAM GROUPS ===\n")
        
        # Добавляем ID групп
        group_id_vars = sorted(existing_ids)
        for i, gid in enumerate(group_id_vars):
            if i == 0:
                lines.append(f"TELEGRAM_GROUP_ID={gid}\n")
            else:
                lines.append(f"TELEGRAM_GROUP_ID{i}={gid}\n")
        
        # Записываем обратно
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        logger.info(f"✅ ID группы {group_id} сохранен в .env файл")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении ID группы в .env: {e}")
        return False


def get_all_group_ids() -> List[str]:
    """Возвращает список всех ID групп из .env"""
    return sorted(list(load_group_ids_from_env()))

