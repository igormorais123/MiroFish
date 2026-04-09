#!/usr/bin/env python3
"""
Script de manutenção: Corrige nós em Neo4j com group_id incorreto ou ausente.

Contexto do bug: Quando 427 chunks foram enviados ao Graphiti, alguns nós
foram criados com group_id incorreto (NULL, vazio, ou "mirofish_test_001").

Este script conecta ao Neo4j e:
1. Identifica nós órfãos (sem group_id correto)
2. Corrige nós com group_id de teste para o ID correto
3. Gera relatório das correções
"""

import sys
from typing import Dict, Any, List, Optional

try:
    from neo4j import GraphDatabase
except ImportError:
    print("ERRO: neo4j-driver não instalado. Instale com: pip install neo4j")
    sys.exit(1)


class Neo4jGraphIdFixer:
    """Ferramenta para corrigir group_ids em Neo4j."""

    def __init__(self, uri: str, username: str, password: str):
        """Inicializa conexão com Neo4j."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.stats = {
            "orphaned_nodes": 0,
            "test_nodes": 0,
            "fixed_nodes": 0,
            "errors": [],
        }

    def close(self):
        """Fecha conexão com Neo4j."""
        if self.driver:
            self.driver.close()

    def get_all_group_ids(self) -> Dict[str, int]:
        """Retorna mapeamento de group_id -> contagem de nós."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n) RETURN DISTINCT n.group_id as group_id, count(n) as count"
            )
            return {record["group_id"]: record["count"] for record in result}

    def find_orphaned_nodes(self) -> List[Dict[str, Any]]:
        """Encontra nós sem group_id correto."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n) WHERE n.group_id IS NULL OR n.group_id = '' "
                "RETURN n.uuid as uuid, n.name as name LIMIT 100"
            )
            orphans = [dict(record) for record in result]
            self.stats["orphaned_nodes"] = len(orphans)
            return orphans

    def find_test_nodes(self, old_test_id: str = "mirofish_test_001") -> List[Dict[str, Any]]:
        """Encontra nós com IDs de teste."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n) WHERE n.group_id = $test_id "
                "RETURN n.uuid as uuid, n.name as name, n.group_id as group_id",
                test_id=old_test_id
            )
            test_nodes = [dict(record) for record in result]
            self.stats["test_nodes"] = len(test_nodes)
            return test_nodes

    def fix_test_nodes(self, old_test_id: str, new_group_id: str) -> int:
        """Corrige nós com IDs de teste para o novo ID."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n) WHERE n.group_id = $old_id "
                "SET n.group_id = $new_id "
                "RETURN count(n) as updated",
                old_id=old_test_id,
                new_id=new_group_id
            )
            count = result.single()["updated"]
            self.stats["fixed_nodes"] += count
            return count

    def validate_group_id(self, group_id: str) -> Dict[str, Any]:
        """Valida um group_id específico."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n {group_id: $group_id}) RETURN count(n) as count",
                group_id=group_id
            )
            count = result.single()["count"]
            return {
                "group_id": group_id,
                "node_count": count,
                "valid": count > 0
            }

    def generate_report(self) -> str:
        """Gera relatório das correções."""
        report = [
            "\n" + "=" * 70,
            "RELATÓRIO DE CORREÇÃO DE GRAPH_IDs EM NEO4J",
            "=" * 70,
            "",
            "RESUMO DAS CORREÇÕES:",
            f"  - Nós órfãos encontrados: {self.stats['orphaned_nodes']}",
            f"  - Nós com ID de teste encontrados: {self.stats['test_nodes']}",
            f"  - Nós corrigidos: {self.stats['fixed_nodes']}",
            "",
        ]

        if self.stats["errors"]:
            report.append("ERROS ENCONTRADOS:")
            for error in self.stats["errors"]:
                report.append(f"  - {error}")
            report.append("")

        # Estatísticas de distribuição
        group_ids = self.get_all_group_ids()
        report.append("DISTRIBUIÇÃO ATUAL DE NÓS POR GROUP_ID:")
        for group_id in sorted(group_ids.keys(), key=lambda x: group_ids[x], reverse=True):
            count = group_ids[group_id]
            report.append(f"  - {group_id}: {count} nós")

        report.append("\n" + "=" * 70)
        return "\n".join(report)


def main():
    """Função principal."""
    # Configuração
    NEO4J_URI = "bolt://neo4j:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "Z3pN3o4j2026!"

    OLD_TEST_ID = "mirofish_test_001"
    CORRECT_ID = "mirofish_fe7124a390d64e7b"

    print("\n[INFO] Conectando ao Neo4j...")
    fixer = Neo4jGraphIdFixer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        print("\n[INFO] Analisando nós em Neo4j...")

        # Encontrar nós órfãos
        orphans = fixer.find_orphaned_nodes()
        if orphans:
            print(f"[AVISO] {len(orphans)} nó(s) órfão(s) encontrado(s)")
            for orphan in orphans[:5]:
                print(f"  - uuid={orphan.get('uuid')}, name={orphan.get('name')}")
            if len(orphans) > 5:
                print(f"  ... e mais {len(orphans) - 5}")

        # Encontrar nós com ID de teste
        test_nodes = fixer.find_test_nodes(OLD_TEST_ID)
        if test_nodes:
            print(f"\n[ALERTA] {len(test_nodes)} nó(s) com ID de teste encontrado(s)")
            for node in test_nodes[:5]:
                print(f"  - uuid={node.get('uuid')}, name={node.get('name')}")
            if len(test_nodes) > 5:
                print(f"  ... e mais {len(test_nodes) - 5}")

            # Corrigir nós de teste
            print(f"\n[AÇÃO] Corrigindo nós com ID de teste {OLD_TEST_ID}...")
            print(f"       Novo ID: {CORRECT_ID}")
            fixed_count = fixer.fix_test_nodes(OLD_TEST_ID, CORRECT_ID)
            print(f"[OK] {fixed_count} nó(s) corrigido(s)")

            # Validar correção
            validation = fixer.validate_group_id(CORRECT_ID)
            print(f"\n[VALIDAÇÃO] Group_id '{CORRECT_ID}': {validation['node_count']} nós")

        # Gerar relatório
        print(fixer.generate_report())

    except Exception as e:
        print(f"\n[ERRO] Falha: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        fixer.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
