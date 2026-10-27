"""Run one approved event in a disposable Mininet namespace, with real TTL expiry."""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "sources/paper_code/sim"))
from active_defense_mininet_replay import build_network,reset_policy,apply_policy,inspect_policy,run_client,profile_for_label,SERVER_IP


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--scenario",required=True);parser.add_argument("--output",required=True)
    args=parser.parse_args();scenario=json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    if any(Path("/sys/class/net",name).exists() for name in ["s1","s2","s3"]):raise RuntimeError("existing_mininet_network_busy")
    endpoint=str(ROOT / "sources/paper_code/sim/mininet_traffic_endpoint.py")
    net=process=None
    try:
        net,subject,background,server,router,process=build_network(endpoint)
        def query(host,port=8080,payload="GET /demo HTTP/1.0",count=12):
            return run_client(host,endpoint,SERVER_IP,port,count,.12,payload)
        baseline=query(subject);base_bg=query(background)
        if baseline["success_rate"]!=1 or base_bg["success_rate"]!=1:raise RuntimeError("baseline_connectivity_failed")
        ttl=scenario["ttl_seconds"]
        if type(ttl) is not int or not 30<=ttl<=900:raise ValueError("invalid_ttl")
        commands=apply_policy(router,scenario);applied=time.monotonic();state=inspect_policy(router)
        port,payload=profile_for_label(scenario["true_label"])
        after=query(subject,port,payload);after_bg=query(background)
        if commands:
            while time.monotonic()-applied<ttl:time.sleep(min(.2,max(0,ttl-(time.monotonic()-applied))))
        reset_policy(router)
        rollback=time.monotonic();recovered=query(subject);recovered_bg=query(background);empty=not inspect_policy(router)["iptables"]
        result={"event_id":scenario["event_id"],"action":scenario["action"],"assessment":scenario["assessment"],
                "mode":"live_isolated_mininet_transaction_test","baseline":baseline,"background_baseline":base_bg,
                "subject_after":after,"background_after":after_bg,"recovery":recovered,"background_recovery":recovered_bg,
                "rollback_integrity":empty and recovered["success_rate"]==1 and recovered_bg["success_rate"]==1,
                "rule_readback":state,"rules_applied":sum(line.startswith("-A ") for line in state["iptables"].splitlines()),
                "commands_executed":len(commands),"ttl_seconds":ttl,
                "ttl_rollback_elapsed_seconds":rollback-applied if commands else None,
                "expiry_mode":"actual_monotonic_ttl_scheduler" if commands else "non_disruptive_no_rule",
                "scope":"synthetic TCP transactions in isolated namespaces; not original PCAP attack effectiveness"}
        Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:
        if net is not None:
            try:reset_policy(net.get("r1"))
            except Exception:pass
        if process is not None:
            process.terminate()
            try:process.wait(timeout=5)
            except Exception:process.kill()
        if net is not None:net.stop()


if __name__=="__main__":main()
