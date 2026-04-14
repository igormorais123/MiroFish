# Testing Patterns

**Analysis Date:** 2026-04-13

## Test Framework

**Runner:**
- pytest 8.0.0+
- Configuration: `pyproject.toml` (no separate `pytest.ini`)
- Located: `backend/pyproject.toml` defines pytest as dev dependency

**Assertion Library:**
- Python's built-in `assert` statements

**Run Commands:**
```bash
# Run all tests (from backend/ directory)
pytest

# Watch mode (not configured, use pytest-watch if needed)
pytest --watch

# Coverage (install with: pip install pytest-cov)
pytest --cov=app

# Specific test file
pytest backend/tests/test_graph_builder.py

# Specific test
pytest backend/tests/test_graph_builder.py::test_wait_for_graph_materialization_returns_empty_gracefully
```

**Frontend Testing:**
- No test framework configured (no vitest, jest, etc. in package.json)
- Frontend relies on manual testing or external E2E tools

## Test File Organization

**Location:**
- Backend tests: Co-located in `backend/tests/` directory (separate from source)
- Frontend: No test files found
- Pattern: `test_*.py` or `*_test.py` prefix/suffix

**Naming:**
- Module under test: `test_graph_builder.py` for `services/graph_builder.py`
- Test functions: `test_<scenario>_<expected_behavior>()` (e.g., `test_wait_for_graph_materialization_returns_empty_gracefully`)

**Structure:**
```
backend/
├── app/
│   ├── api/
│   ├── services/
│   ├── models/
│   └── utils/
├── tests/
│   └── test_graph_builder.py
├── pyproject.toml
└── run.py
```

## Test Structure

**Suite Organization:**
```python
# From backend/tests/test_graph_builder.py
def test_wait_for_graph_materialization_returns_empty_gracefully(monkeypatch):
    """Quando o grafo nao materializa, retorna os dados vazios (degradacao graciosa)."""
    service = GraphBuilderService()
    
    # Setup: monkeypatch mocks
    monkeypatch.setattr(service, "_wait_for_episodes", lambda *args, **kwargs: 0)
    monkeypatch.setattr(
        service,
        "get_graph_data",
        lambda graph_id: { ... }
    )
    
    # Act
    result = service.wait_for_graph_materialization("graph_x")
    
    # Assert
    assert result["node_count"] == 0
    assert result["edge_count"] == 0
```

**Patterns:**

- **Setup**: Create test service instance, apply monkeypatches
- **Teardown**: Implicit (no cleanup detected in existing tests)
- **Assertion**: Direct `assert` statements
- **Naming**: Descriptive test names that read like documentation

## Mocking

**Framework:** pytest's built-in `monkeypatch` fixture

**Patterns:**
```python
# Mock instance method
monkeypatch.setattr(service, "_wait_for_episodes", lambda *args, **kwargs: 0)

# Mock method returning dict
monkeypatch.setattr(
    service,
    "get_graph_data",
    lambda graph_id: {
        "graph_id": graph_id,
        "nodes": [],
        "edges": [],
        "node_count": 0,
        "edge_count": 0,
    }
)

# Mock module-level function
monkeypatch.setattr("app.services.graph_builder.time.sleep", lambda *_args, **_kwargs: None)

# Mock client method
monkeypatch.setattr(service.client, "get_episodes", lambda *args, **kwargs: [])
```

**What to Mock:**
- External service calls (e.g., GraphRAG client, LLM API)
- Time-dependent functions (e.g., `time.sleep()`)
- Side effects (file I/O, database operations)
- Dependencies that are slow or non-deterministic

**What NOT to Mock:**
- Business logic under test
- Data structures and transformations
- Local utility functions unless they cause side effects

## Fixtures and Factories

**Test Data:**
- Not extensively used in current test suite
- Ad-hoc dictionary creation inline (e.g., `{"graph_id": "graph_x", "nodes": [], ...}`)
- No dedicated fixture files or factories detected

**Location:**
- If needed, create `backend/tests/conftest.py` for shared fixtures
- Example pattern to implement:
```python
# conftest.py
import pytest
from app.models.project import Project, ProjectStatus

@pytest.fixture
def sample_project():
    return Project(
        project_id="test-proj-1",
        name="Test Project",
        status=ProjectStatus.CREATED,
        created_at="2026-04-13T00:00:00",
        updated_at="2026-04-13T00:00:00"
    )
```

## Coverage

**Requirements:** None enforced (no coverage thresholds in config)

**View Coverage:**
```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
# or
start htmlcov/index.html  # Windows
```

**Current State:** No coverage configuration or CI/CD checks enforcing minimums

## Test Types

**Unit Tests:**
- Scope: Single service/component in isolation
- Approach: Monkeypatch dependencies, test behavior with various inputs
- Example: `test_graph_builder.py` tests `GraphBuilderService` with mocked graph data
- Location: `backend/tests/`

**Integration Tests:**
- Not detected in current codebase
- Would test interaction between services (e.g., GraphBuilder + ZepEntityReader)
- Should be added as codebase grows

**E2E Tests:**
- Not configured (no playwright, cypress, or puppeteer setup in frontend)
- Manual testing via Playwright MCP or similar tools
- Recommended: Add E2E tests for critical user workflows (upload → graph build → simulation)

## Common Patterns

**Async Testing:**
```python
# pytest-asyncio is in dev dependencies
# Usage:
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

**Error Testing:**
- Not found in current tests
- Pattern to implement:
```python
def test_raises_error_on_invalid_input():
    service = GraphBuilderService()
    
    with pytest.raises(ValueError):
        service.validate_graph_id(None)
```

**Parametrized Tests:**
- Not used in current suite
- Pattern to implement:
```python
@pytest.mark.parametrize("graph_id,expected", [
    ("valid_id", True),
    ("", False),
    (None, False),
])
def test_validate_graph_id(graph_id, expected):
    assert GraphBuilderService.validate_graph_id(graph_id) == expected
```

## Test Execution

**Dependencies:**
```toml
# From backend/pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

**Install & Run:**
```bash
cd backend
pip install -e ".[dev]"  # Install with dev dependencies
pytest                   # Run tests
```

**Monkeypatch Fixture:**
- Built-in pytest fixture, no import needed
- Allows dynamic patching of modules, classes, functions at test time
- Example: `monkeypatch.setattr(obj, "attr", value)`

## Test Coverage Gaps

**Untested Áreas:**
- API endpoints: No tests for Flask routes (`api/graph.py`, `api/simulation.py`, etc.)
- Frontend: No Vue component tests
- Services: Only `GraphBuilderService` has minimal testing
- Error paths: Very limited exception testing
- Integration: No multi-service workflows tested

**Risk:** 
- Bugs in API layer could go undetected
- Frontend logic breaks without feedback
- Refactoring services becomes risky

**Priority:** **High** — Recommend adding:
1. API route tests using Flask test client
2. Service layer tests for critical operations (simulation, graph building)
3. Error condition testing

## Best Practices Observed

1. **Descriptive test names** - Function names read like documentation
2. **Monkeypatch isolation** - Dependencies cleanly mocked, tests independent
3. **Graceful degradation testing** - Tests validate fallback behavior (empty graph returns empty data)
4. **Setup-Act-Assert pattern** - Clear test structure for readability

## Recommendations

1. **Expand test coverage** to API routes and more services
2. **Create `conftest.py`** with shared fixtures for test data
3. **Add parametrized tests** for different input variations
4. **Implement error condition tests** with `pytest.raises()`
5. **Consider frontend testing** with Vitest or Jest if UI becomes complex
6. **Add coverage threshold** (e.g., 70%) to CI/CD pipeline

---

*Testing analysis: 2026-04-13*
