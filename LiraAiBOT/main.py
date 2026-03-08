"""
Простой корневой entrypoint для bothost.
Запускает FastAPI приложение из index.py без вложенных путей.
"""
from index import app
import os
import uvicorn


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("WEB_PORT", "8000")))
    uvicorn.run(app, host=host, port=port, reload=False, log_level="info")
