# AGENTS.md

> Инструкции для AI coding agents. Человеческий обзор - в [README.md](README.md).
> Перегенерировано скиллом `generate-readme`. Источник правды - код репозитория.

## Профиль проекта

- **Тип:** bot (Telegram, aiogram 3.x, полностью async)
- **Аудитория:** internal / source-available showcase
- **Runtime:** Python 3.12 (Poetry)
- **Монорепо:** no (тонкий клиент; приватное ядро - соседний `../DotSoundPrivateCore`)

DotSound - музыкальная платформа в Telegram. Этот репозиторий - публичный тонкий клиент: Telegram/UI-слой и HTTP-клиент к бэкенду. Бизнес-логика и данные - в `DotSoundBackend`, чувствительная bridge-логика и internal-контракты - в закрытом `dotsound_private_core`.

## Жёсткие границы public/private

- Соблюдай [docs/ai-boundary-policy.md](docs/ai-boundary-policy.md) как обязательные правила. CI: `scripts/check_boundary_policy.py`.
- Хендлеры держи тонкими и user-facing; не инлайнь приватные bridge-константы в публичный код.
- Чувствительную bridge-логику реализуй через `dotsound_private_core`.
- Если зона изменения неясна (public bot vs private bridge) - **остановись и запроси подтверждение владельца**.

## Секреты и `.env` (HARD RULE)

- `.env` и любые секретные файлы (полный список - `.cursor/rules/secrets-and-env.mdc`) трогать **запрещено**: не читать, не искать внутри, не редактировать, не переименовывать, не откатывать через git, не передавать во внешние команды, не цитировать содержимое (в чате, коммитах, логах, PR, промптах подагентов).
- Разрешены без спроса: `*.example` / `*.sample` / `*.template`, упоминание **имён** переменных абстрактно, ссылка на путь секрета в конфиге (`env_file: - .env`).
- Нужно конкретное значение - остановись и попроси владельца вставить его в чат или дать одноразовое per-file разрешение на текущую сессию.

## TODO-трекер

`TODO.md` в корне - единый источник задач. Прочитай его в начале сессии и обнови статусы после выполнения.

## Быстрый старт

```bash
poetry install              # требует соседний ../DotSoundPrivateCore
cp .env.example .env         # заполнить BOT_TOKEN, BACKEND_BASE_URL, MINI_APP_URL
poetry run python main.py    # long polling + internal API на :8081
```

Бот не работает без запущенного DotSoundBackend.

## Сборка и проверки

| Действие | Команда |
|----------|---------|
| Установка | `poetry install` |
| Запуск | `poetry run python main.py` |
| Тесты | `poetry run pytest` |
| Покрытие | `poetry run pytest --cov=bot` (branch, порог 80%) |
| Lint | `poetry run ruff check .` |
| Формат | `poetry run black .` |
| Typecheck | `poetry run mypy bot/` |
| Boundary guardrail | `python scripts/check_boundary_policy.py` |
| Docker | `docker compose up -d --build` |

Команды - из `pyproject.toml`, `docker-compose.yml`, `.github/workflows/`. Полноценного lint/test CI в публичном репо пока нет (см. `.github/workflows/ci.yml`); активные guardrails - `policy-guardrails.yml`.

## Структура репозитория

```
bot/
├── main.py        # Bot + Dispatcher, polling, internal API, меню Mini App
├── config.py      # BotSettings (pydantic-settings), валидатор loopback-bind
├── api/           # client.py (BackendClient), internal.py (loopback API)
├── handlers/      # base, audio, inline_mode, likes, player, playlists,
│                  #   recommendations, artists, stats, web_auth
├── keyboards/     # фабрики InlineKeyboardMarkup
├── middlewares/   # logging, throttling
├── services/      # file_id_cache (Redis), player_session
├── core/          # structlog logging
├── i18n/          # каталог строк ru/en
└── utils/         # formatting
scripts/  tests/  docs/  Dockerfile  docker-compose.yml
```

## Соглашения

- **Язык документации:** русский (техтермины и команды - как в репо).
- **Линтер/формат/типы:** Ruff + Black + Mypy strict; длина строки **79**.
- **Без комментариев** - код самодокументируется именами; докстринги только где сигнатура не передаёт смысл.
- **Полная асинхронность:** `async/await` везде.
- **Конфиг:** только через `bot/config.py` (pydantic-settings); `os.environ` напрямую запрещён.
- **Слои:** `handlers/` тонкие → `bot/api/client.py` (единственный канал к бэкенду) → DotSoundBackend REST. Не инстанцировать `httpx` в хендлерах. `keyboards/` - фабрики без логики. `middlewares/` - cross-cutting.
- **Тесты:** после каждой новой фичи обязательно (pytest + anyio); branch-coverage не ниже 80%.

## Internal API (loopback)

`bot/api/internal.py` - приватный HTTP-API для backend↔bot, слушает только loopback (`config.py` валидирует bind). Роуты требуют заголовок `X-Internal-Secret`; контракт - в `dotsound_private_core.contracts.internal_api`. Покрывает скачивание аудио по `file_id`, коды входа, уведомления о входе, админ-алерты (chat_id allowlist).

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `BOT_TOKEN` | Токен бота из @BotFather (обязательна) |
| `BACKEND_BASE_URL` | URL DotSoundBackend (обязательна) |
| `MINI_APP_URL` | URL веб-плеера для кнопки меню (обязательна) |
| `REDIS_URL` | Redis для `file_id`-кэша и сессий плеера |
| `INTERNAL_API_SECRET` | Секрет заголовка `X-Internal-Secret` |
| `INTERNAL_API_HOST` / `INTERNAL_API_PORT` | Bind internal API (только loopback) |
| `TELEGRAM_API_PROXY_URL` | HTTP/SOCKS-прокси для Telegram API (опц.) |
| `ADMIN_ALERT_CHAT_ID_ALLOWLIST` | Allowlist chat_id для админ-алертов |
| `BACKUP_NOTIFY_TELEGRAM_ID` | Chat ID для backup-уведомлений |
| `LOG_LEVEL` | Уровень логов (`DEBUG`/`INFO`/`WARNING`) |

Имена - из `bot/config.py`. Не читай `.env`, не коммить секреты.

## Что делать агенту

- Перед правками прочитай затронутые файлы и соседний код.
- После изменений запусти релевантные тесты/lint из таблицы выше.
- **README-sync:** при глобальных изменениях функционала (новые/удалённые команды, хендлеры, модули, зависимости, смена архитектуры или runtime) обнови `README.md` и `AGENTS.md` через скилл `generate-readme` - включая пересчёт LoC. Мелкие правки (опечатки, внутренний рефактор без изменения команд/API) README не трогают.
- Не латай разметку README вручную - перегенерируй скиллом.
- Минимальный diff - не рефактори несвязанный код. Числа, пути, версии - только из репозитория.

## Чего не делать

- Не выдумывать команды, зависимости, env, endpoints.
- Не переносить private-код в публичную ветку без явного подтверждения владельца.
- Не добавлять `<details>`, centered hero, emoji в README DotCore.
- Не менять `docs/cover.svg` без регенерации обложки.
- Не менять `LICENSE` / `NOTICE` без явного запроса (репо - source-available, не open source).
- Не коммитить секреты, токены, `.env`.
- Не удалять маркеры `<!-- loc:start -->` / `<!-- loc:end -->` в README.

## Документация

- [README.md](README.md) - запуск, команды, стек, архитектура
- [docs/ai-boundary-policy.md](docs/ai-boundary-policy.md) - граница public/private
- [docs/private-core-dependency-policy.md](docs/private-core-dependency-policy.md), [docs/private-boundary-inventory.md](docs/private-boundary-inventory.md), [docs/public-release-cut.md](docs/public-release-cut.md)
- [TODO.md](TODO.md) - трекер задач

## DotCore

Проект следует стандарту DotCore: плоский технический README, SVG-обложка DotBioSite, LoC-бейдж. При запросе «обнови README» используй скилл `generate-readme`.
