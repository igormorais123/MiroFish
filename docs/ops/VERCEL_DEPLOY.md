# Vercel — alternativa histórica do frontend MiroFish INTEIA

> Estado em 2026-07-24: Vercel não serve o domínio público canônico. O produto
> `https://inteia.com.br/mirofish/` é servido pelo nginx da VPS a partir do
> container `mirofish-inteia`. Para produção, use
> [`FONTE_UNICA_VERDADE_MIROFISH.md`](FONTE_UNICA_VERDADE_MIROFISH.md) e
> [`COMANDOS_SEGUROS_MIROFISH.md`](COMANDOS_SEGUROS_MIROFISH.md). Este arquivo
> preserva somente a configuração da alternativa estática.

## Identificação do projeto

| Campo | Valor |
|-------|-------|
| Project name | `mirofish-inteia` |
| Project ID | `prj_enAVMOreJOeLH7VFrOzY9UIzF98s` |
| Org / Team ID | `team_Af2JN68IUUA7lwsIGKuJiN66` |
| CLI context observado | `igormorais123s-projects` |
| CLI user observado | `inteia` |
| URL direta Vercel | https://mirofish-inteia.vercel.app |
| Domínio público canônico | https://inteia.com.br/mirofish/ — servido pela VPS |
| Papel atual | alternativa estática sem segredos server-side |

> Esses IDs vêm de `.vercel/project.json`, gerado por `vercel link`. **`.vercel/` está no `.gitignore`** — cada máquina/instância faz seu próprio `vercel link` se precisar usar a CLI.

## Roteamento histórico do domínio público

Em 2026-05-09, `https://inteia.com.br/mirofish` foi roteado pelo projeto Vercel
raiz `frontend`. Esse estado foi substituído em 2026-07-15 pelo nginx da VPS.
As rotas abaixo são registro histórico e não devem ser publicadas sem uma
decisão explícita de cutover.

Rotas ativas no projeto Vercel `frontend`:

| Ordem | Origem | Destino |
|-------|--------|---------|
| 1 | `^/mirofish/api(?:/(.*))?$` | `https://mirofish.inteia.com.br/api/$1` |
| 2 | `^/mirofish/assets/(.*)$` | `https://mirofish-inteia.vercel.app/assets/$1` |
| 3 | `^/mirofish(?:/(.*))?$` | `https://mirofish-inteia.vercel.app/mirofish/$1` |

Motivo: a rota antiga servia uma cópia estática cacheada dentro do projeto `frontend`. A API não deve apontar direto para IP ou porta da VPS; use o Nginx público `https://mirofish.inteia.com.br/api/...`.

`https://mirofish.inteia.com.br/` não é URL de uso do produto. A raiz do subdomínio redireciona para `https://inteia.com.br/mirofish/`, mas `/api/...` e `/health/...` permanecem como ponte controlada para o backend.

Comandos úteis:

```bash
# Rode os comandos a partir da raiz do projeto Mirofish INTEIA
# (onde fica o vercel.json). Sem --cwd quando voce ja esta no diretorio.
vercel routes list
vercel routes list --diff
vercel routes publish --yes
```

## Configuração de build (declarativa)

Está em [`vercel.json`](../../vercel.json) na raiz:

```json
{
  "installCommand": "npm install && cd frontend && npm install",
  "buildCommand": "npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

- **Install**: roda no root (deps de scripts) e depois entra em `frontend/` (deps do Vite/Vue).
- **Build**: `npm run build` na raiz delega pro frontend (ver `package.json` raiz).
- **Output**: `frontend/dist` é o que vai pra CDN.
- **Rewrites**: SPA fallback — toda rota desconhecida cai em `index.html` para o Vue Router resolver.

## Branches e deploys

| Branch | Tipo de deploy | URL |
|--------|---------------|-----|
| `main` | Produção direta da alternativa | https://mirofish-inteia.vercel.app/mirofish |
| qualquer outra | Preview | `https://mirofish-inteia-<branch-slug>-<team>.vercel.app` |

Se a integração Vercel estiver ativa, push para `main` pode atualizar apenas a
URL direta da alternativa. Isso não publica o domínio canônico. Branches podem
gerar previews conforme a integração instalada.

## Como publicar esta alternativa

Publicar ou promover Vercel é uma mudança externa separada do deploy público e
requer autorização específica. O fluxo canônico continua sendo branch, PR,
merge e publicação na VPS.

```bash
# requer Vercel CLI: npm i -g vercel
vercel link              # primeira vez na máquina
vercel --prod            # NÃO use sem confirmar com Igor
```

## Variáveis de ambiente

**Não estão no Git.** Configuradas no painel Vercel: Settings → Environment Variables.

Fonte canônica de nomes e política: [`SEGREDOS_E_AMBIENTES_MIROFISH.md`](SEGREDOS_E_AMBIENTES_MIROFISH.md).

Estado aplicado em 2026-05-06:

- `VITE_BASE=/mirofish/` em **Production**. Esta variável é pública por definição (`VITE_`) e só controla o prefixo de assets do build publicado em `https://inteia.com.br/mirofish`.
- Nenhum token server-side foi enviado para a Vercel. Não copie `.env` local para Vercel produção sem revisar, porque segredos e valores de desenvolvimento com `localhost` quebram ou vazam o ambiente publicado.

Para listar (precisa Vercel CLI + login):

```bash
vercel env ls
vercel env pull frontend/.env.local   # baixa pra desenvolver local
```

Se você precisar adicionar uma variável de ambiente nova, **abra PR com a documentação no `docs/ops/`** explicando o que adicionou e por quê — a variável em si vai pelo painel da Vercel, mas o registro de existir tem que estar no Git.

## Rollback da alternativa

Pelo painel Vercel:
1. Deployments → encontre o deploy anterior estável
2. clique nos três pontos → **Promote to Production**

Pelo Git (mais lento):
```bash
git revert <sha-do-commit-quebrado>
git push origin main
# a integração Vercel, se ativa, cria um novo deploy direto
```

## Relação com a produção

- o DNS atual de `inteia.com.br` aponta para a VPS principal;
- a falha ou o sucesso de `mirofish-inteia.vercel.app` não prova o estado da produção;
- nunca usar Vercel para contornar um incidente da VPS sem plano de cutover,
  segurança, rollback e autorização.

## Não mexer sem permissão

- `vercel.json` (raiz)
- `.github/workflows/` (CI que valida antes do merge)
- Domínios e DNS no painel Vercel
- Variáveis de ambiente em produção (Settings → Environment Variables)

## Checklist antes de mergear pra `main`

- [ ] `cd frontend && npm run build` passa local
- [ ] Se a alternativa foi alterada, sua URL direta ou preview abre sem erro
- [ ] Não há `console.error` nas DevTools da superfície validada
- [ ] PR descreve **o que muda**, **por que**, **como testar**
- [ ] Se mudou variável de ambiente: documentado + adicionada no painel Vercel
- [ ] CI verde (GitHub Actions)

## Observações

- **Cache de preview de link** (WhatsApp/Telegram/etc) NÃO se renova com novo deploy. Use Facebook Debugger https://developers.facebook.com/tools/debug/ depois de mudar `og:image`.
- **`og:image`** apontando pra `https://inteia.com.br/mirofish/inteia_mirror.png` (definido em `frontend/index.html`). Se mudar, atualizar também o cache via Debugger.
- Se a URL Vercel estiver atualizada e a produção não, isso é esperado: são
  superfícies independentes. Diagnostique o checkout, container e nginx da VPS.
