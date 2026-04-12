## Summary

- [ ] User-facing behavior remains backward-compatible
- [ ] Sensitive bridge logic stays in `DotSoundPrivateCore`

## Boundary Checklist

- [ ] I did not hardcode internal bridge constants in public code
- [ ] I did not add secrets or privileged tokens to source files
- [ ] I updated boundary docs when changing public/private scope

## Verification

- [ ] Boundary policy check passed
- [ ] Tests relevant to the change passed

