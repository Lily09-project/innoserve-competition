"""Measure source-scoped rules on a four-subnet isolated Mininet topology."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from live_network_test import (
    ROOT, LinuxBridge, LinuxRouter, Mininet, NetworkDeadline, NetworkLease, SERVER_IP,
    TCLink, apply_policy, cleanup_owned, inspect_policy, profile_for_label, reset_policy,
    run_client,
)

NODES = (("subject", 1), ("background", 2), ("server", 3), ("bg_extra", 4))
ATTEMPTS = 12
TTL = 30


def measure(owner):
    endpoint = str(ROOT / "sources/paper_code/sim/mininet_traffic_endpoint.py")
    net = Mininet(controller=None, switch=LinuxBridge, link=TCLink, build=False)
    owner["net"] = net
    router = net.addHost("r1", cls=LinuxRouter, ip=None)
    hosts = {}
    for name, subnet in NODES:
        hosts[name] = net.addHost(name, ip=f"10.10.{subnet}.10/24",
                                  defaultRoute=f"via 10.10.{subnet}.1")
        switch = net.addSwitch(f"s{subnet}")
        net.addLink(hosts[name], switch)
        net.addLink(router, switch, intfName1=f"r1-eth{subnet - 1}")
    net.build()
    net.start()
    for _, subnet in NODES:
        router.setIP(f"10.10.{subnet}.1/24", intf=f"r1-eth{subnet - 1}")
    router.cmd("iptables -P FORWARD ACCEPT")
    owner["process"] = hosts["server"].popen(
        [sys.executable, endpoint, "server"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(.35)
    label = "DDoS-LOIC-HTTP"
    port, payload = profile_for_label(label)

    def sample():
        rows = {}
        for name in ("subject", "background", "bg_extra"):
            row = run_client(hosts[name], endpoint, SERVER_IP, port, ATTEMPTS, .12, payload)
            rows[name] = {key: row[key] for key in ("attempts", "successes")}
        return rows

    baseline = sample()
    owner["policy_started"] = True
    scenario = {"action": "upstream_scrubbing", "reason_label": label, "assessment": "support"}
    apply_policy(router, scenario)
    applied = time.monotonic()
    rules = sum(line.startswith("-A ") for line in inspect_policy(router)["iptables"].splitlines())
    during = sample()
    time.sleep(max(0, TTL - (time.monotonic() - applied)))
    reset_policy(router)
    elapsed = time.monotonic() - applied
    recovery = sample()
    remaining_rules = bool(inspect_policy(router)["iptables"].strip())
    stages = {"baseline": baseline, "during": during, "recovery": recovery}
    if (rules != 2 or remaining_rules or elapsed < TTL
            or any(row["attempts"] != ATTEMPTS for stage in stages.values() for row in stage.values())
            or any(row["successes"] != ATTEMPTS for phase, stage in stages.items()
                   for name, row in stage.items() if (phase, name) != ("during", "subject"))
            or during["subject"]["successes"] >= ATTEMPTS):
        raise RuntimeError("expanded_topology_acceptance_failed")
    return {"scope": "one isolated policy replay with generated TCP transactions; no attack PCAP or capacity claim",
            "scenario": label, "action": scenario["action"], "subnets": len(NODES),
            "hosts": len(NODES), "switches": len(NODES), "routers": 1, "stages": stages,
            "transactions": sum(row["attempts"] for stage in stages.values() for row in stage.values()),
            "ttl_seconds": TTL, "rollback_elapsed_seconds": round(elapsed, 3),
            "rules_read_back": rules, "remaining_rules": remaining_rules}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    owner = {}
    links = tuple(Path("/sys/class/net", f"s{i}") for i in range(1, len(NODES) + 1))
    with NetworkLease(), NetworkDeadline(100) as deadline:
        if any(path.exists() for path in links):
            raise RuntimeError("existing_mininet_network_busy")
        try:
            result = measure(owner)
        finally:
            deadline.begin_cleanup()
            cleanup = cleanup_owned(owner, reset_policy, inspect_policy)
            if not cleanup["passed"] or any(path.exists() for path in links):
                raise RuntimeError("expanded_topology_cleanup_failed")
    result["cleanup_passed"] = True
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
