#!/usr/bin/env python3
"""
Тест генерации изображений через Hugging Face Inference API
Используется модель FLUX.1-dev
"""

import os
from huggingface_hub import InferenceClient
from PIL import Image
import io

# Получаем API ключ из переменных окружения
api_key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
if not api_key:
    print("❌ Ошибка: HF_TOKEN или HUGGINGFACE_API_KEY не найден в переменных окружения")
    print("Установите переменную окружения с вашим токеном Hugging Face")
    exit(1)

print("🚀 Инициализация InferenceClient...")
print(f"🔑 Используется токен: {api_key[:10]}...")

# Пробуем разные варианты провайдера
providers_to_test = [
    (None, "Hugging Face Inference API (без провайдера)"),
    ("fal-ai", "fal-ai"),
    ("replicate", "Replicate"),
    ("fireworks-ai", "Fireworks AI"),
    ("hf-inference", "HF Inference"),
]

for provider, name in providers_to_test:
    print(f"\n{'='*60}")
    print(f"🧪 Тест с провайдером: {name}")
    print(f"{'='*60}")
    
    try:
        if provider:
            client = InferenceClient(
                provider=provider,
                api_key=api_key,
            )
        else:
            client = InferenceClient(
                token=api_key,
            )
        
        print("🎨 Генерация изображения: 'Astronaut riding a horse'")
        print("⏳ Это может занять некоторое время...")
        
        # Генерация изображения
        image = client.text_to_image(
            "Astronaut riding a horse",
            model="black-forest-labs/FLUX.1-dev",
        )
        
        # Проверяем тип результата
        print(f"\n✅ Изображение успешно сгенерировано!")
        print(f"📐 Тип объекта: {type(image)}")
        
        if isinstance(image, Image.Image):
            print(f"📏 Размер изображения: {image.size}")
            print(f"🎨 Режим: {image.mode}")
            
            # Сохраняем изображение
            output_path = f"test_flux_output_{provider or 'default'}.png"
            image.save(output_path)
            print(f"\n💾 Изображение сохранено: {output_path}")
            
            # Успех - выходим из цикла
            break
        else:
            print(f"⚠️ Неожиданный тип результата: {type(image)}")

    except Exception as e:
        print(f"\n❌ Ошибка с провайдером {name}:")
        print(f"   {type(e).__name__}: {str(e)[:200]}")
        continue

else:
    print("\n" + "="*60)
    print("❌ Все провайдеры вернули ошибку")
    print("="*60)
