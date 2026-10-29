"""Validated local configuration; relative asset paths are repository-relative."""
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXECUTION_DEFAULTS = {
    'wsl_distribution': 'Ubuntu-24.04', 'wsl_user': 'root',
    'network_timeout_seconds': 100, 'warmup_timeout_seconds': 180,
    'job_retention_seconds': 3600, 'max_completed_jobs': 128,
}


def config():
    path=ROOT / "config.local.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, OSError):
        raise ValueError('Invalid local configuration JSON') from None
    if not isinstance(value, dict):
        raise ValueError('Local configuration must be a JSON object')
    return value


def configured(name, default=None):
    return os.getenv('INNOSERVE_'+name.upper()) or config().get(name, default)


def resolve_path(name, value):
    if not isinstance(value, (str, os.PathLike)) or not str(value).strip():
        raise ValueError('Invalid path setting: '+name)
    path = Path(value).expanduser()
    return (path if path.is_absolute() else ROOT / path).resolve()


def optional_asset_path(name,default):
    value = configured(name)
    return resolve_path(name, value if value not in (None, '') else default)


def asset_path(name):
    value=configured(name)
    if value in (None, ''):raise RuntimeError("Configure "+name+" in config.local.json or INNOSERVE_"+name.upper())
    result=resolve_path(name,value)
    if not result.exists():raise FileNotFoundError("Configured asset is unavailable: "+name)
    return result


def execution_settings():
    result = {}
    for name, default in EXECUTION_DEFAULTS.items():
        value = configured(name, default)
        if isinstance(default, int):
            if isinstance(value, bool) or not str(value).isdigit() or int(value) < 1:
                raise ValueError('Invalid positive integer setting: '+name)
            value = int(value)
        elif not isinstance(value, str) or not value.strip() or '\x00' in value:
            raise ValueError('Invalid execution setting: '+name)
        result[name] = value
    return result
