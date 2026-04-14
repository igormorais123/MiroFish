# Coding Conventions

**Analysis Date:** 2026-04-13

## Naming Patterns

**Files:**
- Python: `snake_case.py` (e.g., `graph_builder.py`, `zep_entity_reader.py`)
- Vue: `PascalCase.vue` for components (e.g., `GraphPanel.vue`, `Step1GraphBuild.vue`)
- JavaScript: `camelCase.js` for utilities (e.g., `pendingUpload.js`, `index.js`)
- Test files: `test_*.py` prefix (e.g., `test_graph_builder.py`)

**Functions & Methods:**
- Python: `snake_case` for functions and methods (e.g., `wait_for_graph_materialization()`, `get_logger()`)
- JavaScript/Vue: `camelCase` for functions and methods (e.g., `detectBaseURL()`, `requestWithRetry()`)
- Private/internal functions: prefix with underscore `_function_name()` (e.g., `_ensure_utf8_stdout()`, `_first_non_empty()`)

**Variables:**
- Python: `snake_case` (e.g., `graph_id`, `entity_types`, `max_retries`)
- JavaScript/Vue: `camelCase` (e.g., `baseURL`, `graphData`, `isPending`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `INTERVIEW_PROMPT_PREFIX`, `MAX_CONTENT_LENGTH`)

**Types/Classes:**
- Python: `PascalCase` (e.g., `SimulationManager`, `ProjectStatus`, `OasisProfileGenerator`)
- Enums: `PascalCase` with `PascalCase` members (e.g., `SimulationStatus.CREATED`, `ProjectStatus.GRAPH_BUILDING`)
- Vue: Components are `PascalCase` (e.g., `GraphPanel`, `Step2EnvSetup`)

## Code Style

**Formatting:**
- Language: **Portuguese** for all docstrings, comments, and variable naming
- Indentation: **4 spaces** for Python, **2 spaces** for JavaScript/Vue
- Line length: **No strict enforced limit**, but keep readable
- No external formatter detected (no Prettier, Black, ESLint config found)

**Linting:**
- **Not enforced** — no `.eslintrc`, `.prettierrc`, or `setup.cfg` present
- Python follows PEP 8 conventions informally via naming patterns observed
- Vue follows standard Vue 3 composition API patterns

## Import Organization

**Python Order:**
1. Standard library imports (`os`, `json`, `logging`, `typing`, etc.)
2. Third-party imports (`flask`, `pydantic`, `dataclasses`, etc.)
3. Relative imports from same project (`from ..config import Config`, `from ..utils.logger import get_logger`)

**Example from `backend/app/api/simulation.py`:**
```python
import os
import traceback
from flask import request, jsonify, send_file

from . import simulation_bp
from ..config import Config
from ..services.zep_entity_reader import ZepEntityReader
from ..utils.logger import get_logger
```

**JavaScript Order:**
1. Third-party imports (`axios`, `vue`, etc.)
2. Project imports (`../api/...`, `../store/...`, etc.)

**Example from `frontend/src/router/index.js`:**
```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Process from '../views/MainView.vue'
```

**Path Aliases:**
- No configured aliases detected
- Use relative paths: `../components/`, `../utils/`, etc.

## Error Handling

**Patterns:**

**Python:**
- Try-catch with explicit `Exception` handling and logging:
```python
try:
    # operation
except Exception as e:
    logger.error(f"Error message: {str(e)}")
    logger.error(traceback.format_exc())  # Always include traceback for debugging
    return jsonify({
        "success": False,
        "error": str(e)
    }), 500
```

- Custom exceptions via Enum status classes (e.g., `SimulationStatus.FAILED`, `ProjectStatus.FAILED`)
- Always log full traceback with `traceback.format_exc()` for unhandled exceptions
- API returns: `{"success": False, "error": "message"}` with HTTP status code

**JavaScript/Vue:**
- Promise-based error handling with catch blocks:
```javascript
service.interceptors.response.use(
  response => {
    if (!res.success && res.success !== undefined) {
      console.error('Error:', res.error)
      return Promise.reject(new Error(res.error))
    }
    return res
  },
  error => {
    console.error('Response error:', error)
    return Promise.reject(error)
  }
)
```

- Specific error type detection (e.g., `error.code === 'ECONNABORTED'` for timeouts)
- Console.error for client-side logging (no dedicated logger)

## Logging

**Framework:** Custom JSON formatter in `backend/app/utils/logger.py`

**Patterns:**

- Get logger instance with `logger = get_logger('module.name')`
- Structured JSON logging with fields:
```python
logger.info(f"Message here: key_value={value}", extra={"contextual_field": "value"})
```

- Log levels used: `debug()`, `info()`, `warning()`, `error()`, `critical()`
- Each log entry includes: `timestamp`, `level`, `logger` name, `message`, `traceback` (if exception)
- Example from `backend/app/api/simulation.py`:
```python
logger = get_logger('mirofish.api.simulation')
logger.info(f"Obtaining entities: graph_id={graph_id}, entity_types={entity_types}")
logger.error(f"Failed to get entities: {str(e)}")
logger.error(traceback.format_exc())
```

**File Handlers:**
- Console handler: `INFO` and above (simplified output)
- File handler: `DEBUG` and above (full details, rotated daily with 10MB max, 5 backups)
- UTF-8 encoded on all platforms (Windows specifically handled)

**Client-side (JavaScript):**
- Use `console.error()`, `console.warn()` for debugging
- Example from `frontend/src/api/index.js`:
```javascript
console.error('API Error:', res.error || res.message || 'Unknown error')
console.warn(`Request failed, retrying (${i + 1}/${maxRetries})...`)
```

## Comments

**When to Comment:**
- Function docstrings: **Required** for all public functions and API routes
- Inline comments: When logic is non-obvious or complex
- Module-level docstrings: Describe purpose and main responsibility
- Portuguese language: All comments and docstrings in Brazilian Portuguese

**JSDoc/TSDoc:**
- Python uses docstring format with Google-style parameters:
```python
def function_name(param1: str, param2: int):
    """
    One-line description.
    
    Multi-line description if needed.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Description of return value
    """
```

- Vue: Simple inline comments, minimal JSDoc
- No TypeScript annotations used (JavaScript ES6 modules)

## Function Design

**Size:** 
- Aim for functions under 50 lines where practical
- Longer functions acceptable when they handle sequential steps (e.g., `wait_for_graph_materialization`)
- API route handlers typically 20-40 lines with try-catch wrapper

**Parameters:**
- Use type hints in Python (e.g., `def func(param: str) -> Dict[str, Any]:`)
- Optional parameters use `Optional[Type]` or default values
- Dataclasses preferred for grouping related parameters (e.g., `SimulationState` dataclass)
- No positional-only or keyword-only patterns enforced

**Return Values:**
- Python APIs return `jsonify()` wrapped dictionaries with `{"success": bool, "data"|"error": ...}` format
- Service methods return typed objects (dataclass instances) or basic types
- Vue functions return Promises or plain values

## Module Design

**Exports:**
- Python: Use `__init__.py` to organize imports but minimal barrel exports
- Flask blueprints: Registered in main app (e.g., `simulation_bp` in `api/simulation.py`)
- JavaScript: Direct named exports from utility files (e.g., `export const requestWithRetry = ...`)

**Barrel Files:**
- Minimal use; `__init__.py` files mostly empty or re-export main classes
- Vue components imported directly by path
- No index.js barrel exports in src/ directories except `main.js` (app entry point)

**Project Structure:**
- Backend: Organized by layer (`api/`, `services/`, `models/`, `utils/`)
- Frontend: Organized by feature (`components/`, `views/`, `api/`, `router/`, `store/`)
- Each API route gets its own docstring describing the endpoint behavior

---

*Convention analysis: 2026-04-13*
