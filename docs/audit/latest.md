> Последний прогон: amber-relay · 2026-07-06. Снимок: [2026-07-06-amber-relay.md](2026-07-06-amber-relay.md) · история: [docs/audit/](.)

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

Полный аудит (веер из 7 подагентов + adversarial-verify) с последующим раундом ремедиации: все 6
Medium первого прогона устранены в коде/инфраструктуре либо переклассифицированы по существу.
Открытых Critical/High/Medium нет. Секреты не выводились; улики маскированы.

## Устранено в этом прогоне (были Medium)

| Было | Файл | Что сделано |
|------|------|-------------|
| Admin-allowlist пустой = allow-all | `bot/api/internal.py` | Пустой allowlist теперь fail-closed (`403`); тест фиксирует deny. |
| Always-on INFO-лог контента/PII | `bot/core/logging.py` | `message_text`/`inline_query` - полная редакция; `chat_id` маскируется. |
| Dockerfile `curl \| python3 -` для Poetry | `Dockerfile` | Poetry из pinned pip в изолированный venv; удалённый скрипт не выполняется. |
| `deploy.yml` ssh-action на подвижном теге | `.github/workflows/deploy.yml` | Запиннено на commit SHA `029f5b4a…` (# v1.0.3). |
| CODEOWNERS плейсхолдер | `.github/CODEOWNERS` | Нерабочие плейсхолдер-правила удалены. |
| Local-path dep | `pyproject.toml` | Переклассифицировано Medium → Low (by-design приватного ядра). |

Верификация: `pytest` - 294 passed; boundary-guardrail - passed; новых lint-замечаний нет.
Полный список остаточных Low/Info и раздел «проверено безопасным» - в снимке
[2026-07-06-amber-relay.md](2026-07-06-amber-relay.md).
