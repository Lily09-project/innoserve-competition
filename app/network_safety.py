"""POSIX deadlines and cleanup for this process's isolated Mininet resources."""
import signal
import subprocess
import time
from pathlib import Path


class NetworkDeadline:
    def __init__(self, seconds):
        if type(seconds) is not int or not 1 <= seconds <= 900:
            raise ValueError('invalid_network_deadline')
        self.seconds = seconds
        self.previous = {}

    def interrupt(self, signum, frame):
        self.begin_cleanup()
        raise TimeoutError('isolated_network_deadline') if signum == signal.SIGALRM else InterruptedError('isolated_network_interrupted')

    def begin_cleanup(self):
        signal.alarm(0)
        for kind in self.previous:
            signal.signal(kind, signal.SIG_IGN)

    def __enter__(self):
        for kind in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
            self.previous[kind] = signal.signal(kind, self.interrupt)
        signal.alarm(self.seconds)
        return self

    def __exit__(self, *args):
        signal.alarm(0)
        for kind, previous in self.previous.items():
            signal.signal(kind, previous)


class NetworkLease:
    """A process lock, never a global mn -c or deletion of another network."""
    def __init__(self, path='/tmp/innoserve-mininet.lock'):
        self.path = path

    def __enter__(self):
        import fcntl
        self.stream = open(self.path, 'a')
        try:
            fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.stream.close()
            raise RuntimeError('isolated_network_busy') from None
        return self

    def __exit__(self, *args):
        self.stream.close()


def cleanup_owned(owner, reset_policy, inspect_policy, link_exists=None):
    link_exists = link_exists or (lambda name: Path('/sys/class/net', name).exists())
    net, process = owner.get('net'), owner.get('process')
    report = {'policy_reset': net is None, 'server_stopped': process is None,
              'network_stopped': net is None, 'policy_started': bool(owner.get('policy_started')),
              'commands_drained':True,'remaining_owned_links': [], 'errors': []}
    if net is not None:
        nodes=[]
        for group in ('hosts','switches','controllers'):
            collection=getattr(net,group,[])
            if isinstance(collection,(list,tuple)):nodes.extend(collection)
        for node in nodes:
            if getattr(node,'waiting',False) is not True:continue
            try:
                node.sendInt()
                until=time.monotonic()+3
                while node.waiting and time.monotonic()<until:
                    node.monitor(timeoutms=100,findPid=False)
                if node.waiting:raise TimeoutError('owned_command_did_not_finish')
            except Exception as exc:
                report['commands_drained']=False
                report['errors'].append('command_drain:'+type(exc).__name__)
    if net is not None:
        try:
            router = net.get('r1')
            reset_policy(router)
            report['policy_reset'] = not inspect_policy(router)['iptables'].strip()
        except Exception as exc:
            if not owner.get('policy_started'):
                report['policy_reset'] = True
            else:
                report['errors'].append('policy_reset:'+type(exc).__name__)
    if process is not None:
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            report['server_stopped'] = process.poll() is not None
        except Exception as exc:
            report['errors'].append('server_stop:'+type(exc).__name__)
    if net is not None:
        try:
            net.stop()
            report['network_stopped'] = True
        except Exception as exc:
            report['errors'].append('network_stop:'+type(exc).__name__)
        report['remaining_owned_links'] = [name for name in ('s1', 's2', 's3') if link_exists(name)]
    report['passed'] = all(report[key] for key in ('commands_drained','policy_reset','server_stopped','network_stopped')) and not report['remaining_owned_links'] and not report['errors']
    return report
