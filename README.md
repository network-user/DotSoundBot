# DotSound Bot

Telegram-бот музыкальной платформы DotSound — загрузка треков, поиск через inline-режим, лайки, открытие Mini App.

> Этот репозиторий опубликован как engineering showcase.
> Критичная закрытая логика переносится в приватный репозиторий
> `DotSoundPrivateCore`.

---

## Стек


| Компонент   | Технология                    |
| ----------- | ----------------------------- |
| Бот         | aiogram 3.x (полностью async) |
| HTTP-клиент | httpx (async)                 |
| Конфиг      | pydantic-settings             |
| Логирование | structlog                     |
| Зависимости | Poetry                        |


---

## Требования


| Инструмент                           | Версия  | Зачем                                           |
| ------------------------------------ | ------- | ----------------------------------------------- |
| Python                               | 3.11+   | Запуск бота                                     |
| [Poetry](https://python-poetry.org/) | любая   | Управление зависимостями                        |
| Telegram Bot Token                   | —       | Получить у [@BotFather](https://t.me/BotFather) |
| DotSoundBackend                      | запущен | Бот — тонкий клиент, вся логика на бэкенде      |


> Бот не работает без запущенного DotSoundBackend. Сначала поднимите бэкенд — инструкция: [DotSoundBackend/README.md](../DotSoundBackend/README.md)

---

## Быстрый старт

### Шаг 1 — Клонируйте и установите зависимости

```bash
git clone <repo-url>
cd DotSoundBot

poetry install
```

### Шаг 2 — Получите токен бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям, придумайте имя и username бота
4. Скопируйте выданный токен вида `123456789:AABBccDDeeFFggHH...`

### Шаг 3 — Настройте переменные окружения

```bash
cp .env.example .env
```

Откройте `.env` и вставьте токен:

```env
BOT_TOKEN=123456789:AABBccDDeeFFggHH...
BACKEND_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO
```

Если бэкенд запущен не локально — укажите его публичный адрес в `BACKEND_BASE_URL`.

### Шаг 4 — Убедитесь, что DotSoundBackend запущен

```bash
curl http://localhost:8000/api/v1/health
# Ожидаемый ответ: {"status": "ok"} или аналогичный
```

Если бэкенд не отвечает — [запустите его сначала](../DotSoundBackend/README.md).

### Шаг 5 — Запустите бота

```bash
poetry run python main.py
```

Бот запустится в режиме long polling. Вы увидите лог:

```
INFO  dotsound_bot_starting ...
INFO  bot started polling
```

Найдите своего бота в Telegram и отправьте `/start`.

---

## Переменные окружения

Файл: `.env` (создаётся из `.env.example`)


| Переменная         | Описание                                 | Обязательная | Значение по умолчанию   |
| ------------------ | ---------------------------------------- | ------------ | ----------------------- |
| `BOT_TOKEN`        | Токен бота из @BotFather                 | ✅            | —                       |
| `TELEGRAM_API_PROXY_URL` | Proxy для Telegram Bot API и скачивания файлов | — | — |
| `BACKEND_BASE_URL` | URL DotSoundBackend                      | —            | `http://localhost:8000` |
| `LOG_LEVEL`        | Уровень логов (`DEBUG`/`INFO`/`WARNING`) | —            | `INFO`                  |
| `BACKUP_NOTIFY_TELEGRAM_ID` | Chat ID для backup-уведомлений internal API | — | `0` |


---

## Возможности бота

### Команды


| Команда    | Описание                                            |
| ---------- | --------------------------------------------------- |
| `/start`   | Регистрация пользователя и приветственное сообщение |
| `/help`    | Список возможностей бота                            |
| `/mystats` | Статистика: количество загруженных треков, лайков   |


### Inline-поиск

Поиск треков прямо из любого чата без открытия бота:

```
@your_bot_name название трека
```

Результаты появятся списком — нажмите на трек, чтобы отправить его в чат.

### Загрузка треков

Отправьте аудиофайл (`.mp3`, `.flac`, `.ogg`, `.wav`, `.m4a`) прямо в чат с ботом — трек автоматически загрузится на платформу.

### Mini App

Кнопка **«Открыть плеер»** открывает полноценный веб-плеер внутри Telegram.

---

## Архитектура

```
Telegram
   ↓
handlers/          ← обработчики команд и событий (тонкий слой)
   ↓
bot/api/client.py  ← HTTP-клиент (httpx)
   ↓
DotSoundBackend REST API
```

Handlers не содержат бизнес-логики — только вызов `BackendClient` и формирование ответа пользователю.

Приватное ядро (`DotSoundPrivateCore`) используется для internal bridge
правил и чувствительных политик, которые не публикуются как open source.

### Компоненты


| Файл / Директория               | Описание                                            |
| ------------------------------- | --------------------------------------------------- |
| `bot/handlers/base.py`          | `/start`, `/help`, кнопка открытия Mini App         |
| `bot/handlers/audio.py`         | Загрузка аудиофайлов                                |
| `bot/handlers/inline_mode.py`   | Inline-поиск треков                                 |
| `bot/handlers/likes.py`         | Callback-обработчик лайков                          |
| `bot/handlers/stats.py`         | `/mystats`, callback статистики                     |
| `bot/api/client.py`             | Все запросы к DotSoundBackend                       |
| `bot/keyboards/inline.py`       | Фабрики инлайн-клавиатур                            |
| `bot/middlewares/throttling.py` | Ограничение частоты запросов (0.7 с / пользователь) |
| `bot/middlewares/logging.py`    | Логирование входящих событий                        |


---

## Команды разработчика

```bash
# Docker Compose (bot + redis + json-file log rotation)
docker compose up -d --build

# Тесты
poetry run pytest

# Линтер
poetry run ruff check .

# Проверка типов
poetry run mypy bot/

# Форматирование
poetry run black bot/
```

---

## License / Usage Restrictions

Репозиторий **не является open source**.

- Лицензия: `[LICENSE](./LICENSE)`
- Ограничения использования: `[NOTICE](./NOTICE)`

Разрешён просмотр и не-production оценка кода. Продакшн-использование,
коммерческая эксплуатация, SaaS-хостинг, встраивание в другие продукты
и перераспространение запрещены без письменного разрешения.

---

## Частые проблемы

**Бот не отвечает после `/start`**

- Проверьте, что `BOT_TOKEN` корректный
- Убедитесь, что DotSoundBackend запущен и доступен по `BACKEND_BASE_URL`

**Ошибка `ConnectionRefusedError` при старте**

- DotSoundBackend не запущен. Выполните `curl $BACKEND_BASE_URL/api/v1/health`

**Inline-поиск не работает**

- В @BotFather включите inline-режим: `/mybots` → ваш бот → `Bot Settings` → `Inline Mode` → `Turn on`

---

> Связанный репозиторий: [DotSoundBackend](../DotSoundBackend)
