# Aprendizado

## O que funcionou

- Mirofish e muito melhor candidato que Paperclip local para aprovar o metodo agora.
- O projeto ja tem AutoResearch proprio em `backend/autoresearch`.
- A verificacao e objetiva: backend tests + frontend build.

## O que nao funcionou

- `uv` nao estava no PATH desta sessao, apesar de existir `uv.lock`.
- A verificacao deve preferir `.\\backend\\.venv\\Scripts\\python.exe`.

## Gotchas para o proximo ciclo

- Nao rodar simulacao longa com LLM ativo sem aprovacao.
- Nao tocar `.env`.
- Nao enfraquecer gates de relatorio nem auditoria numerica/citacoes.

## Deve virar melhoria no metodo?

Sim.

Alvos:

- `.ralph/VERIFY.md`
- `.ralph/SECURITY.md`

## AutoResearch

- method_signal: `weak_verification`
- candidate_targets: `.ralph/VERIFY.md`, `.ralph/SECURITY.md`
- experiment_recommended: `false`

Motivo: primeiro run no Mirofish. Acumular mais 2 runs antes de propor patch.
