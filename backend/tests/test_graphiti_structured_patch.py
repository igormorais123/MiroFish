from pathlib import Path


PATCH_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "graphiti_patches"
    / "zep_graphiti.py"
)


def test_gpt5_structured_completion_receives_pydantic_schema():
    source = PATCH_PATH.read_text(encoding="utf-8")

    method_start = source.index("async def _create_structured_completion(")
    method_end = source.index("async def _create_completion(", method_start)
    method = source[method_start:method_end]

    assert "response_model.model_json_schema()" in method
    assert "messages=[schema_message, *messages]" in method


def test_extracted_entity_alias_is_normalized_before_validation():
    source = PATCH_PATH.read_text(encoding="utf-8")

    assert "'name': item['entity']" in source
