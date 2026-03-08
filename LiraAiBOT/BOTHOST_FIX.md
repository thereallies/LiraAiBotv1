# 🛠️ Исправление ошибки bothost.ru

## Проблема

```
python: can't open file '/app/run.py': [Errno 2] No such file or directory
```

**Причина:** bothost.ru пытался запустить `run.py`, но после `COPY . .` файлы находятся в `/app/`, а структура проекта:

```
LiraAiBOT/          ← корень проекта
├── run.py
├── backend/
│   └── main.py
```

После копирования в контейнер:
```
/app/
├── LiraAiBOT/
│   ├── run.py
│   └── backend/
```

---

## ✅ Решение

### 1. Использовать `index.py` (рекомендуется)

Создан файл `index.py` в корне проекта:
- Импортирует приложение из `backend/main.py`
- Правильно настраивает пути
- Загружает `.env`

**Настройка в панели bothost.ru:**
| Поле | Значение |
|------|----------|
| Главный файл | `index.py` |

### 2. Dockerfile

Проект содержит `Dockerfile` с правильным CMD:

```dockerfile
CMD ["python", "index.py"]
```

**Если bothost.ru использует свой Dockerfile**, измените CMD на:
```dockerfile
CMD ["python", "index.py"]
```

### 3. Альтернатива: изменить структуру

Если bothost.ru требует запуск определённого файла, можно создать симлинк:

```bash
# В Dockerfile добавить:
RUN ln -s /app/index.py /app/run.py
```

---

## 📋 Проверка перед деплоем

1. ✅ `index.py` существует в корне проекта
2. ✅ `Dockerfile` содержит `CMD ["python", "index.py"]`
3. ✅ В панели bothost.ru указан главный файл: `index.py`
4. ✅ Порт указан: `8001`

---

## 🚀 После исправления

1. Пересоберите проект в bothost.ru
2. Проверьте логи сборки:
   ```
   Step 15/15 : CMD ["python", "index.py"]
   ```
3. После запуска проверьте:
   - `https://liraai.bothost.ru/health` → `{"status": "healthy"}`
   - `https://liraai.bothost.ru/web` → лендинг

---

**Создано:** 2026-03-08
**Проблема:** Ошибка запуска `/app/run.py`
**Решение:** Использовать `index.py` как точку входа
