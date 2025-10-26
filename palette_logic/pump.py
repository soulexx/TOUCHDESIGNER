"""Serial palette index pump."""
import time
from typing import Dict

# TouchDesigner-compatible module loading
def _get_module(name):
    """Get palette_logic module using TouchDesigner's mod() function."""
    base = op('/project1')
    if not base:
        raise RuntimeError("Project base not found")
    return mod(f'/project1/palette_logic/{name}')

state = _get_module('state')
ORDER = state.ORDER

INDEX_TIMEOUT = 3.0
RETRY_LIMIT = 3
MIN_REQUEST_INTERVAL = 0.05  # 50ms = max 20 requests/second per palette type


def attach_base(base) -> None:
    state.attach_base(base)


def queue_counts(base, mapping: Dict[str, int]) -> None:
    state.attach_base(base)
    now = time.perf_counter()
    state.state.last_count_request = now
    print(f"[palette] DEBUG received counts: {mapping}")
    for palette_type, count in mapping.items():
        _apply_count(palette_type, int(count))
    for palette_type in mapping.keys():
        _send_next_index(palette_type)


def _apply_count(palette_type: str, count: int) -> None:
    count = max(0, count)
    st = state.state
    st.counts[palette_type] = count
    queue = st.queues[palette_type]
    queue.clear()
    # EOS uses 1-based palette numbers (1, 2, 3, ..., count)
    queue.extend(range(1, count + 1))
    st.active[palette_type] = None
    st.sent_at[palette_type] = 0.0
    st.attempts[palette_type] = 0
    state.ensure_table(palette_type, count)
    print(f"[palette] DEBUG {palette_type} queue initialized: {count} palettes (1-{count})")


def on_list_ack(base, palette_type: str, index: int) -> None:
    state.attach_base(base)
    st = state.state
    active = st.active[palette_type]
    if active != index:
        print(f"[palette] DEBUG {palette_type} ACK mismatch: expected {active}, got {index}")
        return
    queue = st.queues[palette_type]
    remaining = len(queue)
    if queue and queue[0] == index:
        queue.popleft()
    elif index in queue:
        queue.remove(index)
    st.active[palette_type] = None
    st.sent_at[palette_type] = 0.0
    st.attempts[palette_type] = 0
    print(f"[palette] DEBUG {palette_type} palette #{index} ACK (queue: {remaining-1} remaining)")
    _send_next_index(palette_type)


def tick(base) -> None:
    state.attach_base(base)
    st = state.state
    now = time.perf_counter()
    for palette_type in ORDER:
        active = st.active[palette_type]
        if active is None:
            if st.queues[palette_type]:
                _send_next_index(palette_type)
            continue
        if now - st.sent_at[palette_type] <= INDEX_TIMEOUT:
            continue
        osc = state.get_osc_out()
        if not osc:
            continue
        if st.attempts[palette_type] >= RETRY_LIMIT:
            queue = st.queues[palette_type]
            if queue and queue[0] == active:
                queue.popleft()
            st.active[palette_type] = None
            st.attempts[palette_type] = 0
            print(f"[palette] WARN giving up on {palette_type}:{active}")
            _send_next_index(palette_type)
        else:
            # Use correct EOS OSC API: /eos/get/{type}/{num}/list/{index}/{count}
            osc.sendOSC(f"/eos/get/{palette_type}/{active}/list/0/1", [])
            st.sent_at[palette_type] = now
            st.attempts[palette_type] += 1
            print(
                f"[palette] resend {palette_type}:{active} attempt {st.attempts[palette_type]}"
            )


def _send_next_index(palette_type: str) -> None:
    st = state.state
    if st.active[palette_type] is not None:
        return
    queue = st.queues[palette_type]
    if not queue:
        return

    # Rate limiting: enforce minimum interval between requests
    now = time.perf_counter()
    time_since_last = now - st.sent_at[palette_type]
    if time_since_last < MIN_REQUEST_INTERVAL:
        # Uncomment for verbose rate limiting debug:
        # print(f"[palette] DEBUG {palette_type} rate limited (wait {MIN_REQUEST_INTERVAL - time_since_last:.3f}s)")
        return  # Too soon, wait for next tick

    osc = state.get_osc_out()
    if not osc:
        return
    palette_num = queue[0]
    # Use correct EOS OSC API: /eos/get/{type}/{num}/list/{index}/{count}
    osc.sendOSC(f"/eos/get/{palette_type}/{palette_num}/list/0/1", [])
    st.active[palette_type] = palette_num
    st.sent_at[palette_type] = now
    st.attempts[palette_type] = 1
    print(f"[palette] send {palette_type} palette #{palette_num}")
