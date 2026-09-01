"""WIA global constants and configuration defaults."""

from pathlib import Path

# Directory & file names
WIA_DIR_NAME = ".wia"
WIA_CONFIG_FILE = "config.json"
WIA_INDEX_FILE = "index.json"

# Schema versioning
CURRENT_INDEX_SCHEMA_VERSION = "1.0"
CURRENT_CONFIG_SCHEMA_VERSION = "1.0"

# Defaults
DEFAULT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit for raw indexing
DEFAULT_HASH_ALGORITHM = "sha256"
