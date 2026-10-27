"""Read local asset locations without embedding workstation paths in public code."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def config():
    path = ROOT / "config.local.json"
    value = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
    if not isinstance(value, dict):
        raise ValueError("config_must_be_object")
    return value


def runtime_settings():
    values = config()
    defaults = {
        "wsl_distribution": "Ubuntu-24.04",
        "wsl_user": "root",
        "network_timeout_seconds": 100,
        "wsl_probe_timeout_seconds": 20,
        "job_retention_seconds": 3600,
        "max_completed_jobs": 100,
        "service_port": 8765,
        "wsl_mount_root": "/mnt",
    }
    result = {name: values.get(name, default) for name, default in defaults.items()}
    for name in (
        "network_timeout_seconds",
        "wsl_probe_timeout_seconds",
        "job_retention_seconds",
        "max_completed_jobs",
        "service_port",
    ):
        if type(result[name]) is not int or result[name] <= 0:
            raise ValueError("invalid_runtime_setting:" + name)
    if result["service_port"] > 65535:
        raise ValueError("invalid_service_port")
    for name in ("wsl_distribution", "wsl_user", "wsl_mount_root"):
        if not isinstance(result[name], str) or not result[name].strip():
            raise ValueError("invalid_runtime_setting:" + name)
    return result


def wsl_path(path, mount_root="/mnt"):
    value = str(path).replace("\\", "/")
    if len(value) > 2 and value[1] == ":" and value[0].isalpha() and value[2] == "/":
        return mount_root.rstrip("/") + "/" + value[0].lower() + value[2:]
    if value.startswith("/") and not value.startswith("//"):
        return value
    raise ValueError("unsupported_wsl_path")


def optional_asset_path(name, default):
    value = os.getenv("INNOSERVE_" + name.upper()) or config().get(name)
    return Path(value).expanduser().resolve() if value else Path(default)


def asset_path(name):
    value = os.getenv("INNOSERVE_" + name.upper()) or config().get(name)
    if not value:
        raise RuntimeError(
            "Configure " + name + " in config.local.json or INNOSERVE_" + name.upper()
        )
    result = Path(value).expanduser().resolve()
    if not result.exists():
        raise FileNotFoundError("Configured asset is unavailable: " + name)
    return result
