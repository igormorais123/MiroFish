"""
Alvo AutoResearch: Performance do Frontend Mirofish.

Avaliacao: npm build + metricas de bundle size e build time.
Metrica: Score composto inverso (menor bundle + menor build time = maior score).

Custo: Zero LLM na eval. Build leva ~10s. ~200 exp/noite.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

from .base import Asset, Constraints, Evaluator


class FrontendPerfConstraints(Constraints):
    """Invariantes para otimizacao de performance frontend."""

    def __init__(self, frontend_dir: Path):
        self.frontend_dir = frontend_dir

    def to_prompt(self) -> str:
        return (
            "Voce otimiza a configuracao de build do frontend Vue.js/Vite.\n\n"
            "INVARIANTES — nao violar:\n"
            "1. Build deve completar sem erros (npm run build)\n"
            "2. Manter compatibilidade Vue 3\n"
            "3. Nao remover imports ou componentes existentes\n"
            "4. Nao adicionar dependencias externas novas\n"
            "5. Bundle total < 500KB gzipped\n"
            "6. Manter funcionalidade existente intacta\n"
            "7. Sintaxe JavaScript/TypeScript valida\n\n"
            "OBJETIVO: Minimizar bundle size + build time.\n\n"
            "ESTRATEGIAS VALIDAS:\n"
            "- Code splitting e lazy loading de rotas\n"
            "- Tree shaking de imports nao usados\n"
            "- Otimizacao de chunks no Vite config\n"
            "- Minificacao de CSS\n"
            "- Compressao de assets\n"
            "- Remocao de dead code\n"
            "- Otimizacao de imports de bibliotecas"
        )

    def validate(self, asset_path: Path) -> bool:
        """Verifica se o build completa sem erros."""
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(self.frontend_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


class FrontendPerfAsset(Asset):
    """Asset: vite.config.js e arquivos de config do frontend."""

    def __init__(self, config_path: Path):
        self._path = config_path

    def path(self) -> Path:
        return self._path

    def read(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def write(self, content: str) -> None:
        self._path.write_text(content, encoding="utf-8")

    def editable_sections(self) -> Dict[str, str]:
        content = self.read()
        return {"vite_config": content}


class FrontendPerfEvaluator(Evaluator):
    """Avaliador de performance: build time + bundle size."""

    def __init__(self, frontend_dir: Path):
        self.frontend_dir = frontend_dir

    def metric_name(self) -> str:
        return "Performance score (1/build_time + 1/bundle_size)"

    @property
    def requires_llm(self) -> bool:
        return False

    def _get_bundle_size(self) -> int:
        """Retorna tamanho total do bundle em bytes."""
        dist_dir = self.frontend_dir / "dist"
        if not dist_dir.exists():
            return 999_999_999

        total = 0
        for f in dist_dir.rglob("*"):
            if f.is_file() and f.suffix in (".js", ".css", ".html"):
                total += f.stat().st_size
        return total

    def measure(self, asset: Asset) -> float:
        """Build e mede performance. Maior score = melhor."""
        try:
            # Build
            start = time.perf_counter()
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(self.frontend_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            build_time = time.perf_counter() - start

            if result.returncode != 0:
                return 0.0

            # Bundle size
            bundle_bytes = self._get_bundle_size()
            bundle_kb = bundle_bytes / 1024

            # Score: inversamente proporcional a tamanho e tempo
            # Normalizado para ficar em range razoavel
            size_score = 1000 / max(bundle_kb, 1)
            time_score = 100 / max(build_time, 0.1)

            # Peso: 70% tamanho, 30% velocidade de build
            return size_score * 0.7 + time_score * 0.3

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return 0.0
