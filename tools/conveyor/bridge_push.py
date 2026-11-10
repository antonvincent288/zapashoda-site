#!/usr/bin/env python3
"""Conveyor helper: append a message to bridge/alisa_to_architect.json on main.

Usage: export GIT_TOKEN=...; python tools/conveyor/bridge_push.py --id Z-ID --topic "..." --body-file body.txt [--expect none]
"""
import re, json, sys, io, base64, tarfile, time, argparse, datetime, urllib.request, urllib.error

REPO = 'antonvincent288/zapashoda-site'
API = f'https://api.github.com/repos/{REPO}'

def req(url, method='GET', payload=None, token=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header('Authorization', 'Bearer ' + token)
    if data: r.add_header('Content-Type', 'application/json')
    r.add_header('User-Agent', 'conveyor-helper')
    try:
        return json.loads(urllib.request.urlopen(r, timeout=120).read())
    except urllib.error.HTTPError as e:
        print('HTTPERR', e.code, e.read()[:300].decode('utf-8', 'ignore'), file=sys.stderr); return None

def load_bridge(token):
    r = urllib.request.Request(f'https://codeload.github.com/{REPO}/tar.gz/refs/heads/main',
                               headers={'Authorization': f'Bearer {token}', 'User-Agent': 'conveyor-helper'})
    open('/tmp/bridge.tgz', 'wb').write(urllib.request.urlopen(r, timeout=240).read())
    with tarfile.open('/tmp/bridge.tgz') as t:
        for m in t.getmembers():
            if m.isfile() and m.name.endswith('bridge/alisa_to_architect.json'):
                return json.load(t.extractfile(m))
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--id', required=True)
    ap.add_argument('--topic', required=True)
    ap.add_argument('--body-file', required=True)
    ap.add_argument('--expect', default='none')
    a = ap.parse_args()
    import os
    token = os.environ.get('GIT_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token: print('ERROR: set GIT_TOKEN env', file=sys.stderr); sys.exit(2)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(timespec='seconds')
    msg = {'id': a.id, 'ts': now, 'from': 'alisa', 'topic': a.topic, 'expect': a.expect, 'answer_to': None, 'body': open(a.body_file, encoding='utf-8').read()}
    bridge = load_bridge(token)
    bridge.append(msg)
    head = req(f'{API}/git/ref/heads/main', token=token)
    head_sha = head['object']['sha']
    bc = req(f'{API}/git/commits/{head_sha}', token=token)
    b = req(f'{API}/git/blobs', 'POST', {'content': base64.b64encode(json.dumps(bridge, ensure_ascii=False).encode()).decode(), 'encoding': 'base64'}, token)
    tree = req(f'{API}/git/trees', 'POST', {'base_tree': bc['tree']['sha'], 'tree': [{'path': 'bridge/alisa_to_architect.json', 'mode': '100644', 'type': 'blob', 'sha': b['sha']}]}, token)
    c = req(f'{API}/git/commits', 'POST', {'message': f'bridge: alisa {a.id} — {a.topic} [skip ci]', 'tree': tree['sha'], 'parents': [head_sha]}, token)
    if c:
        u = req(f'{API}/git/refs/heads/main', 'PATCH', {'sha': c['sha'], 'force': False}, token)
        if u: print(f'BRIDGE_OK {c["sha"]}'); return
    print('BRIDGE_FAIL'); sys.exit(1)

if __name__ == '__main__':
    main()
