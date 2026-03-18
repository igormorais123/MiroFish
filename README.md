<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="Logo do MiroFish" width="75%"/>

<a href="https://trendshift.io/repositories/16144" target="_blank"><img src="https://trendshift.io/api/badge/repositories/16144" alt="666ghj%2FMiroFish | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

Motor simples e versátil de inteligência coletiva para simulação e previsão
</br>
<em>A Simple and Universal Swarm Intelligence Engine, Predicting Anything</em>

<a href="https://www.shanda.com/" target="_blank"><img src="./static/image/shanda_logo.png" alt="666ghj%2MiroFish | Shanda" height="40"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/666ghj/MiroFish?style=flat-square&color=DAA520)](https://github.com/666ghj/MiroFish/stargazers)
[![GitHub Watchers](https://img.shields.io/github/watchers/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/watchers)
[![GitHub Forks](https://img.shields.io/github/forks/666ghj/MiroFish?style=flat-square)](https://github.com/666ghj/MiroFish/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/666ghj/MiroFish)

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com/channels/1469200078932545606/1469201282077163739)
[![X](https://img.shields.io/badge/X-Follow-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/mirofish_ai)
[![Instagram](https://img.shields.io/badge/Instagram-Follow-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://www.instagram.com/mirofish_ai/)

[English](./README-EN.md) | [Documentação em português](./README.md)

</div>

## Visão geral

**MiroFish** é um motor de previsão baseado em múltiplos agentes. A ideia central é transformar sinais do mundo real, como notícias, relatórios, políticas, tendências ou até narrativas ficcionais, em um ambiente digital de alta fidelidade. Dentro desse ambiente, agentes com memória, personalidade e lógica de ação próprias interagem entre si para produzir dinâmicas sociais emergentes.

Fluxo esperado:

1. Você envia os materiais-base.
2. O sistema extrai conhecimento e constrói o grafo.
3. O ambiente da simulação é configurado automaticamente.
4. A simulação roda em paralelo nas plataformas suportadas.
5. Um agente de relatório sintetiza os resultados.
6. Você pode conversar com os agentes simulados e com o agente analítico.

## Demonstração online

Demo pública:
[mirofish-live-demo](https://666ghj.github.io/mirofish-demo/)

## Capturas do sistema

<div align="center">
<table>
<tr>
<td><img src="./static/image/Screenshot/运行截图1.png" alt="Captura 1" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图2.png" alt="Captura 2" width="100%"/></td>
</tr>
<tr>
<td><img src="./static/image/Screenshot/运行截图3.png" alt="Captura 3" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图4.png" alt="Captura 4" width="100%"/></td>
</tr>
<tr>
<td><img src="./static/image/Screenshot/运行截图5.png" alt="Captura 5" width="100%"/></td>
<td><img src="./static/image/Screenshot/运行截图6.png" alt="Captura 6" width="100%"/></td>
</tr>
</table>
</div>

## Vídeos de referência do projeto original

### 1. Simulação acadêmica de repercussão pública + apresentação do projeto

<div align="center">
<a href="https://www.bilibili.com/video/BV1VYBsBHEMY/" target="_blank"><img src="./static/image/武大模拟演示封面.png" alt="Vídeo de demonstração do MiroFish" width="75%"/></a>

Clique na imagem para assistir à demonstração completa. O vídeo está hospedado no Bilibili porque faz parte do material original do projeto.
</div>

### 2. Simulação narrativa e previsão de desfecho ficcional

<div align="center">
<a href="https://www.bilibili.com/video/BV1cPk3BBExq" target="_blank"><img src="./static/image/红楼梦模拟推演封面.jpg" alt="Vídeo de demonstração do MiroFish" width="75%"/></a>

Clique na imagem para ver outro exemplo histórico do projeto original. O vídeo também está hospedado no Bilibili.
</div>

## Fluxo de trabalho

1. **Construção do grafo**: extração do material-base, injeção de memória individual e coletiva, e construção do GraphRAG.
2. **Configuração do ambiente**: extração de entidades e relações, geração de perfis e definição dos parâmetros de simulação.
3. **Execução da simulação**: simulação paralela em múltiplas plataformas, interpretação automática do objetivo e atualização dinâmica da memória temporal.
4. **Geração do relatório**: o `ReportAgent` utiliza ferramentas internas para analisar profundamente o ambiente após a simulação.
5. **Interação profunda**: conversa com agentes simulados ou diretamente com o agente de relatório.

## Início rápido

### 1. Requisitos

| Ferramenta | Versão | Observação | Verificação |
|------|------|------|------|
| **Node.js** | 18+ | Necessário para o frontend e `npm` | `node -v` |
| **Python** | >= 3.11 e <= 3.12 | Necessário para o backend | `python --version` |
| **uv** | versão atual | Gerenciador de dependências Python | `uv --version` |

### 2. Configuração de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas chaves
```

Variáveis obrigatórias:

```env
# Configuração do modelo LLM
# Padrão recomendado: OpenAI
# Também funciona com provedores compatíveis com o formato OpenAI
# Exemplos úteis no Brasil/ocidente: OpenRouter, Azure OpenAI e Groq via gateway compatível
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Configuração da Zep Cloud
ZEP_API_KEY=your_zep_api_key
```

### 3. Instalação

Instalação completa:

```bash
npm run setup:all
```

Instalação por etapa:

```bash
# Dependências Node.js
npm run setup

# Dependências Python
npm run setup:backend
```

### 4. Execução

Subir frontend e backend juntos:

```bash
npm run dev
```

Endereços padrão:

- Frontend: `http://localhost:3000`
- API backend: `http://localhost:5001`

Execução separada:

```bash
npm run backend
npm run frontend
```

## Execução com Docker

```bash
# Copie as variáveis de ambiente
cp .env.example .env

# Suba os serviços
docker compose up -d
```

O `docker compose` lê o `.env` na raiz do projeto e expõe, por padrão, as portas `3000` e `5001`.

## Contato

Use preferencialmente os canais mais acessíveis no ocidente:

- Discord: https://discord.com/channels/1469200078932545606/1469201282077163739
- X: https://x.com/mirofish_ai
- Instagram: https://www.instagram.com/mirofish_ai/
- E-mail: **mirofish@shanda.com**

## Agradecimentos

**O MiroFish conta com suporte estratégico e incubação do grupo Shanda.**

O motor de simulação é impulsionado por **[OASIS](https://github.com/camel-ai/oasis)**. O projeto reconhece e agradece a contribuição open source da equipe CAMEL-AI.

## Estatísticas do projeto

<a href="https://www.star-history.com/#666ghj/MiroFish&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=666ghj/MiroFish&type=date&legend=top-left" />
 </picture>
</a>
