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

## Плеер в боте

- [x] Inline аудио-плеер (3 трека, editMessageMedia)
- [x] Выбор источника: Мои / Лайки / Лента
- [x] file_id кэш в Redis
- [x] Предзагрузка следующей пачки (prefetch)
- [x] Фильтрация треков без файлов (playable_only на backend)
- [x] Исправление пагинации (internal_user_id vs telegram_id)
- [x] Fallback с try/except + свежий URL при ошибках
- [ ] Расширить источники: плейлисты, подписки, рекомендации
- [x] Shuffle / Random режим
- [ ] Кнопка "Назад" (предыдущая пачка)

## Логирование

- [x] JSON structlog для production (json_output параметр)
- [ ] Structured logging для всех handlers (bind context)

## Инфраструктура

- [ ] Dockerfile для бота (production)
- [ ] docker-compose.yml с logging driver
- [ ] Health endpoint для мониторинга

## Безопасность

- [x] Scoped JWT через internal-token (backend)
- [x] TTL-aware кэш токенов (12 мин)
- [x] Rate limit на callback_query плеера (per-user)

## Интеграция с backend

- [ ] WebSocket: приём player.command для синхронизации с Mini App
- [ ] Уведомления о бэкапах через бота (BACKUP_NOTIFY_TELEGRAM_ID)

---

*Последнее обновление: 2026-04-13 агентом*
