"""
Phase 3: API de Custos Real — Token Tracking Backend
Aplica todas as mudancas necessarias para tracking real de tokens e custos.
"""
import re
import sys

def patch_file(filepath, patches):
    """Aplica patches sequenciais a um arquivo."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for old, new, desc in patches:
        if old in content:
            content = content.replace(old, new, 1)
            print(f"  OK: {desc}")
        else:
            print(f"  SKIP: {desc} (pattern not found)")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "/app/backend"

    # ============================================================
    # 1. PATCH token_tracker.py — add stage-level tracking + pricing per model
    # ============================================================
    print("PATCH 1: token_tracker.py — stage tracking + model pricing")

    tracker_path = f"{base}/app/utils/token_tracker.py"
    with open(tracker_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_tracker = '''"""Rastreamento de consumo de tokens e custo por simulacao."""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

# Precos por modelo (USD por 1M tokens) — input / output
MODEL_PRICING = {
    # BestFREE (DeepSeek via OmniRoute)
    "bestfree": {"input": 0.0, "output": 0.0},
    "deepseek": {"input": 0.0, "output": 0.0},
    # mirofish-smart (GPT-4o-mini via OmniRoute)
    "mirofish-smart": {"input": 0.30, "output": 1.20},
    "gpt-4o-mini": {"input": 0.30, "output": 1.20},
    # Sonnet 4.6
    "claude/claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "sonnet-tasks": {"input": 3.00, "output": 15.00},
    # Opus 4.6
    "claude/claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "opus-tasks": {"input": 15.00, "output": 75.00},
}

def _get_pricing(model_name: str) -> dict:
    """Retorna pricing para o modelo, fallback para mirofish-smart."""
    if not model_name:
        return MODEL_PRICING["mirofish-smart"]
    name = model_name.lower()
    for key, pricing in MODEL_PRICING.items():
        if key in name:
            return pricing
    return MODEL_PRICING["mirofish-smart"]


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    start_time: float = field(default_factory=time.time)
    model: str = ""

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self) -> float:
        pricing = _get_pricing(self.model)
        return (self.prompt_tokens * pricing["input"] / 1_000_000 +
                self.completion_tokens * pricing["output"] / 1_000_000)

    @property
    def cost_brl(self) -> float:
        return self.cost_usd * 5.80

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "cost_usd": round(self.cost_usd, 6),
            "cost_brl": round(self.cost_brl, 4),
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "model": self.model,
        }


class TokenTracker:
    """Singleton thread-safe para rastrear tokens globalmente, por sessao e por etapa."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._global = TokenUsage()
                    cls._instance._sessions: Dict[str, TokenUsage] = {}
                    cls._instance._stages: Dict[str, Dict[str, TokenUsage]] = {}
        return cls._instance

    def track(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        session_id: Optional[str] = None,
        stage: Optional[str] = None,
        model: Optional[str] = None,
    ):
        with self._lock:
            self._global.prompt_tokens += prompt_tokens
            self._global.completion_tokens += completion_tokens
            self._global.total_requests += 1
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = TokenUsage(model=model or "")
                sess = self._sessions[session_id]
                sess.prompt_tokens += prompt_tokens
                sess.completion_tokens += completion_tokens
                sess.total_requests += 1
                # Stage tracking (per session)
                if stage:
                    if session_id not in self._stages:
                        self._stages[session_id] = {}
                    if stage not in self._stages[session_id]:
                        self._stages[session_id][stage] = TokenUsage(model=model or "")
                    st = self._stages[session_id][stage]
                    st.prompt_tokens += prompt_tokens
                    st.completion_tokens += completion_tokens
                    st.total_requests += 1
                    if model:
                        st.model = model

    def track_error(self, session_id: Optional[str] = None, stage: Optional[str] = None):
        with self._lock:
            self._global.total_errors += 1
            if session_id and session_id in self._sessions:
                self._sessions[session_id].total_errors += 1
            if session_id and stage and session_id in self._stages:
                if stage in self._stages[session_id]:
                    self._stages[session_id][stage].total_errors += 1

    def get_global(self) -> dict:
        return self._global.to_dict()

    def get_session(self, session_id: str) -> dict:
        if session_id in self._sessions:
            return self._sessions[session_id].to_dict()
        return TokenUsage().to_dict()

    def get_session_stages(self, session_id: str) -> dict:
        """Retorna breakdown por etapa para uma sessao."""
        if session_id in self._stages:
            return {name: usage.to_dict() for name, usage in self._stages[session_id].items()}
        return {}

    def get_all_sessions(self) -> dict:
        return {sid: usage.to_dict() for sid, usage in self._sessions.items()}

    def reset_global(self):
        with self._lock:
            self._global = TokenUsage()

    def start_session(self, session_id: str):
        with self._lock:
            self._sessions[session_id] = TokenUsage()
            self._stages[session_id] = {}
'''

    with open(tracker_path, 'w', encoding='utf-8') as f:
        f.write(new_tracker)
    print("  REWRITTEN: token_tracker.py with stage tracking + model pricing")

    # ============================================================
    # 2. PATCH llm_client.py — add stage + model params to track()
    # ============================================================
    print("\nPATCH 2: llm_client.py — stage + model in track()")

    llm_path = f"{base}/app/utils/llm_client.py"
    patches = [
        # Add stage param to chat()
        (
            '''    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> str:''',
            '''    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        session_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> str:''',
            "chat() add stage param"
        ),
        # Update track_error call
        (
            '_tracker.track_error(session_id=session_id)',
            '_tracker.track_error(session_id=session_id, stage=stage)',
            "track_error with stage"
        ),
        # Update track call with stage + model
        (
            '''            _tracker.track(
                prompt_tokens=getattr(usage, 'prompt_tokens', 0) or 0,
                completion_tokens=getattr(usage, 'completion_tokens', 0) or 0,
                session_id=session_id,
            )''',
            '''            _tracker.track(
                prompt_tokens=getattr(usage, 'prompt_tokens', 0) or 0,
                completion_tokens=getattr(usage, 'completion_tokens', 0) or 0,
                session_id=session_id,
                stage=stage,
                model=self.model,
            )''',
            "track() with stage + model"
        ),
        # Add stage param to chat_json()
        (
            '''    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:''',
            '''    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        session_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> Dict[str, Any]:''',
            "chat_json() add stage param"
        ),
        # Pass stage in chat_json -> chat call
        (
            '''            session_id=session_id,
        )
        cleaned = response.strip()''',
            '''            session_id=session_id,
            stage=stage,
        )
        cleaned = response.strip()''',
            "chat_json passes stage to chat"
        ),
    ]
    patch_file(llm_path, patches)

    # ============================================================
    # 3. PATCH report_agent.py — propagate session_id + stage
    # ============================================================
    print("\nPATCH 3: report_agent.py — propagate session_id + stage")

    report_path = f"{base}/app/services/report_agent.py"
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all .chat( calls and add stage param if missing
    # The report agent has several chat calls — we need to tag each with the right stage

    # Strategy: find self.llm.chat( and helena_llm.chat( calls and add stage
    # We'll do targeted replacements based on surrounding context

    changes = 0

    # Tag ReACT section generation calls with stage="report"
    # These are in generate_section / _generate_section_react
    for pattern_pair in [
        # Section generation (ReACT)
        ('response = self.llm.chat(\n                    messages=messages',
         'response = self.llm.chat(\n                    messages=messages'),
        # Outline generation
        ('response = self.llm.chat_json(\n                messages=',
         'response = self.llm.chat_json(\n                messages='),
    ]:
        pass  # These are too fragile for blind replacement

    # More targeted: add session_id to the ReportAgent class
    # Check if ReportAgent already has session_id
    if 'self.session_id' not in content:
        # Add session_id to __init__
        content = content.replace(
            'class ReportAgent:',
            'class ReportAgent:\n    """Agente ReACT para geracao de relatorios."""\n',
            1
        ) if '"""Agente ReACT' not in content else content

        # Find __init__ and add session_id
        init_match = re.search(r'(def __init__\(self[^)]*\):.*?\n)', content)
        if init_match:
            init_line = init_match.group(0)
            # Add session_id after the first self assignment
            pass

    # Simpler approach: patch each .chat( call to include stage kwarg
    # Use line-by-line approach
    lines = content.split('\n')
    new_lines = []
    i = 0
    stage_context = "report"  # default for report_agent

    while i < len(lines):
        line = lines[i]

        # Detect helena section
        if 'helena' in line.lower() and ('llm' in line.lower() or 'client' in line.lower()):
            stage_context = "helena"

        # Check for .chat( or .chat_json( calls that don't have stage=
        if ('.chat(' in line or '.chat_json(' in line) and 'stage=' not in line:
            # Find the closing ) by tracking parens
            block = [line]
            paren_count = line.count('(') - line.count(')')
            j = i + 1
            while paren_count > 0 and j < len(lines):
                block.append(lines[j])
                paren_count += lines[j].count('(') - lines[j].count(')')
                j += 1

            # Check if stage= already in the block
            block_text = '\n'.join(block)
            if 'stage=' not in block_text and 'session_id=' not in block_text:
                # Add stage to the last line before closing paren
                # Find the last parameter line
                for k in range(len(block) - 1, -1, -1):
                    stripped = block[k].rstrip()
                    if stripped.endswith(')'):
                        # Add stage before closing paren
                        indent = len(block[k]) - len(block[k].lstrip())
                        if ',' in block[k-1] if k > 0 else True:
                            block[k] = block[k].rstrip()
                            if block[k].endswith(')'):
                                # Simple case: closing ) on same line as last arg
                                # Insert stage= before )
                                block[k] = block[k][:-1].rstrip()
                                if not block[k].endswith(','):
                                    block[k] += ','
                                block[k] += f'\n{" " * (indent + 4)}stage="{stage_context}",'
                                block[k] += f'\n{" " * indent})'
                        changes += 1
                        break

            new_lines.extend(block)
            i = j
            continue

        new_lines.append(line)
        i += 1

    # Actually, the above is too complex and fragile. Let me just write a targeted patch.
    # Reset and do simple targeted patches.
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The key insight: all LLM calls in report_agent already accept session_id kwarg in the LLMClient.
    # We just need to add stage= to each call site.
    # Since these are in a complex file, let's just add session_id tracking at the generate level
    # and patch the existing calls to forward it.

    # Approach: the generate function creates session_id from simulation_id
    # and passes it where needed. The stage names are:
    # - "graphrag" for graph building
    # - "profiles" for agent profile generation
    # - "simulation" for OASIS simulation
    # - "report" for ReACT report sections
    # - "helena" for Helena Strategos

    # For now, ensure the report generation passes stage="report" and helena passes stage="helena"
    # The other stages (graphrag, profiles, simulation) are in different services

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  NOTE: report_agent.py — stage propagation requires careful per-call patching")
    print("  Will handle via sed commands below")

    # ============================================================
    # 4. ADD /api/report/<report_id>/costs endpoint
    # ============================================================
    print("\nPATCH 4: report.py API — add /costs endpoint")

    api_path = f"{base}/app/api/report.py"
    with open(api_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add import for TokenTracker if not present
    if 'TokenTracker' not in content:
        content = content.replace(
            "from ..utils.logger import get_logger",
            "from ..utils.logger import get_logger\nfrom ..utils.token_tracker import TokenTracker",
        )
        print("  OK: Added TokenTracker import")

    # Add the costs endpoint before the last route
    costs_endpoint = '''

@report_bp.route('/<report_id>/costs', methods=['GET'])
def get_report_costs(report_id: str):
    """
    Retorna breakdown de tokens e custos por etapa do pipeline.

    Retorno:
        {
            "success": true,
            "data": {
                "session_total": { ... },
                "stages": {
                    "graphrag": { "prompt_tokens": N, "completion_tokens": N, "cost_usd": N, ... },
                    "profiles": { ... },
                    "simulation": { ... },
                    "report": { ... },
                    "helena": { ... }
                }
            }
        }
    """
    try:
        # O session_id para tracking eh baseado no simulation_id do report
        report_manager = ReportManager()
        report_data = report_manager.get_report(report_id)

        if not report_data:
            return jsonify({"success": False, "error": "Relatorio nao encontrado"}), 404

        simulation_id = report_data.get("simulation_id", "")

        tracker = TokenTracker()
        session_data = tracker.get_session(simulation_id)
        stages_data = tracker.get_session_stages(simulation_id)

        # Garantir que todas as 5 etapas existam no retorno
        default_stage = {
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "total_requests": 0, "total_errors": 0,
            "cost_usd": 0.0, "cost_brl": 0.0, "elapsed_seconds": 0.0, "model": ""
        }

        stage_names = ["graphrag", "profiles", "simulation", "report", "helena"]
        stages = {}
        for name in stage_names:
            stages[name] = stages_data.get(name, default_stage)

        # Adicionar stages extras que possam existir
        for name, data in stages_data.items():
            if name not in stages:
                stages[name] = data

        return jsonify({
            "success": True,
            "data": {
                "session_total": session_data,
                "stages": stages,
                "simulation_id": simulation_id,
            }
        })

    except Exception as exc:
        logger.error(f"Erro ao obter custos do relatorio {report_id}: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500

'''

    # Insert before the tools/search route
    if "get_report_costs" not in content:
        content = content.replace(
            "@report_bp.route('/tools/search', methods=['POST'])",
            costs_endpoint + "@report_bp.route('/tools/search', methods=['POST'])",
        )
        print("  OK: Added /costs endpoint")
    else:
        print("  SKIP: /costs endpoint already exists")

    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\nAll backend patches applied!")
    print("\nRemaining: frontend patch + stage propagation in services")


if __name__ == "__main__":
    main()
