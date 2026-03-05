#!/usr/bin/env python3
"""Скрипт для полной очистки старых моделей из telegram_polling.py"""

import re

with open('backend/api/telegram_polling.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Удаляем старые модели из AVAILABLE_MODELS
content = re.sub(
    r'\s*"solar": \("openrouter", "upstage/solar-pro-3:free"\),.*# OpenRouter Solar Pro 3\n',
    '', content
)
content = re.sub(
    r'\s*"trinity": \("openrouter", "arcee-ai/trinity-mini:free"\),.*# OpenRouter Trinity Mini\n',
    '', content
)
content = re.sub(
    r'\s*"glm": \("openrouter", "z-ai/glm-4.5-air:free"\),.*# OpenRouter GLM-4.5\n',
    '', content
)

print("✅ Старые модели удалены из AVAILABLE_MODELS")

with open('backend/api/telegram_polling.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл обновлён")
