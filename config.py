import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _env_int(name: str, default: int | None = None, required: bool = False) -> int | None:
    value = os.getenv(name)
    if value is None or value == "":
        if required:
            raise RuntimeError(f"Missing required env var: {name}")
        return default
    return int(value)


def _env_int_set(name: str) -> set[int]:
    value = os.getenv(name, "")
    items = [v.strip() for v in value.split(",") if v.strip()]
    return {int(v) for v in items}


def _manual_load_env(dotenv_path: Path) -> None:
    try:
        content = dotenv_path.read_text(encoding="utf-8")
    except OSError:
        return
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class Config:
    bot_token: str
    admin_group_id: int
    admin_ids: set[int]
    db_path: str


def load_config() -> Config:
    dotenv_path = Path(__file__).with_name(".env")
    if dotenv_path.exists():
        _manual_load_env(dotenv_path)
        if load_dotenv:
            load_dotenv(dotenv_path=dotenv_path, override=False, encoding="utf-8-sig")

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing BOT_TOKEN in environment")

    admin_group_id = _env_int("ADMIN_GROUP_ID", required=True)
    admin_ids = _env_int_set("ADMIN_IDS")
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is empty. Provide at least one admin user id.")

    db_path = os.getenv("DB_PATH", "bot.db")

    return Config(
        bot_token=token,
        admin_group_id=admin_group_id,
        admin_ids=admin_ids,
        db_path=db_path,
    )
