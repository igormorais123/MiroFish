"""Fix get_graph_data to use episodes as fallback when search returns empty."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/app/backend/app/services/graph_builder.py"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the get_graph_data method to add episode-based fallback
old_return = '''        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }'''

new_return = '''        # Fallback: se search nao retornou dados, usa episodios
        if not nodes_data and not edges_data:
            try:
                episodes = self.client.get_episodes(graph_id, last_n=200)
                if episodes:
                    for ep in episodes:
                        if isinstance(ep, dict):
                            ep_name = ep.get("name", "")
                            ep_content = ep.get("content", "")
                            ep_uuid = ep.get("uuid", "")
                            ep_created = ep.get("created_at")
                            if ep_content:
                                nodes_data.append({
                                    "uuid": ep_uuid,
                                    "name": ep_name or f"Episodio {len(nodes_data)+1}",
                                    "labels": ["Episodio"],
                                    "summary": ep_content[:200] if ep_content else "",
                                    "attributes": {},
                                    "created_at": str(ep_created) if ep_created else None,
                                })
                    logger.info(f"Fallback episodios: {len(nodes_data)} nos de {len(episodes)} episodios")
            except Exception as ep_err:
                logger.warning(f"Fallback episodios falhou: {ep_err}")

        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print("OK: Added episode fallback to get_graph_data")
else:
    print("WARN: return block not found exactly")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("saved")
