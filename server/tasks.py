"""
Task definitions for the Git Conflict Resolver OpenEnv environment.

Each task contains:
- name, difficulty, description
- filename + file_language
- conflicted_content: the file the agent receives (with markers)
- expected_resolved: ground truth resolved file
- branch_ours / branch_theirs: branch names for context
- num_conflicts: number of conflict blocks
"""

from typing import Any, Dict

TASKS: Dict[str, Dict[str, Any]] = {

    # ─────────────────────────────────────────────────────────────────
    # TASK 1 — Easy: Single conflict block, obvious from context
    # ─────────────────────────────────────────────────────────────────
    "single_conflict": {
        "name": "single_conflict",
        "difficulty": "easy",
        "filename": "config.py",
        "file_language": "python",
        "branch_ours": "main",
        "branch_theirs": "feature/update-timeout",
        "num_conflicts": 1,
        "description": (
            "You are resolving a Git merge conflict in config.py. "
            "The file has ONE conflict block. "
            "The 'feature/update-timeout' branch changed the REQUEST_TIMEOUT from 30 to 60 seconds. "
            "The correct resolution is to accept the incoming change (theirs) — use 60 seconds. "
            "Return the full file with NO conflict markers."
        ),
        "conflicted_content": '''\
# config.py
# Application configuration

APP_NAME = "MyService"
APP_VERSION = "2.1.0"
DEBUG = False

# Network settings
HOST = "0.0.0.0"
PORT = 8080

<<<<<<< HEAD
REQUEST_TIMEOUT = 30  # seconds
=======
REQUEST_TIMEOUT = 60  # seconds — updated for slow upstream APIs
>>>>>>> feature/update-timeout

MAX_RETRIES = 3
LOG_LEVEL = "INFO"
''',
        "expected_resolved": '''\
# config.py
# Application configuration

APP_NAME = "MyService"
APP_VERSION = "2.1.0"
DEBUG = False

# Network settings
HOST = "0.0.0.0"
PORT = 8080

REQUEST_TIMEOUT = 60  # seconds — updated for slow upstream APIs

MAX_RETRIES = 3
LOG_LEVEL = "INFO"
''',
    },

    # ─────────────────────────────────────────────────────────────────
    # TASK 2 — Medium: Three conflict blocks, each needs a different resolution
    # ─────────────────────────────────────────────────────────────────
    "multi_conflict": {
        "name": "multi_conflict",
        "difficulty": "medium",
        "filename": "user_service.py",
        "file_language": "python",
        "branch_ours": "main",
        "branch_theirs": "feature/auth-refactor",
        "num_conflicts": 3,
        "description": (
            "You are resolving a Git merge conflict in user_service.py with THREE conflict blocks. "
            "Resolution rules based on comments and logic: "
            "1) Keep the new import from 'theirs' (bcrypt replaces hashlib). "
            "2) Keep 'ours' version of MAX_LOGIN_ATTEMPTS = 5 (theirs changed to 3, but product decided 5). "
            "3) Keep 'theirs' version of the hash_password function (uses bcrypt, more secure). "
            "Return the complete resolved file with NO conflict markers."
        ),
        "conflicted_content": '''\
# user_service.py
# Handles user authentication and management

<<<<<<< HEAD
import hashlib
=======
import bcrypt
>>>>>>> feature/auth-refactor

import logging
from typing import Optional

logger = logging.getLogger(__name__)

<<<<<<< HEAD
MAX_LOGIN_ATTEMPTS = 5
=======
MAX_LOGIN_ATTEMPTS = 3
>>>>>>> feature/auth-refactor

SESSION_EXPIRY_HOURS = 24


def get_user(user_id: str) -> Optional[dict]:
    """Fetch user record from database."""
    # Implementation omitted for brevity
    return None


<<<<<<< HEAD
def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()
=======
def hash_password(password: str) -> str:
    """Hash a password using bcrypt (more secure)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()
>>>>>>> feature/auth-refactor


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed
''',
        "expected_resolved": '''\
# user_service.py
# Handles user authentication and management

import bcrypt

import logging
from typing import Optional

logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 5

SESSION_EXPIRY_HOURS = 24


def get_user(user_id: str) -> Optional[dict]:
    """Fetch user record from database."""
    # Implementation omitted for brevity
    return None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt (more secure)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed
''',
    },

    # ─────────────────────────────────────────────────────────────────
    # TASK 3 — Hard: Must COMBINE code from both branches (not pick one)
    # ─────────────────────────────────────────────────────────────────
    "logic_conflict": {
        "name": "logic_conflict",
        "difficulty": "hard",
        "filename": "data_pipeline.py",
        "file_language": "python",
        "branch_ours": "main",
        "branch_theirs": "feature/add-validation",
        "num_conflicts": 2,
        "description": (
            "You are resolving a Git merge conflict in data_pipeline.py with TWO conflict blocks. "
            "IMPORTANT: Both sides have valid, additive changes — you must COMBINE them, not pick one. "
            "Block 1: 'ours' adds retry logic, 'theirs' adds timeout parameter — keep BOTH. "
            "Block 2: 'ours' filters out None values, 'theirs' also strips whitespace from strings — keep BOTH operations. "
            "Return the complete resolved file with NO conflict markers."
        ),
        "conflicted_content": '''\
# data_pipeline.py
# Data ingestion and transformation pipeline

import time
import logging
from typing import List, Any, Optional

logger = logging.getLogger(__name__)


<<<<<<< HEAD
def fetch_data(url: str, retries: int = 3) -> dict:
    """Fetch data from an API endpoint with retry logic."""
    for attempt in range(retries):
        try:
            # Simulate HTTP request
            response = make_request(url)
            return response
        except Exception as e:
            if attempt == retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            time.sleep(2 ** attempt)
=======
def fetch_data(url: str, timeout: int = 10) -> dict:
    """Fetch data from an API endpoint with configurable timeout."""
    response = make_request(url, timeout=timeout)
    return response
>>>>>>> feature/add-validation


<<<<<<< HEAD
def clean_records(records: List[Any]) -> List[Any]:
    """Remove None values from records."""
    return [r for r in records if r is not None]
=======
def clean_records(records: List[Any]) -> List[Any]:
    """Strip whitespace from string fields in records."""
    cleaned = []
    for r in records:
        if isinstance(r, str):
            cleaned.append(r.strip())
        else:
            cleaned.append(r)
    return cleaned
>>>>>>> feature/add-validation


def process_batch(records: List[Any]) -> List[Any]:
    """Process a batch of records through the pipeline."""
    cleaned = clean_records(records)
    return cleaned
''',
        "expected_resolved": '''\
# data_pipeline.py
# Data ingestion and transformation pipeline

import time
import logging
from typing import List, Any, Optional

logger = logging.getLogger(__name__)


def fetch_data(url: str, retries: int = 3, timeout: int = 10) -> dict:
    """Fetch data from an API endpoint with retry logic and configurable timeout."""
    for attempt in range(retries):
        try:
            # Simulate HTTP request
            response = make_request(url, timeout=timeout)
            return response
        except Exception as e:
            if attempt == retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            time.sleep(2 ** attempt)


def clean_records(records: List[Any]) -> List[Any]:
    """Remove None values and strip whitespace from string fields."""
    cleaned = []
    for r in records:
        if r is None:
            continue
        if isinstance(r, str):
            cleaned.append(r.strip())
        else:
            cleaned.append(r)
    return cleaned


def process_batch(records: List[Any]) -> List[Any]:
    """Process a batch of records through the pipeline."""
    cleaned = clean_records(records)
    return cleaned
''',
    },
}


def get_task(task_name: str) -> Dict[str, Any]:
    if task_name not in TASKS:
        raise ValueError(f"Unknown task '{task_name}'. Available: {list(TASKS.keys())}")
    return TASKS[task_name]


def list_tasks() -> list:
    return list(TASKS.keys())
