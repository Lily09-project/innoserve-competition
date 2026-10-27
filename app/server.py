from __future__ import annotations
import argparse
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import subprocess
import uuid
import traceback
import time
from settings import runtime_settings, wsl_path
import numpy as np

from pipeline import TrainOnlyBank, run_event, B_NAMES
from network_contract import build_network_scenario, verify_network_receipt

ROOT = Path(__file__).resolve().parents[1]


def prune_jobs(jobs, retention_seconds, maximum, now=None):
    now = time.monotonic() if now is None else now
    completed = sorted(
        ((key, value) for key, value in jobs.items() if value["state"] != "running"),
        key=lambda item: item[1].get("finished_at", now),
    )
    for index, (key, value) in enumerate(completed):
        if (
            now - value.get("finished_at", now) > retention_seconds
            or index < len(completed) - maximum
        ):
            del jobs[key]


def create_server(port=8765, root=ROOT, demo=False):
    root = Path(root)
    runtime = runtime_settings()
    if demo:
        marker = json.loads((root / "demo.json").read_text(encoding="utf-8"))
        if marker != {"kind": "synthetic-demo.v1", "synthetic": True}:
            raise ValueError("invalid_demo_root")
    data = root / "evidence/fresh17"
    bank = TrainOnlyBank.load(data / "train_bank.npz", data / "train_bank_manifest.json")
    events = {
        e["event_id"]: e for e in json.loads((data / "events.json").read_text(encoding="utf-8"))
    }
    cached = {}
    path = data / "judge_records_private.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            cached[value["event_id"]] = value
    lock = threading.Lock()
    job_lock = threading.Lock()
    jobs = {}
    engine = {"value": None}
    live_results = {}
    with np.load(data / "live_inputs_private.npz", allow_pickle=False) as inputs:
        live_ids = inputs["event_ids"].tolist()

    def create_job(action, event_id):
        with job_lock:
            prune_jobs(jobs, runtime["job_retention_seconds"], runtime["max_completed_jobs"])
            if any(j["state"] == "running" for j in jobs.values()):
                return None
            job_id = uuid.uuid4().hex
            jobs[job_id] = {
                "state": "running",
                "phase": "啟動本機工作",
                "action": action,
                "event_id": event_id,
            }

        def progress(message):
            with job_lock:
                jobs[job_id]["phase"] = message

        def work():
            try:
                if action in {"warmup", "live"}:
                    if engine["value"] is None:
                        from live_engine import LiveEngine

                        engine["value"] = LiveEngine(progress)
                    if action == "warmup":
                        result = {"ready": True}
                    else:
                        result = engine["value"].infer(events[event_id], progress)
                        live_results[event_id] = result
                else:
                    event = live_results[event_id]
                    progress("建立隔離Mininet並驗證策略，規則於30秒到期回復")
                    folder = root / "evidence/live_network" / job_id
                    folder.mkdir(parents=True)
                    scenario = build_network_scenario(event)
                    scenario_path = folder / "scenario.json"
                    output_path = folder / "result.json"
                    scenario_path.write_text(
                        json.dumps(scenario, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    process = subprocess.run(
                        [
                            "wsl",
                            "-d",
                            runtime["wsl_distribution"],
                            "-u",
                            runtime["wsl_user"],
                            "--",
                            "python3",
                            wsl_path(
                                root / "scripts/live_network_test.py", runtime["wsl_mount_root"]
                            ),
                            "--scenario",
                            wsl_path(scenario_path, runtime["wsl_mount_root"]),
                            "--output",
                            wsl_path(output_path, runtime["wsl_mount_root"]),
                        ],
                        capture_output=True,
                        timeout=runtime["network_timeout_seconds"],
                    )
                    (folder / "process.log").write_bytes(process.stdout + process.stderr)
                    if process.returncode != 0 or not output_path.exists():
                        raise RuntimeError("isolated_network_test_failed")
                    result = json.loads(output_path.read_text(encoding="utf-8"))
                    if not verify_network_receipt(scenario, result):
                        raise RuntimeError("network_receipt_binding_failed")
                    event["network_receipt"] = result
                with job_lock:
                    jobs[job_id].update(
                        {
                            "state": "done",
                            "phase": "執行完成",
                            "result": result,
                            "finished_at": time.monotonic(),
                        }
                    )
            except Exception:
                folder = root / "validation"
                folder.mkdir(exist_ok=True)
                (folder / ("job-" + job_id + ".log")).write_text(
                    traceback.format_exc(), encoding="utf-8"
                )
                with job_lock:
                    jobs[job_id].update(
                        {
                            "state": "error",
                            "phase": "執行中止，已保留本機診斷紀錄",
                            "error": "execution_failed",
                            "finished_at": time.monotonic(),
                        }
                    )

        threading.Thread(target=work, daemon=True).start()
        return job_id

    class Handler(SimpleHTTPRequestHandler):
        def json_response(self, value, status=200):
            encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def do_GET(self):
            if self.path == "/api/status":
                self.json_response(
                    {
                        "product": "ai-security-demo.v3",
                        "model_ready": engine["value"] is not None,
                        "live_event_ids": [] if demo else live_ids,
                        "synthetic": demo,
                    }
                )
                return
            if self.path.startswith("/api/jobs/"):
                key = self.path.split("/")[-1]
                with job_lock:
                    prune_jobs(
                        jobs, runtime["job_retention_seconds"], runtime["max_completed_jobs"]
                    )
                    value = {k: v for k, v in jobs.get(key, {}).items() if k != "finished_at"}
                self.json_response(value, 200 if value else 404)
                return
            if self.path.startswith("/api/"):
                self.send_error(404)
                return
            return super().do_GET()

        def do_POST(self):
            if self.path not in {"/api/retrieve", "/api/operate", "/api/stop", "/api/export"}:
                self.send_error(404)
                return
            origin = self.headers.get("Origin")
            if origin and origin != "http://127.0.0.1:" + str(server.server_port):
                self.send_error(403)
                return
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                self.send_error(415)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size < 2048:
                    raise ValueError()
                request = json.loads(self.rfile.read(size))
                if not isinstance(request, dict):
                    raise ValueError("request_must_be_object")
                if self.path == "/api/stop":
                    with job_lock:
                        active = any(j["state"] == "running" for j in jobs.values())
                    if active:
                        self.json_response({"error": "busy"}, 409)
                        return
                    self.json_response({"stopped": True})
                    threading.Thread(target=server.shutdown, daemon=True).start()
                    return
                if self.path == "/api/operate":
                    if demo:
                        self.json_response(
                            {
                                "error": "synthetic_execution_disabled",
                                "message": "合成展示不執行模型或網路處置。",
                            },
                            403,
                        )
                        return
                    action = request.get("action")
                    key = request.get("event_id")
                    if not isinstance(action, str) or (
                        action != "warmup" and not isinstance(key, str)
                    ):
                        raise ValueError("invalid_action_or_event_id")
                    if action not in {"warmup", "live", "network"}:
                        raise ValueError()
                    if action == "live" and key not in live_ids:
                        raise ValueError()
                    if action == "network":
                        if key not in live_results:
                            raise ValueError()
                        e = live_results[key]
                        if request.get("execution_id") != e["execution_id"]:
                            raise ValueError("stale_execution")
                        if e["prediction"] not in B_NAMES or e["validation_label"] not in B_NAMES:
                            raise ValueError()
                    job_id = create_job(action, key)
                    self.json_response({"job_id": job_id}, 202) if job_id else self.json_response(
                        {"error": "busy", "message": "已有本機工作執行中，請稍後重試。"}, 409
                    )
                    return
                if self.path == "/api/export" and request.get("mode") == "live_local_models":
                    key = request.get("event_id")
                    if not isinstance(key, str) or key not in live_results:
                        raise ValueError("unknown_live_event")
                    event = live_results[key]
                    if request.get("execution_id") != event["execution_id"]:
                        raise ValueError("stale_export_execution")
                    # Keep Python's original JSON number representation intact for hash verification.
                    self.json_response(event)
                    return
                if self.path == "/api/export" and request.get("mode") != "saved_prediction_replay":
                    raise ValueError("invalid_export_mode")
                key = request.get("event_id")
                if not isinstance(key, str) or key not in events:
                    raise ValueError("unknown_event")
                event = events[key]
                with lock:
                    result = run_event(event, bank, cached.get(event["event_id"]))
                # Return a complete frozen snapshot; never combine it with a live prediction in the client.
                replay = {
                    k: v
                    for k, v in event.items()
                    if k
                    not in {
                        "embedding",
                        "model_sha256",
                        "execution_id",
                        "timings",
                        "network_receipt",
                    }
                }
                replay.update(
                    {
                        "result": result,
                        "evidence": result["evidence"],
                        "execution_mode": "saved_prediction_retrieval_recomputed",
                    }
                )
                self.json_response(
                    replay if self.path == "/api/export" else {**result, "replay_event": replay}
                )
            except (ValueError, TypeError) as exc:
                code = (
                    str(exc)
                    if str(exc)
                    in {
                        "unknown_event",
                        "unknown_live_event",
                        "invalid_action_or_event_id",
                        "stale_execution",
                        "stale_export_execution",
                        "invalid_export_mode",
                        "request_must_be_object",
                    }
                    else "invalid_request"
                )
                self.json_response(
                    {"error": code, "message": "事件、批次或請求格式不符，請重新選擇事件。"}, 400
                )

        def log_message(self, fmt, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(root / "web")))
    server.daemon_threads = True
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=runtime_settings()["service_port"])
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Synthetic public demo; disables model and network execution",
    )
    parser.add_argument("--demo-root", type=Path, default=ROOT / "runtime/synthetic-demo")
    args = parser.parse_args()
    root = ROOT
    if args.demo:
        root = args.demo_root.resolve()
        if not (root / "demo.json").exists():
            sys.path.insert(0, str(ROOT / "scripts"))
            from make_demo_assets import make_demo_assets

            make_demo_assets(root)
        print("SYNTHETIC DATA — NOT EXPERIMENTAL RESULTS", flush=True)
    server = create_server(args.port, root, demo=args.demo)
    print(f"http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
