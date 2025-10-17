import time

ORDER = ['ip','fp','cp','bp']

def _now(): 
    return time.time()

DEFAULT = dict(
    last_seen=0.0,
    last_subscribe=0.0,
    pending={t:[] for t in ORDER},
    inflight=None,              # {'t':str,'idx':int,'sent':float,'retries':int}
    backoff_s=5.0,
    max_backoff_s=60.0,
)

def get(root):
    s = root.fetch('PAL_STATE', None)
    if s is None:
        s = dict(DEFAULT)
        s['pending'] = {t:[] for t in ORDER}
        root.store('PAL_STATE', s)
    return s

def set_last_seen(root): 
    get(root)['last_seen'] = _now()

def mark_subscribe(root):
    s = get(root)
    s['last_subscribe'] = _now()
    s['backoff_s'] = min(max(s['backoff_s']*1.5, 5.0), s['max_backoff_s'])

def reset_backoff(root):
    get(root)['backoff_s'] = 5.0
