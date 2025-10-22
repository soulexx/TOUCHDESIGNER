"""Subscription / count watchdog."""
import time
from . import state
from .state import ORDER

SUBSCRIBE_BACKOFF = 5.0
COUNT_BACKOFF = 10.0


def ensure_subscribed(base) -> None:
    state.attach_base(base)
    st = state.state
    now = time.perf_counter()
    osc = state.get_osc_out()
    if not osc:
        return
    if (now - st.last_activity) > SUBSCRIBE_BACKOFF and (
        now - st.last_subscribe
    ) > SUBSCRIBE_BACKOFF:
        osc.sendOSC("/eos/subscribe", [1])
        st.last_subscribe = now
        st.subscribed = True
        print("[palette] subscribe sent")
    if (now - st.last_count_request) > COUNT_BACKOFF:
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
