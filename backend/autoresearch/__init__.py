"""
AutoResearch INTEIA — Loop autonomo de otimizacao por experimentacao.

Adaptacao da arquitetura de 3 arquivos do Karpathy (program.md / train.py / prepare.py)
para o ecossistema INTEIA: constraints.yaml / asset editavel / evaluator.py.

O engine roda hipoteses via LLM (haiku), modifica o asset, avalia o resultado,
e mantém melhorias (git commit) ou reverte falhas (git reset).
"""

__version__ = "0.1.0"
