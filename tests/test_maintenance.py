"""Public setup, data separation and fail-closed parsing regression tests."""

import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "app"), str(ROOT / "scripts")]
import settings
from integrity import digest, verify_ledger
from judge_response import parse_judge_response
from server import create_server, prune_jobs
from make_demo_assets import make_demo_assets
from import_local_assets import REQUIRED, import_assets
from preflight import check_assets


class SettingsTests(unittest.TestCase):
    def test_defaults_and_overrides(self):
        with patch.object(settings, "config", return_value={"service_port": 9000}):
            self.assertEqual(settings.runtime_settings()["service_port"], 9000)
            self.assertEqual(settings.runtime_settings()["network_timeout_seconds"], 100)

    def test_invalid_runtime_values(self):
        for value in (0, -1, True, "10", None):
            with patch.object(settings, "config", return_value={"job_retention_seconds": value}):
                with self.assertRaises(ValueError):
                    settings.runtime_settings()

    def test_paths(self):
        self.assertEqual(settings.wsl_path(r"D:\demo\test.json"), "/mnt/d/demo/test.json")
        self.assertEqual(settings.wsl_path("C:/demo", "/custom"), "/custom/c/demo")
        for path in ("relative/file", r"\\server\file"):
            with self.assertRaises(ValueError):
                settings.wsl_path(path)

    def test_bom_config_and_shape(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(settings, "ROOT", Path(folder)):
            path = Path(folder) / "config.local.json"
            path.write_text('{"service_port":9001}', encoding="utf-8-sig")
            self.assertEqual(settings.config()["service_port"], 9001)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                settings.config()


class MaintenanceTests(unittest.TestCase):
    def test_job_cleanup_retains_running(self):
        jobs = {
            "run": {"state": "running"},
            "old": {"state": "done", "finished_at": 0},
            "new": {"state": "error", "finished_at": 95},
        }
        prune_jobs(jobs, 30, 1, now=100)
        self.assertEqual(set(jobs), {"run", "new"})

    def test_judge_json(self):
        for raw in (
            '```json\n{"assessment":"support","reason":"braces {ok}"}\n```',
            '{"assessment":"support","reason":"ok","detail":{"x":1}}',
        ):
            self.assertEqual(parse_judge_response(raw)["assessment"], "support")
        for raw in (
            "{}",
            "hello",
            '{"assessment":"support","reason":""}',
            '{"assessment":"support","reason":"a"} {"assessment":"review","reason":"b"}',
        ):
            with self.assertRaises(ValueError):
                parse_judge_response(raw)

    def test_integrity_invalid_inputs_fail_closed(self):
        for ledger in (None, [], [1], [{}]):
            self.assertFalse(verify_ledger(ledger))
        with self.assertRaises(ValueError):
            digest({"x": float("nan")})

    def test_import_validation_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / "source", Path(folder) / "target"
            with self.assertRaises(FileNotFoundError):
                import_assets(source, target)
            self.assertFalse(target.exists())
            assets = source / "evidence/fresh17"
            assets.mkdir(parents=True)
            for name in REQUIRED:
                (assets / name).write_text(name)
            (assets / "unrelated-secret.txt").write_text("must stay private")
            result = import_assets(source, target)
            self.assertEqual({p.name for p in result.iterdir()}, set(REQUIRED))
            with self.assertRaises(FileExistsError):
                import_assets(source, target)
            with self.assertRaises(ValueError):
                import_assets(source, source / "nested")

    def test_preflight_missing_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                check_assets(folder)

    def test_preflight_valid_assets_and_missing_judge(self):
        with tempfile.TemporaryDirectory() as folder:
            root = make_demo_assets(Path(folder) / "demo")
            judge = root / "evidence/fresh17/judge_records_private.jsonl"
            judge.write_text("", encoding="utf-8")
            self.assertEqual(check_assets(root)["train_cases"], 85)
            judge.unlink()
            with self.assertRaises(FileNotFoundError):
                check_assets(root)

    def test_pages_build_excludes_private_assets(self):
        from build_pages import build_pages

        with tempfile.TemporaryDirectory() as folder:
            output = build_pages(Path(folder) / "site")
            self.assertFalse((output / "evidence").exists())
            self.assertFalse((output / "config.local.json").exists())
            manifest = json.loads((output / "site-manifest.json").read_text())
            self.assertTrue(manifest["synthetic"])
            self.assertEqual(manifest["video_seconds"], 45)
            with self.assertRaises(FileExistsError):
                build_pages(output)

    def test_public_demo_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            root = make_demo_assets(Path(folder) / "demo")
            with self.assertRaises(FileExistsError):
                make_demo_assets(root)
            server = create_server(0, root, demo=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = "http://127.0.0.1:" + str(server.server_port)
            try:
                with urllib.request.urlopen(base + "/api/status") as response:
                    status = json.load(response)
                self.assertTrue(status["synthetic"])
                self.assertEqual(status["live_event_ids"], [])
                request = urllib.request.Request(
                    base + "/api/operate",
                    data=b'{"action":"warmup"}',
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(request)
                self.assertEqual(error.exception.code, 403)
                request = urllib.request.Request(
                    base + "/api/retrieve",
                    data=b'{"event_id":"synthetic-event-07"}',
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(request) as response:
                    event = json.load(response)["replay_event"]
                self.assertTrue(event["synthetic"])
                self.assertTrue(verify_ledger(event["result"]["ledger"]))
                self.assertFalse(event["result"]["policy"]["allowed"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(5)
