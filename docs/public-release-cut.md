# DotSoundBot Public Release Cut

## Included In Public Repository

- User-facing handlers and keyboards.
- Public backend API client integration.
- Bot bootstrap and middleware wiring.
- Tests and developer tooling.

## Excluded Or Delegated To Private Core

- Internal bridge constants and secret-header transport policy.
- Internal auth bridge URL and request shaping rules.
- Future anti-abuse transport constraints.

## Pre-Publish Checklist

- [x] No hardcoded internal bridge constants in public modules.
- [x] No secrets in source.
- [x] `docs/ai-boundary-policy.md` reflects current boundaries.
- [x] CI guardrails and CODEOWNERS are enabled.
- [x] License and usage restrictions are present.

