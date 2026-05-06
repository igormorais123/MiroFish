"""
Modulo de servicos de negocio.

Mantem exports historicos sem importar servicos pesados durante a carga do pacote.
Isso permite que testes unitarios de modulos leves importem `app.services.*` sem
exigir dependencias opcionais de simulacao/LLM.
"""

from importlib import import_module

_EXPORTS = {
    'OntologyGenerator': ('ontology_generator', 'OntologyGenerator'),
    'GraphBuilderService': ('graph_builder', 'GraphBuilderService'),
    'TextProcessor': ('text_processor', 'TextProcessor'),
    'ZepEntityReader': ('zep_entity_reader', 'ZepEntityReader'),
    'EntityNode': ('zep_entity_reader', 'EntityNode'),
    'FilteredEntities': ('zep_entity_reader', 'FilteredEntities'),
    'OasisProfileGenerator': ('oasis_profile_generator', 'OasisProfileGenerator'),
    'OasisAgentProfile': ('oasis_profile_generator', 'OasisAgentProfile'),
    'SimulationManager': ('simulation_manager', 'SimulationManager'),
    'SimulationState': ('simulation_manager', 'SimulationState'),
    'SimulationStatus': ('simulation_manager', 'SimulationStatus'),
    'SimulationConfigGenerator': ('simulation_config_generator', 'SimulationConfigGenerator'),
    'SimulationParameters': ('simulation_config_generator', 'SimulationParameters'),
    'AgentActivityConfig': ('simulation_config_generator', 'AgentActivityConfig'),
    'TimeSimulationConfig': ('simulation_config_generator', 'TimeSimulationConfig'),
    'EventConfig': ('simulation_config_generator', 'EventConfig'),
    'PlatformConfig': ('simulation_config_generator', 'PlatformConfig'),
    'SimulationRunner': ('simulation_runner', 'SimulationRunner'),
    'SimulationRunState': ('simulation_runner', 'SimulationRunState'),
    'RunnerStatus': ('simulation_runner', 'RunnerStatus'),
    'AgentAction': ('simulation_runner', 'AgentAction'),
    'RoundSummary': ('simulation_runner', 'RoundSummary'),
    'ZepGraphMemoryUpdater': ('zep_graph_memory_updater', 'ZepGraphMemoryUpdater'),
    'ZepGraphMemoryManager': ('zep_graph_memory_updater', 'ZepGraphMemoryManager'),
    'AgentActivity': ('zep_graph_memory_updater', 'AgentActivity'),
    'SimulationIPCClient': ('simulation_ipc', 'SimulationIPCClient'),
    'SimulationIPCServer': ('simulation_ipc', 'SimulationIPCServer'),
    'IPCCommand': ('simulation_ipc', 'IPCCommand'),
    'IPCResponse': ('simulation_ipc', 'IPCResponse'),
    'CommandType': ('simulation_ipc', 'CommandType'),
    'CommandStatus': ('simulation_ipc', 'CommandStatus'),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _EXPORTS[name]
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
