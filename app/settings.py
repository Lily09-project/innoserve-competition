"""Read local asset locations without embedding workstation paths in public code."""
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def config():
    path=ROOT / "config.local.json"
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def optional_asset_path(name,default):
    value=os.getenv("INNOSERVE_"+name.upper()) or config().get(name)
    return Path(value).expanduser().resolve() if value else Path(default)


def asset_path(name):
    value=os.getenv("INNOSERVE_"+name.upper()) or config().get(name)
    if not value:raise RuntimeError("Configure "+name+" in config.local.json or INNOSERVE_"+name.upper())
    result=Path(value).expanduser().resolve()
    if not result.exists():raise FileNotFoundError("Configured asset is unavailable: "+name)
    return result
