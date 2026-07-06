# Security Audit · Amber Relay · 2026-07-06

| Поле | Значение |
|------|----------|
| Статус | PASSED |
| Прогон | amber-relay |
| Уровень | full |
| Охват | leaks + code |
| Модель | Claude Opus 4.8 |
| Дата | 2026-07-06 |

## Сводка

```
Трек A · Секреты/ключи:    0  (Crit 0 / High 0)
Трек A · PII/экспозиция:    0
Трек A · История git:       0  (79 коммитов проверены)
Трек B · Инъекции/exec:     2
Трек B · Authz/крипто/деф.: 9
Трек B · Зависимости:       3
Инфра/CI:                   3
──────────────────────────────────────────────
Severity: Crit 0 · High 0 · Med 0 · Low 13 · Info 5
Готовность: 9/10
Вердикт: PASSED
```

Методика: полный аудит, веер из 7 подагентов по измерениям (утечки, зависимости, инфра/CI,
инъекции/SSRF/path, authz/IDOR, крипто/секреты/десериализация, дефолты/DoS) + adversarial-verify
находки уровня High. Затем - раунд ремедиации: все Medium устранены в коде/инфраструктуре либо
переклассифицированы по существу. Секреты не читались и не выводились; улики маскированы.

Первый прогон дал вердикт PASSED WITH WARNINGS (6 Medium). После ремедиации (см. ниже) открытых
Critical/High/Medium не осталось - вердикт повышен до PASSED.

## Устранено в этом прогоне (были Medium)

| Было | Файл | Что сделано |
|------|------|-------------|
| Admin-allowlist пустой = allow-all | `bot/api/internal.py` | Пустой allowlist теперь **fail-closed**: `if not allowlist -> 403`. Разделены ветки «не сконфигурирован» и «chat_id не в списке». Тест `test_admin_alert_denied_when_no_allowlist` фиксирует deny. |
| Always-on INFO-лог контента/PII | `bot/core/logging.py` | `message_text`, `inline_query` добавлены в `_FULL_REDACT_KEYS` (полная редакция при `redact_logs=True`, дефолт); `chat_id` добавлен в correlation/sensitive и маскируется как `user_id`. |
| Dockerfile `curl \| python3 -` для Poetry | `Dockerfile` | Poetry ставится из **pinned** `poetry==${POETRY_VERSION}` в изолированный venv под `POETRY_HOME` (никакого выполнения удалённого скрипта из shell); `curl` убран из builder. |
| `deploy.yml` ssh-action на подвижном теге | `.github/workflows/deploy.yml` | Запиннено на неизменяемый commit SHA `029f5b4aeeeb58fdfe1410a5d17f967dacf36262` (# v1.0.3), резолв через `git ls-remote` github.com. |
| CODEOWNERS плейсхолдер `@your-github-username` | `.github/CODEOWNERS` | Нерабочие плейсхолдер-правила удалены (не создают ложного впечатления ревью-гейта); оставлена инструкция, как включить owners. |
| Local-path dep `dotsound-private-core` | `pyproject.toml` | Переклассифицировано **Medium → Low**: зависимость by-design приватного ядра (public/private split), задокументирована, у атакующего пути эксплуатации нет. Остаётся как Low-заметка ниже. |

Верификация: `poetry run pytest` - 294 passed; `python scripts/check_boundary_policy.py` - passed;
правки не внесли новых ruff-замечаний. Примечание: изменение `Dockerfile` не проверено сборкой
локально (нет docker + нужен родительский build-контекст с приватным ядром); паттерн изолированного
venv под `POETRY_HOME` повторяет семантику прежнего официального инсталлятора (Poetry ставит deps в
системный site-packages, т.к. его префикс = data_dir).

## Проверено и подтверждено безопасным

- **Утечки:** ни в рабочем дереве, ни в истории всех 79 коммитов нет секретов, токенов, приватных ключей, PII или machine-paths. `.gitignore` закрывает `.env*`, `*.pem/key/p12/pfx`, `secrets.json`, БД, venv.
- **RCE/инъекции:** нет `os.system`/`subprocess`/`eval`/`exec`/`pickle`/`yaml.load` во всём репо. Backend-пути int-типизированы (path traversal невозможен). HTML-синки экранируются. Query-параметры кодируются httpx.
- **AuthZ:** IDOR-фикс в `playlists.py` полный. Internal API сравнивает секрет через `hmac.compare_digest` (constant-time, fail-closed). Принципал всегда из `update.from_user.id`. Player-сессии и лайки изолированы по пользователю.
- **Крипто/десериализация:** Redis хранит только plain-строки (не pickle). TLS нигде не отключён. Login-коды генерируются в приватном ядре.
- **DoS/дефолты:** loopback-bind валидатор корректен. Sweep устаревших player-сессий работает, in-memory структуры ограничены. httpx-таймауты заданы, ретраев нет. Стек-трейсы клиенту не отдаются.

## Остаточные находки (Low / Info - hardening-бэклог, гейт не блокируют)

| Severity | Категория | Файл:строка | Описание | Рекомендация |
|----------|-----------|-------------|----------|--------------|
| Low | SSRF (в глубину) | `bot/handlers/player.py:189`, `bot/api/client.py:293-304` | `URLInputFile(data["url"])` для stream-URL без allowlist схемы/хоста (URL из доверенного бэкенда). | Валидировать `scheme==https` + хост по allowlist перед `URLInputFile`. |
| Low | AuthZ / fail-open | `bot/api/client.py:256-274` | При ошибке получения токена `get_playlist_detail`/`get_user_playlists`/`create_playlist` уходят в бэкенд без Authorization. | Прерывать запрос при невозможности получить токен. |
| Low | Дефолт / footgun | `bot/config.py:30,37-61` | `internal_api_secret` дефолтит в `""`; fail-closed, но деплой без секрета молча ломает internal-auth. | Требовать непустой секрет на старте (fail-fast). |
| Low | Дефолт / OOM (условно) | `bot/handlers/audio.py:65-69,145-149` | Нет явного code-level cap на `file_size` перед `download_file` (безопасно на стандартном Bot API 20 MB; self-hosted 2 GB → OOM). | Добавить guard `audio.file_size > 20 MB`. |
| Low | DoS / contention | `bot/handlers/audio.py:19` | Глобальный `Semaphore(2)` на все аплоады - крупные файлы держат оба слота. | Разделить лимит конкуренции и per-file size guard. |
| Low | Дефолт / size-cap bypass | `bot/api/internal.py:169-172` | Cap пропускается при `file_size` = `None`/`0` (loopback + секрет - охват низкий). | Трактовать отсутствующий размер как недоверенный. |
| Low | Крипто / hardening | `bot/config.py:17,26,30` | `bot_token`, `internal_api_secret`, `redis_url` - plain `str`, не `SecretStr`. | Типизировать секретные поля как `SecretStr`. |
| Low | Зависимости | `pyproject.toml:12,25,22` | `httpx 0.27.2` / `ruff 0.5.7` отстают (известных CVE нет); `pytest-anyio = "*"` без границ. | Обновить; зафиксировать нижнюю границу `pytest-anyio`. |
| Low | Зависимости / supply-chain | `pyproject.toml:16` | `dotsound-private-core` - local-path dep без hash-пиннинга (by-design приватного ядра). | Контролируемый источник при переносе на CI/деплой. |
| Low | Инфра / hardening | `docker-compose.yml:17-26` | Redis без `requirepass` (портов наружу нет). | `requirepass` из env-секрета. |
| Low | Инфра / hardening | `Dockerfile`, `docker-compose.yml:18`, `policy-guardrails.yml` | Базовые образы/actions на подвижных тегах, не digest/SHA. | Пиннинг по digest/SHA. |
| Info | HTML | `bot/utils/formatting.py:15` | `safe_html(quote=False)` сейчас безопасно (данные только в тексте элементов). | Заметка на будущее. |
| Info | AuthZ / boundary | `bot/api/client.py:149-180` | `get_user_profile/stats/login-history` - plain GET без токена; бот всегда шлёт `from_user.id`, IDOR не вносит; authz делегирован бэкенду. | Убедиться в enforcement на бэкенде. |
| Info | Крипто | `bot/handlers/web_auth.py`, `bot/api/internal.py:238` | Генерация/энтропия login-кодов - в приватном ядре, из публичного клиента не аудируются. | Аудировать PRNG/хеш в `dotsound_private_core`. |
| Info | Инфра / CI | `.github/workflows/ci.yml` | Файл - заглушка без `on:`/`jobs:`; lint/test CI фактически отключён. | Включить lint/test CI-гейт. |
| Info | Дефолты (позитив) | `bot/api/client.py`, `bot/middlewares/throttling.py`, `bot/services/file_id_cache.py` | Подтверждены хорошие дефолты: httpx timeouts, отсутствие ретраев, TTL-sweep throttle, 7-дневный TTL кэша, opaque error codes. | Наблюдение. |
