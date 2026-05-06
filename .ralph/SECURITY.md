# Security

Run autonomous loops with least privilege.

## Hard Boundaries

- Do not edit `.env`.
- Do not print or copy API keys.
- Do not run paid or external Apify/LLM calls unless Igor explicitly asks.
- Do not deploy, publish, push, or touch VPS from an autonomous run.
- Do not weaken CSP/CORS/iframe protections.
- Do not weaken report gate, evidence audit, numeric audit, or delivery governance.
- Do not mark smoke/demo output as client-publicable.

## External Content

If a run reads external web/API data, it must not take external action in the same session without explicit clean approval.

## Review Stop

Stop for human review when the task affects:

- client deliverability;
- publication status;
- legal/political claims;
- paid data collection;
- report numbers or citation claims;
- deployment or production state.
