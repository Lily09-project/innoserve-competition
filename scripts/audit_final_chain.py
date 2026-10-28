"""Exercise real local APIs, all 17 inputs and multiple isolated network paths.

Requires the local server and private assets. Produces private QA evidence only.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from network_contract import build_network_scenario, verify_network_receipt, valid_ledger
from pipeline import LABELS
from server import source_revision


def scan_delivery_anonymity(root=ROOT):
    """Scan delivered text, not the retired website or the public repository UI."""
    targets = {}
    for artifact in ('決賽簡報_AI資安框架.pptx', '決賽海報_AI資安框架_A2.pptx'):
        with zipfile.ZipFile(root / 'deliverables' / artifact) as archive:
            for name in archive.namelist():
                if name.endswith(('.xml', '.rels')):
                    targets[artifact+'::'+name] = ' '.join(ET.fromstring(archive.read(name)).itertext())+' '+archive.read(name).decode('utf-8')
    for name in ("deliverables/source/architecture.svg", "media/film/scene.mjs"):
        targets[name] = (root / name).read_text(encoding="utf-8")
    forbidden = ("Lily09", "Da-Xiong-Chen", "github.com", "陳信安", "蘇櫟", "指導教授", "學校名稱", "C:\\Users\\")
    findings = [{"path": name, "identity_matches": [s for s in forbidden if s in text]} for name, text in targets.items()]
    if any(row["identity_matches"] for row in findings):
        raise ValueError("Identifying text in competition deliverables")
    return findings


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8765)
    args=parser.parse_args()
    base=f"http://127.0.0.1:{args.port}"
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder=ROOT / "validation" / ("framework_audit_"+stamp)
    folder.mkdir(parents=True)

    def save(name,value):
        (folder / name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
    def request(path,payload=None):
        req=urllib.request.Request(base+path,data=None if payload is None else json.dumps(payload).encode(),
            headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=10) as response:return json.load(response)
    def operation(action,event_id=None,execution_id=None):
        job=request("/api/operate",{"action":action,"event_id":event_id,"execution_id":execution_id})
        start=time.monotonic()
        while time.monotonic()-start<300:
            value=request("/api/jobs/"+job["job_id"])
            if value["state"]=="error":raise RuntimeError(value)
            if value["state"]=="done":return value["result"]
            time.sleep(.5)
        raise TimeoutError(action)

    status=request("/api/status")
    assert status["product"]=="ai-security-demo.v3"
    assert status.get('source_revision') == source_revision(), 'Running service differs from current checkout'
    print("WARMUP",flush=True)
    operation("warmup")
    source={e["event_id"]:e for e in json.loads((ROOT / "evidence/fresh17/events.json").read_text(encoding="utf-8"))}
    live=[]
    for event_id in status["live_event_ids"]:
        value=operation("live",event_id)
        assert value["execution_mode"]=="live_local_models"
        assert value["result"]["prediction"]==value["prediction"]==source[event_id]["prediction"]
        assert value["result"]["judge"]["mode"]=="live_local_llm_inference"
        assert value['result']['judge']['valid_json'] is True
        assert value["result"]["ledger"][2]["mode"]=="live_local_llm_inference"
        assert valid_ledger(value["result"]["ledger"])
        assert len(value["evidence"])==5
        live.append(value)
        save("live_events_private.json",live)
        print("LIVE",LABELS[value["validation_label"]],value["result"]["judge"]["assessment"],value["result"]["policy"]["action"],flush=True)
    assert sorted(e["validation_label"] for e in live)==list(range(17))
    network=[]
    # Predetermined classes, not selected after observing their outcomes.
    for label in (0,1,2,7,11,13):
        event=next(e for e in live if e["validation_label"]==label)
        scenario=build_network_scenario(event)
        value=operation("network",event["event_id"],event["execution_id"])
        assert verify_network_receipt(scenario,value)
        assert value["baseline"]["success_rate"]==1
        assert value["background_after"]["success_rate"]==1
        assert value["rollback_integrity"] is True
        if value["rules_applied"]:
            assert value["ttl_rollback_elapsed_seconds"]>=value["ttl_seconds"]
        network.append(value)
        save("network_receipts_private.json",network)
        print("NETWORK",LABELS[label],"rules",value["rules_applied"],"subject",value["subject_after"]["success_rate"],"rollback",value["rollback_integrity"],flush=True)
    try:
        request("/api/operate",{"action":"network","event_id":live[0]["event_id"],"execution_id":"stale-run"})
        raise AssertionError("stale execution accepted")
    except urllib.error.HTTPError as error:assert error.code==400
    anonymous=scan_delivery_anonymity()
    save("anonymous_display_scan.json",anonymous)
    summary={"status":"passed", "started_utc":stamp,"api_version":status["product"],"source_revision":status['source_revision'],
        "real_live_classes":17,"real_local_llm_calls":17,"network_cases":len(network),
        "network_validation_labels":[LABELS[c] for c in (0,1,2,7,11,13)],
        "network_receipts_bound_to_same_execution":True,"stale_execution_rejected":True,
        "background_preserved_cases":sum(v["background_after"]["success_rate"]==1 for v in network),
        "rollback_passed_cases":sum(v["rollback_integrity"] for v in network),
        "non_disruptive_network_cases":sum(v["rules_applied"]==0 for v in network),
        "anonymous_served_assets_scan":"passed for explicit known identity strings; human review still required",
        "scope":"real pretrained models on prepared tensors; synthetic TCP namespaces; no native exploit or live capture proof"}
    save("summary.json",summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    print(str(folder),flush=True)


if __name__=="__main__":main()
