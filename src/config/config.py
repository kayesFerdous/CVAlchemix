import json
from pathlib import Path

from platformdirs import user_config_dir

config_dir = Path(user_config_dir("cvalchemix"))
PROFILE_DIR = config_dir / "linkedin_profile"


def ensure_config_dir() -> Path:
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def ensure_profile_dir() -> Path:
    ensure_config_dir()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILE_DIR


ensure_config_dir()

def get_config_path() -> Path:
    return ensure_config_dir() / "config.json"

def save_config(data: dict):
    path = get_config_path()
    existing = load_config()
    existing.update(data)
    path.write_text(json.dumps(existing, indent=2))

def load_config() -> dict:
    path = get_config_path()
    return json.loads(path.read_text()) if path.exists() else {}

def get(key: str):
    return load_config().get(key)
