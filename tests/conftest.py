"""Make every test pass with no .env, as CI has none.

This runs before the first import of the Project: pytest loads conftest.py
before it collects the test modules.
"""

import os

import dotenv

# The Project calls load_dotenv() at import time. Without it, nothing reads a
# local .env, so a test never depends on one.
dotenv.load_dotenv = lambda *args, **kwargs: False

# The LLM client refuses to import without these three. Dummy values: no test
# calls a real LLM.
os.environ["LLM_BASE_URL"] = "http://localhost:0/v1"
os.environ["LLM_API_KEY"] = "dummy"
os.environ["LLM_MODEL"] = "dummy"
