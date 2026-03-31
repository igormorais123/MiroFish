# AutoResearch INTEIA v2 — Plano de Implantação

> De hill climbing manual para sistema evolucionário autônomo com memória persistente.
> Baseado em: Karpathy AutoResearch, Agent Zero, OPRO, DSPy MIPROv2, TextGrad, PromptBreeder.

---

## Estado Atual (v1)

```
engine.py          → Hill climbing: 1 hipótese por vez, sem memória entre sessões
experiment_log.py  → JSONL append-only, sem consolidação cross-session
git_ops.py         → Snapshot/commit/revert atômico
cost_guard.py      → Budget USD + tempo
targets/           → 4 alvos (hookify F1=0.9705, skill, genetic, frontend)
cli.py             → CLI manual: run + baseline
```

**Limitações**: busca sequencial (lenta), sem memória entre runs, corpus fixo, sem paralelismo, sem auto-referência.

---

## Arquitetura Alvo (v2)

```
backend/autoresearch/
├── engine.py                    # Loop base (hill climbing) — MANTER como fallback
├── engines/
│   ├── population.py            # [FASE 2] Busca populacional (PBT + Tournament)
│   ├── island_model.py          # [FASE 2] Múltiplas ilhas com migração
│   └── simulated_annealing.py   # [FASE 5] Refinamento local pós-convergência
├── memory/
│   ├── cross_session.py         # [FASE 1] Memória persistente entre sessões
│   ├── pattern_ranker.py        # [FASE 1] Ranking OPRO-style dos melhores
│   └── transfer.py              # [FASE 6] Transferência entre alvos
├── evolution/
│   ├── operators.py             # [FASE 2] Operadores de mutação + crossover
│   ├── selection.py             # [FASE 2] Tournament, Elitist, Rank-based
│   ├── adaptive_ops.py          # [FASE 3] MAB (UCB1/Thompson) para seleção de operadores
│   └── promptbreeder.py         # [FASE 6] Auto-referencial (evolui mutation-prompts)
├── corpus/
│   ├── adversarial.py           # [FASE 4] Geração adversarial de test cases
│   └── curriculum.py            # [FASE 5] Ordenação fácil→difícil
├── parallel/
│   ├── evaluator.py             # [FASE 3] Avaliação paralela (ProcessPool + asyncio)
│   └── rate_limiter.py          # [FASE 3] Rate limiting para APIs LLM
├── scheduler/
│   ├── cron_runner.py           # [FASE 7] Daemon/cron para runs autônomas
│   └── overnight.py             # [FASE 7] Configuração de runs overnight
├── textgrad/
│   └── gradient_feedback.py     # [FASE 5] Gradientes textuais (críticas direcionadas)
├── dashboard/
│   └── report.py                # [FASE 7] Relatório HTML de progresso
├── targets/                     # Existente — expandir
├── corpora/                     # Existente — expandir com adversariais
├── results/                     # Existente — logs JSONL
├── cost_guard.py                # Existente — OK
├── experiment_log.py            # Existente — expandir com cross-session
├── git_ops.py                   # Existente — expandir com branches paralelas
└── cli.py                       # Existente — expandir com novos comandos
```

---

## Fases de Implantação

### FASE 1: Memória Entre Sessões + Ranking OPRO (2-3h)
**Impacto**: Alto | **Esforço**: Baixo | **Custo LLM**: Zero | **Dependências**: Nenhuma

O sistema atual perde todo conhecimento entre execuções. Um run de 50 experimentos gera padrões valiosos que o próximo run ignora completamente.

**Arquivos a criar**:
- `memory/cross_session.py`
- `memory/pattern_ranker.py`

**Implementação**:

```python
# memory/cross_session.py
class CrossSessionMemory:
    """Persiste padrões de sucesso/falha entre execuções do loop."""

    def __init__(self, target_name: str, results_dir: Path):
        self.memory_path = results_dir / f"{target_name}_memory.jsonl"

    def ingest_run(self, log_path: Path) -> None:
        """Após cada run, extrai padrões e salva na memória."""
        # Lê o log do run
        # Classifica cada experimento: SUCCESS (kept + delta > 0.005),
        #   NEUTRAL (kept mas delta < 0.005), FAILED (reverted),
        #   ANTI_PATTERN (falhou 3+ vezes com hipótese similar)
        # Appenda à memória cross-session

    def load_context(self, max_success: int = 10, max_anti: int = 5) -> dict:
        """Carrega contexto para injetar no prompt de hipótese."""
        # Retorna {"successful": [...], "anti_patterns": [...],
        #          "best_ever": float, "total_experiments": int}

    def inject_into_prompt(self) -> str:
        """Gera texto formatado para o LLM."""
        ctx = self.load_context()
        return (
            f"HISTÓRICO CROSS-SESSION ({ctx['total_experiments']} experimentos):\n"
            f"Melhor score já atingido: {ctx['best_ever']:.4f}\n\n"
            f"PADRÕES QUE FUNCIONARAM (reusar/expandir):\n"
            + "\n".join(f"  ✓ {p}" for p in ctx['successful'])
            + f"\n\nPADRÕES QUE NUNCA FUNCIONAM (não repetir):\n"
            + "\n".join(f"  ✗ {p}" for p in ctx['anti_patterns'])
        )
```

```python
# memory/pattern_ranker.py — inspirado no OPRO
class OPROStyleRanker:
    """Mantém ranking dos N melhores (solução, score) para meta-prompt."""

    def __init__(self, target_name: str, results_dir: Path, top_k: int = 15):
        self.ranking_path = results_dir / f"{target_name}_ranking.json"
        self.top_k = top_k

    def update(self, solution_desc: str, score: float) -> None:
        """Adiciona ao ranking se score > pior do top_k."""

    def format_for_prompt(self) -> str:
        """Gera meta-prompt estilo OPRO: pares (solução, score) ordenados."""
        # "Aqui estão soluções anteriores ordenadas por qualidade:
        #  Score=0.9705: adicionei word boundary em \bdor\b
        #  Score=0.9632: adicionei enviar.*email bidirecional
        #  ...
        #  Gere uma solução MELHOR que todas as anteriores."
```

**Modificação em `engine.py`**:
- No `__init__`: instanciar `CrossSessionMemory` e `OPROStyleRanker`
- No `_generate_hypothesis`: injetar contexto da memória + ranking no prompt
- No final do `run()`: chamar `memory.ingest_run(self.log.log_path)`

**Validação**: Rodar hookify 2x consecutivas. Segunda run deve convergir mais rápido que a primeira.

---

### FASE 2: Busca Populacional + Operadores Evolutivos (4-6h)
**Impacto**: Alto | **Esforço**: Médio | **Custo LLM**: ~2x do atual | **Dependências**: Fase 1

Hill climbing explora 1 direção por vez. Com população de 8, explora 8 direções simultaneamente e recombina as melhores.

**Arquivos a criar**:
- `engines/population.py`
- `evolution/operators.py`
- `evolution/selection.py`

**Implementação**:

```python
# engines/population.py
class PopulationEngine:
    """Engine populacional: N variantes evoluem em paralelo."""

    def __init__(self, target, population_size=8, elite_pct=0.1, tournament_k=3):
        self.pop_size = population_size
        self.elite_pct = elite_pct
        self.tournament_k = tournament_k
        self.population = []  # Lista de (asset_content, score, generation, lineage)

    def initialize(self):
        """Cria população inicial via mutações do baseline."""
        baseline = self.target.asset.read()
        baseline_score = self.target.evaluator.measure(self.target.asset)
        self.population = [
            {"content": baseline, "score": baseline_score, "gen": 0, "id": "baseline"}
        ]
        # Gera N-1 mutantes via LLM
        for i in range(self.pop_size - 1):
            mutant = self._llm_mutate(baseline, f"Variante {i+1}")
            self.population.append(mutant)

    def evolve_generation(self):
        """Um ciclo evolutivo completo."""
        # 1. Avaliar toda a população
        for member in self.population:
            self.target.asset.write(member["content"])
            member["score"] = self.target.evaluator.measure(self.target.asset)

        # 2. Seleção: elitismo + tournament
        sorted_pop = sorted(self.population, key=lambda m: m["score"], reverse=True)
        n_elite = max(1, int(self.pop_size * self.elite_pct))
        elite = sorted_pop[:n_elite]

        # Tournament para o resto
        selected = []
        for _ in range(self.pop_size - n_elite):
            competitors = random.sample(self.population, min(self.tournament_k, len(self.population)))
            winner = max(competitors, key=lambda m: m["score"])
            selected.append(winner)

        # 3. Reprodução: crossover + mutação
        new_pop = list(elite)  # Elite passa direto
        for parent in selected:
            # 30% chance de crossover com outro membro
            if random.random() < 0.3 and len(elite) > 0:
                other = random.choice(elite)
                child = self._crossover(parent, other)
            else:
                child = self._llm_mutate(parent["content"], f"Gen {parent['gen']+1}")
            new_pop.append(child)

        self.population = new_pop[:self.pop_size]
        return max(self.population, key=lambda m: m["score"])
```

```python
# evolution/operators.py
class MutationOperators:
    """Operadores de mutação para regex e prompts."""

    @staticmethod
    def add_alternative(pattern: str, new_term: str) -> str:
        """Adiciona alternativa a um grupo OR: a|b → a|b|c"""

    @staticmethod
    def add_word_boundary(pattern: str, term: str) -> str:
        """Envolve termo com \\b: dor → \\bdor\\b"""

    @staticmethod
    def add_accent_class(pattern: str) -> str:
        """Substitui letra por char class: a → [aá], e → [eé]"""

    @staticmethod
    def make_optional_plural(pattern: str, term: str) -> str:
        """Adiciona plural opcional: lead → leads?"""

    @staticmethod
    def add_context_requirement(pattern: str, term: str, context: str) -> str:
        """Exige contexto: servidor → servidor.*(?:web|vps|linux)"""

    @staticmethod
    def crossover_sections(parent_a: str, parent_b: str) -> str:
        """Crossover por seções delimitadas por ==="""

class PromptMutationOperators:
    """Operadores específicos para system prompts de skills."""

    @staticmethod
    def rephrase_instruction(prompt: str, section: str) -> str:
        """Reescreve uma instrução mantendo semântica."""

    @staticmethod
    def add_example(prompt: str, section: str) -> str:
        """Adiciona exemplo concreto a uma seção."""

    @staticmethod
    def reorder_sections(prompt: str) -> str:
        """Muda ordem das seções (impacta atenção do LLM)."""

    @staticmethod
    def strengthen_constraint(prompt: str, constraint: str) -> str:
        """Reforça uma restrição com ênfase."""
```

```python
# evolution/selection.py
class SelectionStrategies:
    @staticmethod
    def tournament(population, k=3, n=None): ...

    @staticmethod
    def elitist_tournament(population, elite_pct=0.1, k=3): ...

    @staticmethod
    def rank_based(population, pressure=1.5): ...
```

**Modificação em `cli.py`**: novo comando `run --engine population --pop-size 8`

**Validação**: Comparar convergência população vs hill climbing no hookify (mesmo budget). Espera-se 2-5x mais rápido.

---

### FASE 3: Avaliação Paralela + Seleção Adaptativa de Operadores (3-4h)
**Impacto**: Médio-Alto | **Esforço**: Médio | **Custo LLM**: Igual | **Dependências**: Fase 2

Sem paralelismo, avaliar 8 membros é 8x mais lento. Com paralelismo + MAB para selecionar operadores, o sistema se auto-calibra.

**Arquivos a criar**:
- `parallel/evaluator.py`
- `parallel/rate_limiter.py`
- `evolution/adaptive_ops.py`

**Implementação**:

```python
# parallel/evaluator.py
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

class ParallelEvaluator:
    """Avalia população inteira em paralelo."""

    def __init__(self, max_workers=None, use_processes=True):
        # Processos para regex (CPU-bound), threads para LLM (IO-bound)
        self.use_processes = use_processes
        self.max_workers = max_workers or (os.cpu_count() or 4)

    def evaluate_all(self, members, eval_fn, timeout=60):
        """Avalia todos os membros em paralelo."""
        Executor = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        with Executor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(eval_fn, m): m for m in members}
            for future in as_completed(futures, timeout=timeout):
                member = futures[future]
                try:
                    member["score"] = future.result()
                except Exception:
                    member["score"] = 0.0
        return members
```

```python
# evolution/adaptive_ops.py — Multi-Armed Bandit para operadores
import math
from collections import defaultdict

class AdaptiveOperatorSelector:
    """UCB1 + Thompson Sampling para escolher qual operador de mutação usar."""

    def __init__(self, operators: list, strategy="ucb1", c=1.5):
        self.operators = operators
        self.strategy = strategy
        self.c = c
        self.rewards = defaultdict(list)
        self.total_pulls = 0

    def select(self) -> int:
        """Retorna índice do operador a usar."""
        if self.strategy == "ucb1":
            return self._ucb1_select()
        return self._thompson_select()

    def _ucb1_select(self) -> int:
        scores = []
        for i in range(len(self.operators)):
            n = len(self.rewards[i])
            if n == 0:
                return i  # Nunca testado: prioridade máxima
            mean = sum(self.rewards[i]) / n
            bonus = self.c * math.sqrt(math.log(self.total_pulls) / n)
            scores.append(mean + bonus)
        return scores.index(max(scores))

    def update(self, op_idx: int, delta: float):
        """Recompensa = delta de fitness normalizado."""
        reward = max(0, min(1, delta * 10))  # Normaliza para [0, 1]
        self.rewards[op_idx].append(reward)
        self.total_pulls += 1

    def report(self) -> dict:
        """Relatório de eficácia de cada operador."""
        return {
            self.operators[i].__name__: {
                "pulls": len(self.rewards[i]),
                "mean_reward": sum(self.rewards[i]) / max(len(self.rewards[i]), 1),
            }
            for i in range(len(self.operators))
        }
```

**Integração com `PopulationEngine`**:
- Mutação usa `AdaptiveOperatorSelector.select()` para escolher operador
- Após avaliação, `selector.update(op_idx, delta)` atualiza o MAB
- Report no final mostra quais operadores foram mais produtivos

**Validação**: Verificar que o MAB converge para os operadores mais eficazes (ex: `add_accent_class` deve dominar no hookify por ter corrigido os erros de acentuação).

---

### FASE 4: Geração Adversarial de Corpus (3-4h)
**Impacto**: Alto | **Esforço**: Médio | **Custo LLM**: ~$0.50/expansão | **Dependências**: Fase 1

Corpus fixo de 108 prompts causa overfitting. O sistema precisa gerar casos que exponham fraquezas.

**Arquivos a criar**:
- `corpus/adversarial.py`

**Implementação**:

```python
# corpus/adversarial.py
class AdversarialCorpusExpander:
    """Gera test cases adversariais que expõem fraquezas do asset atual."""

    def __init__(self, llm_client, corpus_path: Path, target_evaluator):
        self.llm = llm_client
        self.corpus_path = corpus_path
        self.evaluator = target_evaluator

    def find_weaknesses(self, asset, n=5) -> list:
        """Identifica categorias com menor F1."""
        report = self.evaluator.detailed_report(asset)
        cats = report["categories"]
        # Ordena por F1 crescente
        weak = sorted(cats.items(), key=lambda x: x[1]["f1"])[:n]
        return weak

    def generate_adversarial(self, weak_categories: list, n_per_cat=5) -> list:
        """Gera prompts que testam os limites das categorias fracas."""
        new_cases = []
        for cat, metrics in weak_categories:
            prompt = (
                f"Gere {n_per_cat} prompts de usuário em português brasileiro que:\n"
                f"1. DEVERIAM ativar a categoria '{cat}' mas usam vocabulário incomum\n"
                f"2. NÃO deveriam ativar '{cat}' mas usam palavras ambíguas\n"
                f"3. São multi-label (pertencem a '{cat}' E outra categoria)\n\n"
                f"Cada prompt deve ser realista (algo que Igor digitaria no Claude Code).\n"
                f"Formato JSONL: {{\"prompt\": \"...\", \"labels\": [\"...\"], \"difficulty\": \"hard\"}}\n"
                f"Retorne apenas as linhas JSONL, sem markdown."
            )
            response = self.llm.chat([{"role": "user", "content": prompt}])
            # Parse e validação
            for line in response.strip().split("\n"):
                try:
                    case = json.loads(line)
                    if "prompt" in case and "labels" in case:
                        new_cases.append(case)
                except json.JSONDecodeError:
                    continue
        return new_cases

    def validate_and_append(self, new_cases: list) -> int:
        """Valida labels com LLM juiz e appenda ao corpus."""
        validated = 0
        with open(self.corpus_path, "a", encoding="utf-8") as f:
            for case in new_cases:
                # Validação: LLM confirma que o label está correto
                if self._validate_label(case):
                    f.write(json.dumps(case, ensure_ascii=False) + "\n")
                    validated += 1
        return validated

    def expand_cycle(self, asset, target_new=20) -> dict:
        """Ciclo completo: identifica fraquezas → gera → valida → appenda."""
        weak = self.find_weaknesses(asset)
        raw = self.generate_adversarial(weak, n_per_cat=target_new // max(len(weak), 1))
        added = self.validate_and_append(raw)
        return {"weak_categories": [w[0] for w in weak], "generated": len(raw), "added": added}
```

**Integração com engine**: A cada N gerações (ou quando F1 estagna), rodar `expand_cycle()` para aumentar o corpus. Registrar no log que o corpus mudou.

**Validação**: Após expansão, F1 deve cair temporariamente (novos casos difíceis) e depois subir acima do nível anterior (sistema se adaptou).

---

### FASE 5: Curriculum Learning + Simulated Annealing + TextGrad-lite (4-5h)
**Impacto**: Médio | **Esforço**: Médio | **Custo LLM**: ~$0.10/run | **Dependências**: Fases 2, 4

Três técnicas complementares que refinam a eficiência do loop.

**Arquivos a criar**:
- `corpus/curriculum.py`
- `engines/simulated_annealing.py`
- `textgrad/gradient_feedback.py`

**Curriculum Learning**:
```python
# corpus/curriculum.py
class CurriculumScheduler:
    """Ordena o corpus do fácil ao difícil, liberando casos progressivamente."""

    PHASES = [
        {"name": "quick_wins", "difficulty": ["easy"], "budget_pct": 0.25,
         "constraint": "Modifique APENAS um termo por vez. Mudanças mínimas."},
        {"name": "structural", "difficulty": ["easy", "medium"], "budget_pct": 0.50,
         "constraint": "Pode modificar múltiplos termos. Reestruture patterns."},
        {"name": "adversarial", "difficulty": ["easy", "medium", "hard"], "budget_pct": 0.25,
         "constraint": "Criatividade total. Novos padrões, lookaheads, contexto."},
    ]

    def get_phase(self, budget_used_pct: float) -> dict:
        cumulative = 0
        for phase in self.PHASES:
            cumulative += phase["budget_pct"]
            if budget_used_pct <= cumulative:
                return phase
        return self.PHASES[-1]

    def filter_corpus(self, corpus: list, phase: dict) -> list:
        """Filtra corpus pela dificuldade da fase atual."""
        return [c for c in corpus if c.get("difficulty", "easy") in phase["difficulty"]]
```

**Simulated Annealing** (pós-convergência da população):
```python
# engines/simulated_annealing.py
class SARefiner:
    """Refinamento local quando a população convergiu (delta < threshold)."""

    def __init__(self, initial_temp=1.0, cooling=0.95, min_temp=0.01, restarts=3):
        ...

    def refine(self, best_content: str, eval_fn, neighbor_fn, max_iter=50):
        """SA com restarts a partir do melhor indivíduo da população."""
        # Temperatura controla agressividade da perturbação
        # Aceita soluções piores com probabilidade exp(delta/T)
        # Restarts previnem mínimos locais
```

**TextGrad-lite** (gradientes textuais como direção de melhoria):
```python
# textgrad/gradient_feedback.py
class TextualGradient:
    """Gera 'gradientes textuais' — críticas estruturadas que direcionam a mutação."""

    def compute_gradient(self, asset_content, eval_report, target_metric) -> str:
        """Analisa o relatório de avaliação e gera críticas direcionadas."""
        prompt = (
            f"Analise este relatório de avaliação e gere críticas ESPECÍFICAS:\n\n"
            f"Score atual: {eval_report['f1_macro']:.4f}\n"
            f"Categorias fracas: {self._format_weak(eval_report)}\n"
            f"Erros específicos: {self._format_errors(eval_report)}\n\n"
            f"Para CADA erro, sugira uma direção de melhoria (não a solução exata).\n"
            f"Formato: 'CATEGORIA: o pattern falha porque X. Direção: tentar Y.'"
        )
        return self.llm.chat([{"role": "user", "content": prompt}])

    def apply_gradient(self, hypothesis_prompt: str, gradient: str) -> str:
        """Injeta gradiente no prompt de geração de hipótese."""
        return hypothesis_prompt + f"\n\nDIREÇÕES DE MELHORIA (baseadas em análise de erros):\n{gradient}"
```

**Integração**:
- Curriculum: `PopulationEngine` usa `CurriculumScheduler` para filtrar corpus por fase
- SA: quando delta médio da população < 0.001 por 3 gerações, switch para SARefiner
- TextGrad: antes de gerar hipótese, compute gradient e injete no prompt

**Validação**: Medir velocidade de convergência com/sem cada técnica.

---

### FASE 6: Transferência Entre Alvos + PromptBreeder (4-6h)
**Impacto**: Médio | **Esforço**: Alto | **Custo LLM**: ~$0.20/run | **Dependências**: Fases 1-3

**Cross-Target Transfer**:
```python
# memory/transfer.py
class CrossTargetTransfer:
    """Extrai princípios abstratos de um alvo e injeta em outro."""

    def extract_principles(self, source_target: str, results_dir: Path) -> list:
        """Analisa logs de sucesso de um alvo e extrai princípios genéricos."""
        memory = CrossSessionMemory(source_target, results_dir)
        ctx = memory.load_context()

        prompt = (
            f"Estes padrões funcionaram no alvo '{source_target}':\n"
            + "\n".join(f"  - {p}" for p in ctx['successful'])
            + f"\n\nExtraia PRINCÍPIOS ABSTRATOS (não específicos de regex/prompt) "
            f"que poderiam se aplicar a qualquer tarefa de otimização."
        )
        return self.llm.chat([{"role": "user", "content": prompt}])

    def inject_transfer(self, dest_prompt: str, principles: str) -> str:
        """Adiciona princípios transferidos ao prompt de hipótese do destino."""
        return dest_prompt + f"\n\nPRINCÍPIOS DE OUTROS ALVOS (adaptar, não copiar):\n{principles}"
```

**PromptBreeder** (auto-referencial):
```python
# evolution/promptbreeder.py
class PromptBreeder:
    """Evolui não só o asset, mas também o prompt que gera hipóteses."""

    def __init__(self, population_size=8):
        self.units = []  # Cada unidade = (task_prompt, mutation_prompt, fitness)

    def hyper_mutate(self, mutation_prompt: str) -> str:
        """Meta-nível: muta o prompt de mutação usando ele mesmo."""
        meta_prompt = (
            f"Voce é um prompt que melhora outros prompts.\n"
            f"Prompt atual de mutação: {mutation_prompt}\n"
            f"Gere uma versão MELHORADA deste prompt de mutação."
        )
        return self.llm.chat([{"role": "user", "content": meta_prompt}])

    def evolve(self, asset, evaluator):
        """Ciclo evolutivo: muta mutation_prompt → muta task_prompt → avalia."""
        for unit in self.units:
            # 1. Hyper-mutação (20% das vezes)
            if random.random() < 0.2:
                unit["mutation_prompt"] = self.hyper_mutate(unit["mutation_prompt"])

            # 2. Mutação direta do asset usando mutation_prompt
            new_content = self._apply_mutation(
                asset.read(), unit["mutation_prompt"]
            )
            asset.write(new_content)

            # 3. Avaliação
            unit["fitness"] = evaluator.measure(asset)

        # 4. Seleção por torneio binário
        self._tournament_select()
```

**Validação**: Medir se transfer de hookify→skill melhora convergência do skill. Medir se PromptBreeder supera hill climbing em runs longos (>50 iterações).

---

### FASE 7: Automação + Dashboard + Cron (3-4h)
**Impacto**: Alto | **Esforço**: Baixo-Médio | **Custo LLM**: Configurável | **Dependências**: Todas anteriores

**Cron Runner**:
```python
# scheduler/cron_runner.py
class AutoResearchDaemon:
    """Roda AutoResearch como serviço em background."""

    SCHEDULES = {
        "hookify": {"cron": "0 1 * * *", "budget": 2.0, "hours": 6,
                     "engine": "population", "pop_size": 8},
        "skill_ash": {"cron": "0 2 * * MON", "budget": 3.0, "hours": 4,
                       "engine": "hill_climbing"},
        "frontend": {"cron": "0 3 * * FRI", "budget": 1.0, "hours": 2,
                      "engine": "hill_climbing"},
    }

    def run_scheduled(self, target_name: str):
        """Executa um run agendado com notificação ao final."""
        config = self.SCHEDULES[target_name]
        # 1. Configura target
        # 2. Roda engine escolhido
        # 3. Salva relatório
        # 4. Notifica (Windows toast ou email)
```

**Dashboard HTML**:
```python
# dashboard/report.py
class ProgressReport:
    """Gera relatório HTML com gráficos de evolução."""

    def generate(self, target_name: str, results_dir: Path) -> Path:
        """Gera HTML standalone com Chart.js inline."""
        # Gráficos: score ao longo do tempo, operadores mais eficazes,
        # distribuição da população, heat map de categorias
        # Salva em results/{target}_report.html
```

**Novos comandos CLI**:
```
python -m backend.autoresearch.cli run --target hookify --engine population --pop-size 8
python -m backend.autoresearch.cli expand-corpus hookify  # Gera adversariais
python -m backend.autoresearch.cli schedule hookify --cron "0 1 * * *"
python -m backend.autoresearch.cli report hookify  # Gera dashboard HTML
python -m backend.autoresearch.cli transfer hookify skill  # Cross-target
```

---

## Cronograma de Execução

| Fase | Descrição | Horas | Dependência | Risco |
|------|-----------|-------|-------------|-------|
| 1 | Memória cross-session + ranking OPRO | 2-3h | Nenhuma | Baixo |
| 2 | Busca populacional + operadores | 4-6h | Fase 1 | Médio |
| 3 | Paralelismo + MAB adaptativo | 3-4h | Fase 2 | Baixo |
| 4 | Corpus adversarial | 3-4h | Fase 1 | Médio |
| 5 | Curriculum + SA + TextGrad-lite | 4-5h | Fases 2, 4 | Médio |
| 6 | Transfer + PromptBreeder | 4-6h | Fases 1-3 | Alto |
| 7 | Automação + dashboard + cron | 3-4h | Todas | Baixo |
| **TOTAL** | | **23-32h** | | |

**Paralelismo possível**: Fases 1 e 4 podem rodar em paralelo (sem dependência mútua).

---

## Métricas de Sucesso

| Métrica | Atual (v1) | Meta (v2) | Como medir |
|---------|------------|-----------|------------|
| F1 Hookify | 0.9705 | > 0.99 | `cli baseline hookify` |
| Convergência (iterações até F1 > 0.95) | ~8 manuais | < 20 automáticas | Log JSONL |
| Custo por +0.01 F1 | $0 (manual) | < $0.10 | CostGuard |
| Tempo para rodar 100 experimentos | N/A (manual) | < 2h (overnight) | Cron log |
| Reuso de aprendizado cross-session | 0% | > 60% | Memory hit rate |
| Cobertura adversarial do corpus | 108 prompts | > 300 prompts | Contagem JSONL |
| Operadores adaptativos convergindo | N/A | Top 3 com >80% dos pulls | MAB report |

---

## Custo Estimado

| Componente | Custo por run | Frequência | Custo mensal |
|------------|--------------|------------|-------------|
| Hookify (zero LLM na eval) | $0.50 hipóteses | Diário | $15 |
| Skill prompt (LLM na eval) | $2.00 | Semanal | $8 |
| Corpus adversarial | $0.50 | Semanal | $2 |
| Transfer learning | $0.20 | Mensal | $0.20 |
| **TOTAL** | | | **~$25/mês** |

Usando Haiku para hipóteses e avaliação local onde possível, o sistema custa menos que um café por dia.

---

## Fontes e Referências

| Framework | Conceito usado | Onde aplicar |
|-----------|---------------|-------------|
| Karpathy AutoResearch | Loop hipótese→modifica→avalia→commit | engine.py (base) |
| Agent Zero | Memória FAISS + behaviour_adjustment + scheduler | memory/, scheduler/ |
| OPRO (Google DeepMind) | Ranking (solução, score) no meta-prompt | memory/pattern_ranker.py |
| DSPy MIPROv2 (Stanford) | Busca bayesiana + bootstrap de exemplos | Futuro: integrar Optuna |
| TextGrad (Stanford/Zou) | Gradientes textuais como direção | textgrad/gradient_feedback.py |
| PromptBreeder (DeepMind) | Evolução auto-referencial | evolution/promptbreeder.py |
| PBT (DeepMind) | População + exploit/explore | engines/population.py |
| UCB1/Thompson Sampling | Seleção adaptativa de operadores | evolution/adaptive_ops.py |
| Island Model | Múltiplas sub-populações com migração | engines/island_model.py |

---

*Plano criado em 2026-03-31. Autor: ONIR + Igor.*
*Próximo passo: executar Fase 1 (memória cross-session).*
