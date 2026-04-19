# DotSoundBot — Agent Context

## Проект
DotSound — музыкальная платформа в Telegram (SoundCloud-style, UGC, без рекламы).
Этот репозиторий: Telegram-бот (aiogram 3.x) + Mini App (HTML/CSS/JS). Только визуальная часть.
Вся бизнес-логика и данные — в репозитории `DotSoundBackend`.

## TODO-трекер
- Файл `TODO.md` в корне — единый источник задач проекта.
- Агент обязан прочитать его в начале сессии и обновить после
  выполнения задач.

## Жёсткие границы public/private
- Этот репозиторий — публичный thin client. Private bridge логика
  живёт в `DotSoundPrivateCore`.
- Любой агент обязан соблюдать `docs/ai-boundary-policy.md`.
- Запрещено переносить private-код в public-ветку без явного
  подтверждения владельца.
- Если неясно, к какой зоне относится изменение, агент должен
  остановиться и запросить подтверждение.

## Секреты и `.env` (HARD RULE)
- `.env` и любые другие файлы с секретами (полный список —
  `.cursor/rules/secrets-and-env.mdc`) агенту трогать **запрещено**:
  ни читать, ни искать внутри, ни редактировать, ни переименовывать,
  ни откатывать через git, ни передавать в команды, ни цитировать
  содержимое в чате/коммитах/логах.
- Разрешены без спроса только `*.example` / `*.sample` / `*.template`,
  упоминания **имён** переменных в абстракции, и ссылка на путь к
  секретному файлу в конфиге (например, `env_file: - .env` в
  `docker-compose.yml`).
- Если для задачи нужно конкретное значение — агент обязан
  остановиться и попросить владельца либо вставить значение в чат,
  либо явно дать одноразовое разрешение на чтение конкретного файла.
- Разрешение действует только на текущую сессию и только на
  указанный файл; на следующий чат и на другие файлы оно не
  переносится.

## Стек
- Python 3.12
- aiogram 3.x (Telegram Bot API, полностью async)
- httpx (async HTTP-клиент для вызовов DotSoundBackend)
- pydantic-settings (конфиг из env)

## Соглашения кода
- Линтер: **Ruff** | Форматтер: **Black** | Type checker: **Mypy strict**
- Длина строки: **79 символов**
- **Без комментариев** — код самодокументируется через имена
- Докстринги только там, где сигнатура не передаёт смысл
- **Полная асинхронность**: async/await везде без исключений
- Настройки только через `bot/config.py` (pydantic-settings). `os.environ` напрямую — запрещено
- **После каждой новой фичи обязательно пишем тесты** (pytest + anyio)

## Архитектурные слои
```
handlers/  →  bot/api/client.py  →  [DotSoundBackend REST API]
```
- `handlers/` — тонкие. Никакой логики: только вызов `BackendClient` и ответ пользователю.
- `bot/api/client.py` — единственный канал к бэкенду. Никогда не инстанциировать `httpx` напрямую в хендлерах.
- `keyboards/` — фабричные функции, возвращающие `InlineKeyboardMarkup`. Никакой логики.
- `middlewares/` — cross-cutting concerns (логирование, rate limiting в будущем).
- `bot/api/internal.py` — приватный HTTP-API для backend↔bot:
  - `POST /internal/profile-audios/{user_id}` — список треков юзера
  - `POST /internal/download-audio` — скачать аудио по file_id
  - `POST /internal/send-auth-code` — отправить код входа
  - `POST /internal/send-login-notification` — уведомление о входе
  - `POST /internal/admin-alert` — алерты админ-панели в Telegram
    (chat_id allowlist через `ADMIN_ALERT_CHAT_ID_ALLOWLIST`)
  Все эти роуты требуют `X-Internal-Secret` header, контракт
  endpoints в `dotsound_private_core.contracts.internal_api`.

## Структура репозитория
```
DotSoundBot/
├── bot/
│   ├── main.py              # async main(): Bot + Dispatcher + polling
│   ├── config.py            # BotSettings(BaseSettings)
│   ├── api/
│   │   └── client.py        # BackendClient, BackendError
│   ├── handlers/
│   │   └── base.py          # register_handlers(dp), /start, echo
│   ├── keyboards/
│   │   └── inline.py        # open_player_keyboard()
│   ├── middlewares/
│   │   └── logging.py       # LoggingMiddleware
│   └── utils/
│       └── formatting.py    # truncate()
├── tests/
│   └── test_placeholder.py
├── .env.example
├── .gitignore
├── main.py                  # asyncio.run(bot.main.main())
└── pyproject.toml
```

## Запуск локально
```bash
cp .env.example .env
# заполнить BOT_TOKEN из @BotFather
poetry install
poetry run python main.py
```

## Тесты
```bash
poetry run pytest
```

## Lint / Format / Typecheck
```bash
poetry run ruff check .
poetry run black .
poetry run mypy bot/
```
