# Vercel — Deploy do frontend MiroFish INTEIA

> Documento operacional para qualquer agente IA ou humano que precise mexer em deploy.

## Identificação do projeto

| Campo | Valor |
|-------|-------|
| Project name | `mirofish-inteia` |
| Project ID | `prj_enAVMOreJOeLH7VFrOzY9UIzF98s` |
| Org / Team ID | `team_Af2JN68IUUA7lwsIGKuJiN66` |
| CLI context observado | `igormorais123s-projects` |
| CLI user observado | `inteia` |
| URL direta Vercel | https://mirofish-inteia.vercel.app |
| Site público | https://inteia.com.br/mirofish |
| Plataforma | Vercel (Hobby/Pro — verificar com Igor) |

> Esses IDs vêm de `.vercel/project.json`, gerado por `vercel link`. **`.vercel/` está no `.gitignore`** — cada máquina/instância faz seu próprio `vercel link` se precisar usar a CLI.

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
| `main` | **Production** | https://inteia.com.br/mirofish |
| qualquer outra | Preview | `https://mirofish-inteia-<branch-slug>-<team>.vercel.app` |

**Push pra `main` faz deploy de produção automaticamente.** Push pra qualquer outra branch (`feat/...`, `codex/...`, `chore/...`) cria um deploy de preview com URL própria — útil pra revisar antes de mergear.

## Como publicar em produção

### Caminho preferido (todos os agentes IA devem usar este):

```bash
# 1. Sua mudança está numa branch e tem PR aberto pra main
gh pr view <num> --web    # confirmar que CI passou e o preview deploy está OK
gh pr merge <num> --squash --delete-branch   # ou merge no UI do GitHub
# Vercel publica produção sozinho ao detectar push em main
```

### Caminho de hotfix (só com aprovação direta do Igor):

```bash
# requer Vercel CLI: npm i -g vercel
vercel link              # primeira vez na máquina
vercel --prod            # NÃO use sem confirmar com Igor
```

## Variáveis de ambiente

**Não estão no Git.** Configuradas no painel Vercel: Settings → Environment Variables.

Para listar (precisa Vercel CLI + login):

```bash
vercel env ls
vercel env pull frontend/.env.local   # baixa pra desenvolver local
```

Se você precisar adicionar uma variável de ambiente nova, **abra PR com a documentação no `docs/ops/`** explicando o que adicionou e por quê — a variável em si vai pelo painel da Vercel, mas o registro de existir tem que estar no Git.

## Rollback

Pelo painel Vercel:
1. Deployments → encontre o deploy anterior estável
2. clique nos três pontos → **Promote to Production**

Pelo Git (mais lento):
```bash
git revert <sha-do-commit-quebrado>
git push origin main
# Vercel faz novo deploy de produção em ~2min
```

## Marketplace / integrações em uso

- (a confirmar com Igor) — domínio custom `inteia.com.br/mirofish` é roteado por DNS apontando pro Vercel ou por um proxy reverso na VPS.
- Se o site público falhar mas o deploy Vercel direto (`mirofish-inteia.vercel.app`) funcionar, é problema de proxy/DNS, não de build.

## Não mexer sem permissão

- `vercel.json` (raiz)
- `.github/workflows/` (CI que valida antes do merge)
- Domínios e DNS no painel Vercel
- Variáveis de ambiente em produção (Settings → Environment Variables)

## Checklist antes de mergear pra `main`

- [ ] `cd frontend && npm run build` passa local
- [ ] Preview deploy do Vercel (URL no PR) abre sem erro
- [ ] Não há `console.error` nas DevTools no preview
- [ ] PR descreve **o que muda**, **por que**, **como testar**
- [ ] Se mudou variável de ambiente: documentado + adicionada no painel Vercel
- [ ] CI verde (GitHub Actions)

## Observações

- **Cache de preview de link** (WhatsApp/Telegram/etc) NÃO se renova com novo deploy. Use Facebook Debugger https://developers.facebook.com/tools/debug/ depois de mudar `og:image`.
- **`og:image`** apontando pra `https://inteia.com.br/mirofish/inteia_mirror.png` (definido em `frontend/index.html`). Se mudar, atualizar também o cache via Debugger.
