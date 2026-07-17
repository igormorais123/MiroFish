from pathlib import Path


PATCH_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "graphiti_patches"
    / "ingest.py"
)


def test_messages_endpoint_starts_worker_on_demand():
    source = PATCH_PATH.read_text(encoding="utf-8")

    endpoint_start = source.index("async def add_messages(")
    endpoint_end = source.index("@router.post('/entity-node'", endpoint_start)

    assert "await async_worker.start()" in source[endpoint_start:endpoint_end]


def test_worker_is_restartable_and_survives_job_failure():
    source = PATCH_PATH.read_text(encoding="utf-8")

    assert "if self.task is None or self.task.done():" in source
    assert "logger.exception('Graphiti message ingestion failed')" in source
    assert "self.queue.task_done()" in source
