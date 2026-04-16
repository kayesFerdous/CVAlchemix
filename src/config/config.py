import json
from platformdirs import user_config_dir
from pathlib import Path

APP_NAME = "CVAlchemix"

def get_config_path() -> Path:
    config_dir = Path(user_config_dir(APP_NAME))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"

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
