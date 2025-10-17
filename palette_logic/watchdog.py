from .state import get, mark_subscribe, reset_backoff, _now

def send(path, *args):
    op('/project1/io/osc_out').sendOSC(path, args)

def request_all_counts():
    for t in ['ip','fp','cp','bp']:
        send(f'/eos/get/{t}/count')

def ensure_subscribed(root):
    s = get(root)
    age = _now() - s['last_seen']
    since = _now() - s['last_subscribe']

    # Wenn in den letzten 5s Leben da war: nix tun, Backoff resetten
    if age < 5.0:
        reset_backoff(root)
        return

    # Throttle: nur alle backoff_s resubscriben
    if since < s['backoff_s']:
        return

    send('/eos/subscribe', 1)
    request_all_counts()
    mark_subscribe(root)
