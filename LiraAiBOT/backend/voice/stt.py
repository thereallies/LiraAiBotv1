"""
Модуль для преобразования речи в текст (Speech-to-Text).
"""
import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("bot.stt")

class SpeechToText:
    """
    Класс для преобразования речи в текст.
    """
    
    def __init__(self):
        """
        Инициализирует STT движок.
        """
        self.use_speech_recognition = True
        
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            logger.info("SpeechRecognition инициализирован")
        except ImportError:
            logger.error("SpeechRecognition не установлен. Установите: pip install SpeechRecognition")
            self.use_speech_recognition = False
    
    def _convert_to_wav(self, input_path: str) -> Optional[str]:
        """
        Конвертирует аудио в WAV через librosa.
        
        Args:
            input_path: Путь к исходному файлу
            
        Returns:
            Путь к WAV файлу или None
        """
        try:
            import librosa
            import soundfile as sf
            
            # Создаем папку temp если не существует
            temp_dir = Path(__file__).parent.parent.parent / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            logger.info(f"🔄 КОНВЕРТИРУЕМ В WAV: {input_path}")
            
            # Загружаем аудио
            audio_data, sample_rate = librosa.load(input_path, sr=16000)  # 16kHz для STT
            
            # Создаем путь для WAV файла
            wav_path = temp_dir / "voice_temp.wav"
            
            # Сохраняем как WAV
            sf.write(str(wav_path), audio_data, sample_rate)
            
            logger.info(f"✅ КОНВЕРТАЦИЯ ЗАВЕРШЕНА: {wav_path}")
            
            return str(wav_path)
            
        except Exception as e:
            logger.error(f"Ошибка конвертации: {e}")
            return None
    
    def speech_to_text(self, audio_path: str, language: str = "ru") -> str:
        """
        Преобразует речь в текст.
        
        Args:
            audio_path: Путь к аудиофайлу
            language: Язык (ru, en, etc.) - используется для определения формата (ru -> ru-RU)
            
        Returns:
            Распознанный текст
        """
        if not self.use_speech_recognition:
            logger.error("STT не доступен - SpeechRecognition не установлен")
            return ""
        
        wav_path = None
        
        try:
            import speech_recognition as sr
            
            # Проверяем существование файла
            if not os.path.exists(audio_path):
                logger.error(f"Аудиофайл не найден: {audio_path}")
                return ""
            
            # Проверяем размер файла
            file_size = os.path.getsize(audio_path)
            logger.info(f"Обрабатываем аудиофайл: {audio_path} (размер: {file_size} байт)")
            
            if file_size == 0:
                logger.error("Аудиофайл пустой")
                return ""
            
            # Конвертируем в WAV если нужно
            if not audio_path.lower().endswith('.wav'):
                wav_path = self._convert_to_wav(audio_path)
                if not wav_path:
                    return ""
                process_path = wav_path
            else:
                process_path = audio_path
            
            logger.info(f"🎤 ЗАПУСКАЕМ SPEECH RECOGNITION: {process_path}")
            
            # Определяем язык для Google API
            lang_code = "ru-RU" if language == "ru" else f"{language}-{language.upper()}"
            
            # Загружаем аудиофайл
            with sr.AudioFile(process_path) as source:
                # Записываем аудио
                audio = self.recognizer.record(source)
                
                # Распознаем речь через Google API (бесплатно)
                text = self.recognizer.recognize_google(audio, language=lang_code)
                
                logger.info(f"✅ РАСПОЗНАННЫЙ ТЕКСТ: {text}")
                return text
            
        except sr.UnknownValueError:
            logger.warning("Не удалось распознать речь")
            return ""
        except sr.RequestError as e:
            logger.error(f"Ошибка сервиса распознавания: {e}")
            return ""
        except Exception as e:
            logger.error(f"❌ ОШИБКА ПРИ РАСПОЗНАВАНИИ РЕЧИ: {e}")
            return ""
        finally:
            # Удаляем временный WAV файл
            if wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                    logger.info(f"🗑️ УДАЛЕН ВРЕМЕННЫЙ WAV: {wav_path}")
                except:
                    pass
    
    async def process_voice_message(self, file_path: str) -> str:
        """
        Обрабатывает голосовое сообщение.
        
        Args:
            file_path: Путь к файлу голосового сообщения
            
        Returns:
            Распознанный текст
        """
        try:
            logger.info(f"🎤 НАЧИНАЕМ ОБРАБОТКУ ГОЛОСОВОГО ФАЙЛА: {file_path}")
            
            # Проверяем файл
            if not os.path.exists(file_path):
                logger.error(f"❌ ФАЙЛ НЕ СУЩЕСТВУЕТ: {file_path}")
                return ""
            
            # Распознаем речь
            text = self.speech_to_text(file_path)
            return text
            
        except Exception as e:
            logger.error(f"❌ ОШИБКА ПРИ ОБРАБОТКЕ ГОЛОСОВОГО СООБЩЕНИЯ: {e}")
            return ""
