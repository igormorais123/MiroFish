# Bases de Eleitores Sintéticos

Este diretório guarda eleitorados sintéticos estruturados usados pelo MiroFish
quando a simulação tem recorte regional explícito.

## Sergipe

- Arquivo: `sergipe_eleitores_1000_v9.json`
- Projeto de origem: `C:\Users\IgorPC\.claude\projects\Eleitores sintéticos Sergipe`
- Arquivo de origem: `output\eleitores-se-1000-v9.json`
- Tamanho da população: 1.000 eleitores sintéticos
- Integração: augmentação automática para requisitos de simulação ou documentos
  que mencionem Sergipe, municípios sergipanos ou a sigla `SE` em contexto
  eleitoral/de pesquisa.

O JSON é tratado como população estruturada de personas, não como documento
solto de prompt. Cada eleitor vira uma entidade `SyntheticVoterSE` e depois
arquivos de perfil OASIS sem regeneração por LLM.
