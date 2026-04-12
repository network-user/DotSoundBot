# DotSoundBot Private Boundary Inventory

## Scope

This file defines which parts of `DotSoundBot` stay public and which
parts delegate private rules to `DotSoundPrivateCore`.

## Public In DotSoundBot

- Telegram handlers and UX messages.
- Keyboard builders and callback wiring.
- Public backend API client for regular bot features.
- Dispatcher/bootstrap and middleware registration.

## Private Candidates Migrated To DotSoundPrivateCore

- `bot/handlers/web_auth.py`
  - internal auth code endpoint route binding
  - internal secret header shaping
- `bot/api/internal.py`
  - internal secret header constants
  - internal bridge endpoint constants

## Private Candidates Planned For Later Slices

- Internal anti-abuse transport constraints.
- Privileged internal-only bridge extensions.

## Non-Goals For Slice-1

- No UI text migration from bot handlers.
- No changes in user-facing bot command behavior.
- No protocol changes for regular backend client calls.

