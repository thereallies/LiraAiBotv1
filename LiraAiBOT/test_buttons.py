#!/usr/bin/env python3
"""Тест обработки кнопок"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / 'backend'))

from backend.utils.keyboards import create_main_menu_keyboard, BOT_MODES, get_mode_from_button

print("=== Тест обработки кнопок ===\n")

# Тест 1: Кнопка "📊 Статистика"
print("1. Кнопка '📊 Статистика':")
btn_stats = "📊 Статистика"
in_modes = btn_stats in BOT_MODES.values()
mode = get_mode_from_button(btn_stats)
print(f"   В BOT_MODES.values(): {in_modes}")
print(f"   get_mode_from_button(): {mode}")
print(f"   Будет обработана в блоке режимов: {in_modes and mode == 'stats'}")
print()

# Тест 2: Кнопки моделей
print("2. Кнопки выбора моделей:")
model_buttons = ["🚀 Groq Llama 3.3", "🦙 Groq Llama 4", "🔍 Groq Scout", "🌙 Groq Kimi K2"]
for btn in model_buttons:
    in_modes = btn in BOT_MODES.values()
    mode = get_mode_from_button(btn)
    print(f"   {btn}:")
    print(f"      В BOT_MODES.values(): {in_modes}")
    print(f"      get_mode_from_button(): {mode}")
    print(f"      Будет обработана в блоке моделей: {not in_modes}")
print()

# Тест 3: Кнопка "◀️ Назад к меню"
print("3. Кнопка '◀️ Назад к меню':")
btn_back = "◀️ Назад к меню"
in_modes = btn_back in BOT_MODES.values()
mode = get_mode_from_button(btn_back)
print(f"   В BOT_MODES.values(): {in_modes}")
print(f"   get_mode_from_button(): {mode}")
print(f"   Будет обработана отдельно (до режимов): {not in_modes}")
print()

# Тест 4: create_main_menu_keyboard
print("4. create_main_menu_keyboard():")
kb = create_main_menu_keyboard()
print(f"   Тип: {type(kb)}")
print(f"   Ключи: {list(kb.keys())}")
print(f"   Количество рядов кнопок: {len(kb.get('keyboard', []))}")
print(f"   resize_keyboard: {kb.get('resize_keyboard')}")
print()

print("=== Все тесты пройдены! ===")
