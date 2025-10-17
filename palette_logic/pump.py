from .state import get, _now

TIMEOUT_S = 2.0
MAX_RETRIES = 2
ORDER = ['ip','fp','cp','bp']

def send(path, *args):
    op('/project1/io/osc_out').sendOSC(path, args)

def queue_counts(root, counts:dict):
    s = get(root)
    for t, c in counts.items():
        if t in s['pending'] and not s['pending'][t]:
            s['pending'][t] = list(range(0, max(0, int(c))))  # 0-basiert
    if s['inflight'] is None:
        kick(root)

def kick(root):
    s = get(root)
    if s['inflight'] is not None:
        return
    for t in ORDER:
        q = s['pending'][t]
        if q:
            idx = q.pop(0)
            send(f'/eos/get/{t}/index/{idx}', [])
            s['inflight'] = dict(t=t, idx=idx, sent=_now(), retries=0)
            return

def on_list_ack(root, t:str, list_index:int):
    s = get(root)
    infl = s['inflight']
    if infl and infl['t'] == t and infl['idx'] == int(list_index):
        s['inflight'] = None
        kick(root)

def tick(root):
    s = get(root)
    infl = s['inflight']
    if not infl:
        return
    if _now() - infl['sent'] > TIMEOUT_S:
        if infl['retries'] < MAX_RETRIES:
            infl['retries'] += 1
            infl['sent'] = _now()
            send(f"/eos/get/{infl['t']}/index/{infl['idx']}", [])
        else:
            s['inflight'] = None
            kick(root)
