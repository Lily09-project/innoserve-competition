"""Private isolated SSH protocol endpoint; no host users or external targets."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import logging
from pathlib import Path
import socket
import threading
import time

import paramiko

logging.getLogger('paramiko').setLevel(logging.CRITICAL)


def serve(folder):
    cfg = json.loads((folder / 'credentials.json').read_text())
    key = paramiko.RSAKey.from_private_key_file(str(folder / 'host.key'))
    lock = threading.Lock()

    class Auth(paramiko.ServerInterface):
        def check_auth_password(self, username, password):
            ok = username == cfg['username'] and password == cfg['password']
            with lock:
                with (folder / 'auth.jsonl').open('a') as stream:
                    stream.write(json.dumps({'accepted': ok, 'time': time.time()}) + '\n')
            return paramiko.AUTH_SUCCESSFUL if ok else paramiko.AUTH_FAILED

        def get_allowed_auths(self, username):
            return 'password'

        def check_channel_request(self, kind, chanid):
            return paramiko.OPEN_SUCCEEDED if kind == 'session' else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def handle(conn):
        transport = paramiko.Transport(conn)
        try:
            transport.add_server_key(key)
            transport.start_server(server=Auth())
            channel = transport.accept(4)
            if channel is not None:
                channel.sendall(b'isolated-service-healthy\n')
                channel.shutdown_write()
        except (OSError, EOFError, paramiko.SSHException):
            pass
        finally:
            transport.close()

    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(('10.10.3.10', 22))
    listener.listen(64)
    with ThreadPoolExecutor(max_workers=32) as pool:
        while True:
            conn, _ = listener.accept()
            pool.submit(handle, conn)


def wave(folder, kind, count):
    cfg = json.loads((folder / 'credentials.json').read_text())
    public = paramiko.RSAKey.from_private_key_file(str(folder / 'host.key'))
    gate = threading.Barrier(count)

    def attempt(_):
        client = paramiko.SSHClient()
        client.get_host_keys().add('10.10.3.10', public.get_name(), public)
        gate.wait()
        try:
            client.connect('10.10.3.10', port=22, username=cfg['username'],
                           password=cfg['password'] if kind == 'valid' else 'invalid-lab-only-password',
                           timeout=1.8, banner_timeout=1.8, auth_timeout=1.8,
                           allow_agent=False, look_for_keys=False)
            channel = client.get_transport().open_session(timeout=1.8)
            received = channel.recv(256)
            return {'authenticated': True, 'healthy': received == b'isolated-service-healthy\n', 'rejected': False}
        except paramiko.AuthenticationException:
            return {'authenticated': False, 'healthy': False, 'rejected': True}
        except (OSError, EOFError, paramiko.SSHException):
            return {'authenticated': False, 'healthy': False, 'rejected': False}
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=count) as pool:
        records = list(pool.map(attempt, range(count)))
    return {'attempts': count, **{key: sum(row[key] for row in records) for key in records[0]}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['server', 'wave'])
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--kind', choices=['valid', 'invalid'], default='valid')
    parser.add_argument('--count', type=int, default=8)
    args = parser.parse_args()
    if args.mode == 'server':
        serve(args.folder)
    else:
        if not 1 <= args.count <= 16:
            parser.error('isolated wave count must be 1..16')
        print(json.dumps(wave(args.folder, args.kind, args.count)), flush=True)
