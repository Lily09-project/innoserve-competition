"""Run one approved event in a disposable Mininet namespace, with real TTL expiry."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "sources/paper_code/sim"))
sys.path.insert(0,str(ROOT / "app"))
from network_contract import validate_network_scenario, bind_network_receipt, validate_measurement
from active_defense_mininet_replay import reset_policy,apply_policy,inspect_policy,run_client,profile_for_label,SERVER_IP,Mininet,LinuxBridge,TCLink,LinuxRouter
from network_safety import NetworkDeadline, NetworkLease, cleanup_owned


def build_owned_network(endpoint, owner):
    net = Mininet(controller=None, switch=LinuxBridge, link=TCLink, build=False)
    owner['net'] = net
    subject = net.addHost('subject', ip='10.10.1.10/24', defaultRoute='via 10.10.1.1')
    background = net.addHost('background', ip='10.10.2.10/24', defaultRoute='via 10.10.2.1')
    server = net.addHost('server', ip='10.10.3.10/24', defaultRoute='via 10.10.3.1')
    router = net.addHost('r1', cls=LinuxRouter, ip=None)
    for host, name, interface in ((subject,'s1','r1-eth0'),(background,'s2','r1-eth1'),(server,'s3','r1-eth2')):
        switch = net.addSwitch(name)
        net.addLink(host, switch)
        net.addLink(router, switch, intfName1=interface)
    net.build()
    net.start()
    for number in range(3):
        router.setIP(f'10.10.{number+1}.1/24', intf=f'r1-eth{number}')
    router.cmd('iptables -P FORWARD ACCEPT')
    owner['process'] = server.popen([sys.executable,endpoint,'server'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(.35)
    return subject, background, router


def measure(scenario, endpoint, subject, background, router, owner):
    def query(host,port=8080,payload="GET /demo HTTP/1.0",count=12):
        return run_client(host,endpoint,SERVER_IP,port,count,.12,payload)
    port,payload=profile_for_label(scenario["true_label"])
    baseline=query(subject,port,payload);base_bg=query(background)
    if baseline["success_rate"]!=1 or base_bg["success_rate"]!=1:raise RuntimeError("baseline_connectivity_failed")
    ttl=scenario["ttl_seconds"]
    if type(ttl) is not int or not 30<=ttl<=900:raise ValueError("invalid_ttl")
    owner['policy_started']=True
    commands=apply_policy(router,scenario);applied=time.monotonic();state=inspect_policy(router)
    owner['progress_path'].write_text(json.dumps({'phase':'policy_applied','commands':len(commands)}),encoding='utf-8')
    after=query(subject,port,payload);after_bg=query(background)
    if commands:
        while time.monotonic()-applied<ttl:time.sleep(min(.2,max(0,ttl-(time.monotonic()-applied))))
    reset_policy(router)
    rollback=time.monotonic();recovered=query(subject,port,payload);recovered_bg=query(background)
    rollback_state=inspect_policy(router);empty=not rollback_state["iptables"]
    result={"event_id":scenario["event_id"],"action":scenario["action"],"assessment":scenario["assessment"],
            "mode":"live_isolated_mininet_transaction_test","baseline":baseline,"background_baseline":base_bg,
            "subject_after":after,"background_after":after_bg,"recovery":recovered,"background_recovery":recovered_bg,
            "rollback_integrity":empty and recovered["success_rate"]==1 and recovered_bg["success_rate"]==1,
            "rule_readback":state,"rollback_rule_readback":rollback_state,
            "network_test_executed":True,"network_action_executed":bool(commands),
            "rules_applied":sum(line.startswith("-A ") for line in state["iptables"].splitlines()),
            "commands_executed":len(commands),"ttl_seconds":ttl,
            "ttl_rollback_elapsed_seconds":rollback-applied if commands else None,
            "expiry_mode":"actual_monotonic_ttl_scheduler" if commands else "non_disruptive_no_rule",
            "scope":"synthetic TCP transactions in isolated namespaces; not original PCAP attack effectiveness"}
    return result


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--scenario',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--deadline-seconds',type=int,default=100)
    args=parser.parse_args(argv)
    output=Path(args.output)
    cleanup_path=output.with_suffix('.cleanup.json')
    if any(path.exists() for path in (output,cleanup_path,output.with_suffix('.progress.json'))):
        raise FileExistsError('network_evidence_already_exists')
    scenario=json.loads(Path(args.scenario).read_text(encoding='utf-8'))
    validate_network_scenario(scenario)
    endpoint=str(ROOT/'sources/paper_code/sim/mininet_traffic_endpoint.py')
    owner={'progress_path':output.with_suffix('.progress.json')}
    failure=None
    with NetworkLease(), NetworkDeadline(args.deadline_seconds) as deadline:
        if any(Path('/sys/class/net',name).exists() for name in ('s1','s2','s3')):
            raise RuntimeError('existing_mininet_network_busy')
        try:
            subject,background,router=build_owned_network(endpoint,owner)
            result=measure(scenario,endpoint,subject,background,router,owner)
        except BaseException as exc:
            failure=type(exc).__name__
            raise
        finally:
            deadline.begin_cleanup()
            cleanup=cleanup_owned(owner,reset_policy,inspect_policy)
            cleanup_path.write_text(json.dumps({'failure_type':failure,**cleanup},indent=2),encoding='utf-8')
    if not cleanup['passed']:raise RuntimeError('isolated_network_cleanup_failed')
    result['cleanup']=cleanup
    validate_measurement(scenario,result)
    result=bind_network_receipt(scenario,result)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
