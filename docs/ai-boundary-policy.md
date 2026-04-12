# DotSoundBot AI Boundary Policy

## Purpose

This repository is a public showcase thin client. Sensitive logic is
implemented in `DotSoundPrivateCore`.

## Public Zone

- Telegram handlers and user-facing bot UX.
- Keyboard builders and callback wiring.
- Public backend client integration.

## Private Zone

- Internal bridge constants and secret-header policy.
- Internal auth bridge rules.
- Future risk and anti-abuse transport policies.

## Mandatory Rules For Any AI Agent

1. Keep handlers thin and user-facing.
2. Do not inline private bridge constants in public code.
3. Implement sensitive bridge logic via `dotsound_private_core`.
4. If scope is unclear, stop and request explicit confirmation.

## Enforcement

- CI runs `scripts/check_boundary_policy.py`.
- CODEOWNERS protection is required for boundary docs and guardrails.
- Secret scanning runs in CI for every PR and push.

