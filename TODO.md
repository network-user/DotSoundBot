# DotSoundBot — TODO Tracker

> Этот файл поддерживается автоматически ИИ-агентом.
> Агент обязан: (1) прочитать этот файл в начале сессии,
> (2) обновить статусы после выполнения задач,
> (3) добавить новые задачи если они возникли.

## Статусы

- `[ ]` — не начато
- `[~]` — в процессе
- `[x]` — завершено
- `[-]` — отменено / неактуально

---

- [x] **Telegram Bot API proxy startup guard (2026-05-15)**
  - Bot startup now normalizes proxy URL env artifacts such as matching
    quotes and inline comments before constructing aiogram session.
  - `TELEGRAM_API_PROXY_URL` now accepts comma-separated proxy candidates
    and uses the first valid URL.
  - Invalid Telegram API proxy URL no longer crashes the process during
    startup; the bot logs `telegram_api_proxy_invalid` and falls back to
    direct Telegram API session.
  - Added regression tests for proxy normalization and invalid-port
    fallback.

- [x] **Telegram Bot API proxy (2026-05-15)**
  - Added `TELEGRAM_API_PROXY_URL` so Telegram profile-audio listing and
    file downloads can use a server-side HTTP/SOCKS proxy or Tor endpoint.
  - Added `aiohttp-socks` dependency for SOCKS proxy support in aiogram.

## Плеер в боте

- [x] Inline аудио-плеер (3 трека, editMessageMedia)
- [x] Выбор источника: Мои / Лайки / Лента
- [x] file_id кэш в Redis
- [x] Предзагрузка следующей пачки (prefetch)
- [x] Фильтрация треков без файлов (playable_only на backend)
- [x] Исправление пагинации (internal_user_id vs telegram_id)
- [x] Fallback с try/except + свежий URL при ошибках
- [x] Расширить источники: плейлисты, подписки, рекомендации
- [x] Shuffle / Random режим
- [x] Кнопка "Назад" (предыдущая пачка)

## Логирование

- [x] JSON structlog для production (json_output параметр)
- [x] Structured logging для всех handlers (bind context)

## Инфраструктура

- [x] Dockerfile для бота (production)
- [x] docker-compose.yml с logging driver
- [x] Health endpoint для мониторинга

## Безопасность

- [x] Scoped JWT через internal-token (backend)
- [x] TTL-aware кэш токенов (12 мин)
- [x] Rate limit на callback_query плеера (per-user)

## Интеграция с backend

- [ ] WebSocket: приём player.command для синхронизации с Mini App
- [x] Уведомления о бэкапах через бота (BACKUP_NOTIFY_TELEGRAM_ID)

---

*Последнее обновление: 2026-05-15 агентом*
