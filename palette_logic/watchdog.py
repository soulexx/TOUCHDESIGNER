"""Subscription / count watchdog."""
import time

# TouchDesigner-compatible module loading
def _get_module(name):
    """Get palette_logic module using TouchDesigner's mod() function."""
    base = op('/project1')
    if not base:
        raise RuntimeError("Project base not found")
    return mod(f'/project1/palette_logic/{name}')

state = _get_module('state')
ORDER = state.ORDER

SUBSCRIBE_BACKOFF = 5.0
COUNT_BACKOFF = 10.0


def ensure_subscribed(base) -> None:
    state.attach_base(base)
    st = state.state
    now = time.perf_counter()
    osc = state.get_osc_out()
    if not osc:
        print("[palette] DEBUG watchdog: OSC out not found")
        return
    time_since_activity = now - st.last_activity
    time_since_subscribe = now - st.last_subscribe
    if (time_since_activity) > SUBSCRIBE_BACKOFF and (
        time_since_subscribe
    ) > SUBSCRIBE_BACKOFF:
        print(f"[palette] DEBUG sending subscribe (last activity: {time_since_activity:.1f}s ago)")
        osc.sendOSC("/eos/subscribe", [1])
        st.last_subscribe = now
        st.subscribed = True
        print("[palette] subscribe sent")
    if (now - st.last_count_request) > COUNT_BACKOFF:
        print(f"[palette] DEBUG requesting counts (last request: {(now - st.last_count_request):.1f}s ago)")
        request_all_counts(base)


def request_all_counts(base) -> None:
    state.attach_base(base)
    st = state.state
    osc = state.get_osc_out()
    if not osc:
        print("[palette] WARN osc_out DAT missing; cannot request counts")
        return
    st.last_count_request = time.perf_counter()
    for palette_type in ORDER:
        osc.sendOSC(f"/eos/get/{palette_type}/count", [])
        print(f"[palette] count request {palette_type}")
