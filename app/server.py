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
import numpy as np

from pipeline import TrainOnlyBank, run_event, B_NAMES
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    data = ROOT / "evidence/fresh17"
    bank = TrainOnlyBank.load(data / "train_bank.npz", data / "train_bank_manifest.json")
    events = {e["event_id"]: e for e in json.loads((data / "events.json").read_text(encoding="utf-8"))}
    cached = {}
    path = data / "judge_records_private.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line); cached[value["event_id"]] = value
    lock = threading.Lock()
    job_lock = threading.Lock()
    jobs = {}
    engine = {"value": None}
    live_results = {}
    with np.load(data / "live_inputs_private.npz",allow_pickle=False) as inputs:
        live_ids = inputs["event_ids"].tolist()

    def create_job(action,event_id):
        with job_lock:
            if any(j["state"]=="running" for j in jobs.values()):
                return None
            job_id=uuid.uuid4().hex
            jobs[job_id]={"state":"running","phase":"啟動本機工作","action":action,"event_id":event_id}
        def progress(message):
            with job_lock:jobs[job_id]["phase"]=message
        def work():
            try:
                if action in {"warmup","live"}:
                    if engine["value"] is None:
                        from live_engine import LiveEngine
                        engine["value"]=LiveEngine(progress)
                    if action=="warmup":result={"ready":True}
                    else:
                        result=engine["value"].infer(events[event_id],progress)
                        live_results[event_id]=result
                else:
                    event=live_results[event_id]
                    policy=event["result"]["policy"]
                    progress("建立隔離Mininet並驗證策略，規則於30秒到期回復")
                    folder=ROOT / "evidence/live_network" / job_id
                    folder.mkdir(parents=True)
                    scenario={"event_id":event_id,"true_label":B_NAMES[event["validation_label"]],
                              "reason_label":B_NAMES[event["prediction"]],
                              "assessment":event["result"]["judge"]["assessment"],
                              "action":policy["action"] if policy["allowed"] else "capture_evidence",
                              "ttl_seconds":30}
                    scenario_path=folder / "scenario.json";output_path=folder / "result.json"
                    scenario_path.write_text(json.dumps(scenario,ensure_ascii=False,indent=2),encoding="utf-8")
                    def linux(p):
                        value=str(p).replace("\\","/")
                        return "/mnt/"+value[0].lower()+value[2:] if len(value)>2 and value[1]==":" else value
                    process=subprocess.run(["wsl","-d","Ubuntu-24.04","-u","root","--","python3",
                         linux(ROOT / "scripts/live_network_test.py"),"--scenario",linux(scenario_path),"--output",linux(output_path)],
                         capture_output=True,timeout=100)
                    (folder / "process.log").write_bytes(process.stdout+process.stderr)
                    if process.returncode!=0 or not output_path.exists():raise RuntimeError("isolated_network_test_failed")
                    result=json.loads(output_path.read_text(encoding="utf-8"))
                with job_lock:jobs[job_id].update({"state":"done","phase":"執行完成","result":result})
            except Exception:
                folder=ROOT / "validation";folder.mkdir(exist_ok=True)
                (folder / ("job-"+job_id+".log")).write_text(traceback.format_exc(),encoding="utf-8")
                with job_lock:jobs[job_id].update({"state":"error","phase":"執行中止，已保留本機診斷紀錄"})
        threading.Thread(target=work,daemon=True).start()
        return job_id
    class Handler(SimpleHTTPRequestHandler):
        def json_response(self,value,status=200):
            encoded=json.dumps(value,ensure_ascii=False,allow_nan=False).encode("utf-8")
            self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(encoded)));self.end_headers();self.wfile.write(encoded)
        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            super().end_headers()
        def do_GET(self):
            if self.path=="/api/status":
                self.json_response({"product":"ai-security-demo.v1","model_ready":engine["value"] is not None,"live_event_ids":live_ids});return
            if self.path.startswith("/api/jobs/"):
                key=self.path.split("/")[-1]
                with job_lock:value=dict(jobs.get(key,{}))
                self.json_response(value,200 if value else 404);return
            if self.path.startswith("/api/"):self.send_error(404);return
            return super().do_GET()
        def do_POST(self):
            if self.path not in {"/api/retrieve","/api/operate","/api/stop"}: self.send_error(404); return
            origin = self.headers.get("Origin")
            if origin and origin != "http://127.0.0.1:" + str(args.port): self.send_error(403); return
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                self.send_error(415); return
            if self.path=="/api/stop":
                with job_lock:active=any(j["state"]=="running" for j in jobs.values())
                if active:self.json_response({"error":"busy"},409);return
                self.json_response({"stopped":True})
                threading.Thread(target=server.shutdown,daemon=True).start();return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size < 2048: raise ValueError()
                request = json.loads(self.rfile.read(size))
                if self.path=="/api/operate":
                    action=request.get("action");key=request.get("event_id")
                    if action not in {"warmup","live","network"}:raise ValueError()
                    if action=="live" and key not in live_ids:raise ValueError()
                    if action=="network":
                        if key not in live_results:raise ValueError()
                        e=live_results[key]
                        if e["prediction"] not in B_NAMES or e["validation_label"] not in B_NAMES:raise ValueError()
                    job_id=create_job(action,key)
                    self.json_response({"job_id":job_id},202) if job_id else self.json_response({"error":"busy"},409)
                    return
                event = events[request["event_id"]]
                with lock: result = run_event(event, bank, cached.get(event["event_id"]))
                self.json_response(result)
            except (ValueError, KeyError, TypeError): self.send_error(400, "Invalid or unbound event request")
        def log_message(self, fmt, *args): pass
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(ROOT / "web")))
    print(f"http://127.0.0.1:{args.port}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__": main()
