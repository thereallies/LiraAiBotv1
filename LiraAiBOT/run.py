"""
Скрипт для запуска Telegram бота.
"""
import os
import sys
from pathlib import Path

# Добавляем путь к backend в sys.path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Переходим в директорию backend
os.chdir(backend_path)

# Запускаем main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

