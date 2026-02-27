#!/usr/bin/env python3
"""
Вспомогательный скрипт для распознавания голоса через STT
Вызывается из Node.js скрипта
"""
import sys
import os
from pathlib import Path

# Добавляем путь к backend
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.voice.stt import SpeechToText

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("", end="")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print("", end="")
        sys.exit(1)
    
    try:
        stt = SpeechToText()
        text = stt.speech_to_text(audio_path, language="ru")
        print(text, end="")
    except Exception as e:
        print("", end="")
        sys.exit(1)


