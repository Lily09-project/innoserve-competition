"""Read-only finals workstation checks; optionally preload the local model server."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "app"))
from settings import asset_path,optional_asset_path
from pipeline import TrainOnlyBank,digest


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--warmup",action="store_true");args=parser.parse_args()
    checks=[]
    def check(name,fn):
        try:detail=fn();checks.append({"check":name,"passed":True,"detail":detail});print("PASS",name,flush=True)
        except Exception as exc:checks.append({"check":name,"passed":False,"error":str(exc)});print("FAIL",name,flush=True)
    def assets():
        folder=ROOT / "evidence/fresh17"
        bank=TrainOnlyBank.load(folder / "train_bank.npz",folder / "train_bank_manifest.json")
        for name in ("events.json","live_inputs_private.npz","judge_records_private.jsonl"):
            if not (folder / name).is_file():raise FileNotFoundError(name)
        return {"train_cases":len(bank.ids),"representation":bank.representation_id}
    def models():
        ref=asset_path("ids_reference_root")
        manifest=json.loads((ROOT / "evidence/fresh17/train_bank_manifest.json").read_text(encoding="utf-8"))
        hashes={}
        for name in manifest["model_hashes"]:
            h=hashlib.sha256()
            with (ref / "models/augmented/seed_42" / name / "best_model.pt").open("rb") as f:
                for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
            hashes[name]=h.hexdigest()
        if hashes!=manifest["model_hashes"] or digest(hashes)!=manifest["model_sha256"]:raise ValueError("checkpoint mismatch")
        gate=optional_asset_path("gate_impl_path",ref.parent / "gate_soft_oof_search.py")
        if not gate.is_file():raise FileNotFoundError("gate_impl_path")
        llm=asset_path("llama_model_dir")
        if not list(llm.glob("*.safetensors")) or not (llm / "config.json").is_file():raise FileNotFoundError("local Llama weights")
        return {"verified_checkpoints":len(hashes),"local_llm_weights":True}
    def gpu():
        import torch
        if not torch.cuda.is_available():raise RuntimeError("This finals setup requires the validated CUDA workstation")
        return {"device":torch.cuda.get_device_name(0),"torch":torch.__version__}
    def network():
        code="import mininet; from mininet.net import Mininet; import shutil; assert shutil.which('iptables'); print('MININET_READY')"
        result=subprocess.run(["wsl","-d","Ubuntu-24.04","-u","root","--","python3","-c",code],capture_output=True,timeout=20)
        if result.returncode or b"MININET_READY" not in result.stdout:raise RuntimeError("WSL/Mininet/iptables unavailable")
        return "isolated network dependencies available"
    def service():
        with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=5) as res:value=json.load(res)
        if value["product"]!="ai-security-demo.v3" or len(value["live_event_ids"])!=17:raise ValueError("wrong service or inputs")
        if args.warmup and not value["model_ready"]:
            req=urllib.request.Request("http://127.0.0.1:8765/api/operate",data=b'{"action":"warmup"}',headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=10) as res:job=json.load(res)
            deadline=time.monotonic()+180
            while time.monotonic()<deadline:
                with urllib.request.urlopen("http://127.0.0.1:8765/api/jobs/"+job["job_id"],timeout=5) as res:state=json.load(res)
                if state["state"]=="error":raise RuntimeError("model preload failed; inspect local diagnostic log")
                if state["state"]=="done":return {"version":value["product"],"model_ready":True}
                time.sleep(.5)
            raise TimeoutError("model preload")
        if not value["model_ready"]:raise RuntimeError("Preload models before entering the competition area")
        return {"version":value["product"],"model_ready":True}
    for name,fn in (("private assets",assets),("model lineage",models),("CUDA runtime",gpu),("WSL isolation",network),("local demonstration",service)):check(name,fn)
    result={"passed":all(c["passed"] for c in checks),"checks":checks,"scope":"workstation readiness; no network policy deployed"}
    folder=ROOT / "validation";folder.mkdir(exist_ok=True)
    (folder / "finals_preflight.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("READY" if result["passed"] else "CHECK_FAILED",flush=True)
    if not result["passed"]:raise SystemExit(1)


if __name__=="__main__":main()
