def test_oasis_runtime_exports_used_by_simulation_scripts():
    import oasis
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    from oasis import (
        ActionType,
        LLMAction,
        ManualAction,
        generate_reddit_agent_graph,
        generate_twitter_agent_graph,
    )

    assert oasis is not None
    assert ModelFactory is not None
    assert ModelPlatformType is not None
    assert ActionType is not None
    assert LLMAction is not None
    assert ManualAction is not None
    assert callable(generate_reddit_agent_graph)
    assert callable(generate_twitter_agent_graph)
