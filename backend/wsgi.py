"""WSGI entrypoint for production servers."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def _validate_config():
    errors = Config.validate()
    if errors:
        details = "\n  - ".join(errors)
        raise RuntimeError(f"Invalid MiroFish configuration:\n  - {details}")


_validate_config()
app = create_app()
