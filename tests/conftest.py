import os
import tempfile

# The application reads its settings at import time: set them before any
# mathutrice module is imported.
_db_dir = tempfile.mkdtemp(prefix="mathutrice-tests-")
os.environ.update(
    {
        "AUTH_MODE": "dev",
        "SESSION_SECRET": "test-secret",
        "DATABASE_URL": f"sqlite:///{_db_dir}/app.db",
        "LLM_BASE_URL": "http://localhost:0/v1",
        "LLM_API_KEY": "test-key",
        "LLM_MODEL": "test-model",
    }
)
