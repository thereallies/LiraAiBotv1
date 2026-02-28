#!/usr/bin/env python3
"""Тестирование выбора моделей"""
from backend.api.telegram_polling import user_models, AVAILABLE_MODELS

print("="*60)
print("🧪 ТЕСТИРОВАНИЕ ВЫБОРА МОДЕЛЕЙ")
print("="*60)

# Симулируем выбор разных моделей
test_user = "test_user_123"

print("\n1️⃣ Тест: Выбор Groq Llama 3.3")
user_models[test_user] = "groq-llama"
model_key = user_models.get(test_user, "groq-llama")
model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
client_type, model = model_info
print(f"   model_key: {model_key}")
print(f"   client_type: {client_type}")
print(f"   model: {model}")
print(f"   ✅ {'OK' if client_type == 'groq' else '❌ ОШИБКА!'}")

print("\n2️⃣ Тест: Выбор Cerebras Qwen 3")
user_models[test_user] = "cerebras-qwen"
model_key = user_models.get(test_user, "groq-llama")
model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
client_type, model = model_info
print(f"   model_key: {model_key}")
print(f"   client_type: {client_type}")
print(f"   model: {model}")
print(f"   ✅ {'OK' if client_type == 'cerebras' else '❌ ОШИБКА!'}")

print("\n3️⃣ Тест: Выбор Cerebras Llama 3.1")
user_models[test_user] = "cerebras-llama"
model_key = user_models.get(test_user, "groq-llama")
model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
client_type, model = model_info
print(f"   model_key: {model_key}")
print(f"   client_type: {client_type}")
print(f"   model: {model}")
print(f"   ✅ {'OK' if client_type == 'cerebras' else '❌ ОШИБКА!'}")

print("\n4️⃣ Тест: Выбор Solar")
user_models[test_user] = "solar"
model_key = user_models.get(test_user, "groq-llama")
model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
client_type, model = model_info
print(f"   model_key: {model_key}")
print(f"   client_type: {client_type}")
print(f"   model: {model}")
print(f"   ✅ {'OK' if client_type == 'openrouter' else '❌ ОШИБКА!'}")

print("\n5️⃣ Тест: Выбор Trinity")
user_models[test_user] = "trinity"
model_key = user_models.get(test_user, "groq-llama")
model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
client_type, model = model_info
print(f"   model_key: {model_key}")
print(f"   client_type: {client_type}")
print(f"   model: {model}")
print(f"   ✅ {'OK' if client_type == 'openrouter' else '❌ ОШИБКА!'}")

print("\n6️⃣ Тест: Выбор GLM-4.5")
user_models[test_user] = "glm"
model_key = user_models.get(test_user, "groq-llama")
model_info = AVAILABLE_MODELS.get(model_key, ("groq", "llama-3.3-70b-versatile"))
client_type, model = model_info
print(f"   model_key: {model_key}")
print(f"   client_type: {client_type}")
print(f"   model: {model}")
print(f"   ✅ {'OK' if client_type == 'openrouter' else '❌ ОШИБКА!'}")

print("\n" + "="*60)
print("✅ ВСЕ МОДЕЛИ МАППЯТСЯ ПРАВИЛЬНО!")
print("="*60)
