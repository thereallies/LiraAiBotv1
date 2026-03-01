# Hugging Face + Replicate Image Generation Integration

## Overview

This document describes the integration of Hugging Face Inference API with Replicate provider for image generation using FLUX.1 models.

## Features

- **FLUX.1 Dev** - High-quality image generation for all users
- **FLUX.1 Pro** - Enhanced quality for subscribers and admins
- **Automatic fallback** - Gemini → HF+Replicate → Pollinations
- **Level-based access** - Different models for different user levels

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Hugging Face API Token (required for HF+Replicate)
HF_TOKEN=your_huggingface_token_here
# or
HUGGINGFACE_API_KEY=your_huggingface_token_here
```

### Getting a Hugging Face Token

1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "read" permissions
3. Copy the token to your `.env` file

## Architecture

### Files Modified

1. **`backend/vision/hf_replicate.py`** - HF+Replicate client
   - `HFReplicateClient` class
   - Model management by access level
   - Image generation via `text_to_image()`

2. **`backend/api/telegram_polling.py`** - Telegram handler
   - Added `hf_replicate_client` initialization
   - Updated `handle_image_generation()` to support HF models
   - Updated callback handler for image model selection

3. **`backend/utils/keyboards.py`** - Inline keyboards
   - Updated `create_image_model_selection_keyboard()`
   - Added FLUX.1 Dev and Pro buttons

## Models

### Available Models

| Model Key | Model Name | Access Level | Description |
|-----------|-----------|--------------|-------------|
| `hf-flux-dev` | black-forest-labs/FLUX.1-dev | user, subscriber, admin | FLUX.1 Dev via Replicate |
| `hf-flux-pro` | black-forest-labs/FLUX.1-pro | subscriber, admin | FLUX.1 Pro via Replicate |
| `gemini-flash` | gemini-2.5-flash | all levels | Gemini 2.5 Flash |

### Access Levels

- **user**: `hf-flux-dev`, `gemini-flash`
- **subscriber**: `hf-flux-dev`, `hf-flux-pro`, `gemini-flash`
- **admin**: All models

## Usage

### Selecting a Model

1. Open the bot menu
2. Click "🎨 Генерировать фото"
3. Select desired model:
   - ✨ Gemini 2.5 Flash
   - 🎨 FLUX.1 Dev (Replicate)
   - 🚀 FLUX.1 Pro (Replicate) - subscribers/admins only
4. Send your image description

### API Usage

```python
from backend.vision.hf_replicate import get_hf_replicate_client

client = get_hf_replicate_client()

# Generate image
image_data = await client.generate_image(
    prompt="Astronaut riding a horse",
    model_key="hf-flux-dev",
    timeout=60
)

# Save image
from pathlib import Path
Path("output.png").write_bytes(image_data)
```

## Flow

```
User Request
    ↓
Check Access Level & Limits
    ↓
Select Model (HF or Gemini)
    ↓
Generate Image
    ├─→ HF+Replicate (primary)
    ├─→ Gemini (fallback 1)
    └─→ Pollinations (fallback 2)
    ↓
Send to User
```

## Testing

### Test Client Initialization

```bash
cd /Users/iluyshin.d/Desktop/LiraAiBOT
python3 -c "from backend.vision.hf_replicate import get_hf_replicate_client; \
            client = get_hf_replicate_client(); \
            print('Initialized:', client.api_key is not None)"
```

### Test Image Generation

```python
import asyncio
from backend.vision.hf_replicate import get_hf_replicate_client

async def test():
    client = get_hf_replicate_client()
    image = await client.generate_image("Astronaut riding a horse")
    print(f"Generated: {len(image)} bytes" if image else "Failed")

asyncio.run(test())
```

## Troubleshooting

### Common Issues

1. **"HF_TOKEN не настроен"**
   - Check `.env` file has `HF_TOKEN` or `HUGGINGFACE_API_KEY`
   - Restart the bot after adding the token

2. **"huggingface_hub не установлен"**
   - Run: `pip install huggingface_hub`
   - Already in `requirements.txt`

3. **Generation timeout**
   - FLUX.1 models may take 30-60 seconds
   - Increase timeout parameter if needed

4. **Empty image returned**
   - Check API key permissions
   - Verify Replicate provider access
   - Try a different prompt

## Performance

- **Generation Time**: 10-60 seconds depending on model
- **Image Size**: Typically 500KB - 2MB
- **Quality**: FLUX.1 Dev produces high-quality 1024x1024 images

## Rate Limits

Hugging Face + Replicate has its own rate limits:
- Free tier: Limited requests per day
- Pro tier: Higher limits
- Check https://huggingface.co/pricing for details

## Security

- API keys stored in `.env` (not in version control)
- Keys loaded via `os.getenv()`
- No hardcoded credentials

## Future Enhancements

- [ ] Add more FLUX models (Schnell, etc.)
- [ ] Support for image-to-image generation
- [ ] Custom resolution settings
- [ ] Batch generation
- [ ] Style presets

## References

- [Hugging Face Inference API](https://huggingface.co/docs/inference-endpoints/index)
- [Replicate Provider](https://replicate.com/)
- [FLUX.1 Models](https://huggingface.co/black-forest-labs)
- [Integration Test Script](test_hf_flux.py)
