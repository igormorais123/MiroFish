# Verification Strategy

Mode: code

## Default Check

Run:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -q
npm run build
git diff --check
```

If `.venv` is unavailable, use:

```powershell
python -m pytest backend\tests -q
```

## Mirofish-Specific Proof

For backend/gate/report work, prove at least one of:

- tests covering `backend/app/services/*` pass;
- report/system gate output is supported by local evidence;
- client/demo governance remains separated;
- numeric/citation audit still blocks unsupported claims;
- no external LLM/Apify/deploy action was required.

For frontend work, prove:

- `npm run build` passes;
- changed screen/state is named;
- if UI is material, verify with browser/screenshot before closing.

## Human Required

Stop when verification needs real paid APIs, LLM keys, Apify token, deploy credentials, VPS, client publication, long simulation spend, or legal/reputational decision.
