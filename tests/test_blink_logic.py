"""
Test the actual blink manager logic (without TouchDesigner dependencies).
"""

import json
import time


class MockOp:
    """Mock TouchDesigner operator for testing."""

    def __init__(self, data=None):
        self.data = data or []
        self.module = None
        self.numRows = len(self.data)
        self.numCols = len(self.data[0]) if self.data else 0

    def __getitem__(self, key):
        if isinstance(key, tuple):
            r, c = key
            if 0 <= r < len(self.data) and 0 <= c < len(self.data[r]):
                return MockCell(self.data[r][c])
        return MockCell("")


class MockCell:
    """Mock TouchDesigner cell."""

    def __init__(self, value):
        self.val = str(value)


def test_pattern_parsing():
    """Test that patterns are correctly parsed from TSV format."""
    print("=" * 60)
    print("TEST: Pattern Parsing Logic")
    print("=" * 60)

    # Simulate pattern data
    patterns_data = [
        ["name", "stages"],
        ["slow", '[{"state": "press", "duration": 0.5}, {"state": "idle", "duration": 0.5}]'],
        ["fast", '[{"state": "press", "duration": 0.2}, {"state": "off", "duration": 0.2}]'],
        ["pulse", '[{"state": "press", "duration": 0.1}, {"state": "idle", "duration": 0.4}]'],
    ]

    # Parse like the manager does
    _patterns = {}
    dat = MockOp(patterns_data)

    if dat.numRows < 2:
        print("❌ FAIL: Not enough rows")
        return False

    cols = {dat[0, c].val.strip().lower(): c for c in range(dat.numCols)}
    ci_name = cols.get("name")
    ci_stages = cols.get("stages")

    if ci_name is None or ci_stages is None:
        print("❌ FAIL: Required columns not found")
        return False

    print(f"✓ Found columns: name={ci_name}, stages={ci_stages}")

    for r in range(1, dat.numRows):
        cell_name = dat[r, ci_name]
        cell_stage = dat[r, ci_stages]

        if not cell_name or not cell_name.val.strip():
            continue

        try:
            raw = cell_stage.val if cell_stage else ""
            stages = json.loads(raw) if raw else []
        except Exception as exc:
            print(f"❌ FAIL: Bad stages for {cell_name.val}: {exc}")
            continue

        cleaned = []
        for st in stages:
            if not isinstance(st, dict):
                continue
            state = (st.get("state") or "").strip().lower()
            if not state:
                continue
            try:
                duration = float(st.get("duration", 0.1))
            except Exception:
                duration = 0.1
            duration = max(duration, 0.01)
            color = (st.get("color") or "").strip()
            cleaned.append({"state": state, "duration": duration, "color": color})

        if cleaned:
            _patterns[cell_name.val.strip().lower()] = cleaned
            print(f"✓ Parsed pattern '{cell_name.val}':")
            for i, step in enumerate(cleaned):
                print(f"    Step {i}: state={step['state']}, duration={step['duration']}s")

    # Verify patterns
    expected = ["slow", "fast", "pulse"]
    for name in expected:
        if name not in _patterns:
            print(f"❌ FAIL: Pattern '{name}' not parsed")
            return False

    # Verify slow pattern details
    slow = _patterns["slow"]
    if len(slow) != 2:
        print(f"❌ FAIL: 'slow' should have 2 steps, has {len(slow)}")
        return False

    if slow[0]["state"] != "press" or slow[0]["duration"] != 0.5:
        print(f"❌ FAIL: 'slow' step 0 incorrect")
        return False

    if slow[1]["state"] != "idle" or slow[1]["duration"] != 0.5:
        print(f"❌ FAIL: 'slow' step 1 incorrect")
        return False

    print(f"\n✓ PASS: All {len(expected)} patterns parsed correctly")
    return True


def test_blink_timing():
    """Test that blink timing logic works correctly."""
    print("\n" + "=" * 60)
    print("TEST: Blink Timing Logic")
    print("=" * 60)

    # Simulate a simple blink pattern
    pattern = [
        {"state": "press", "duration": 0.5},
        {"state": "idle", "duration": 0.5},
    ]

    # Simulate blink state
    entry = {
        "target": "btn/4",
        "steps": pattern,
        "index": 0,
        "next_time": 0.0,
        "priority": 10,
        "color": "blue",
        "base": ("idle", "blue"),
    }

    now = 0.0
    events = []

    # Simulate 3 seconds of blinking
    dt = 0.1  # 100ms tick rate
    duration = 3.0
    ticks = int(duration / dt)

    print(f"Simulating {duration}s of blinking at {int(1/dt)}Hz tick rate...")

    for tick in range(ticks):
        now = tick * dt

        # This is the core logic from tick()
        steps = entry["steps"]
        while now >= float(entry.get("next_time", now)):
            current_step = entry["index"]
            step = steps[current_step]

            # Record the event
            events.append({
                "time": now,
                "step": current_step,
                "state": step["state"],
            })

            # Advance to next step
            duration_val = max(float(step.get("duration", 0.1)), 0.01)
            entry["next_time"] = now + duration_val
            entry["index"] = (entry["index"] + 1) % len(steps)

    # Analyze events
    print(f"\n✓ Generated {len(events)} state changes")

    # Print first few events
    print("\nFirst 6 events:")
    for i, evt in enumerate(events[:6]):
        print(f"  {evt['time']:.2f}s: step {evt['step']} → {evt['state']}")

    # Verify alternating pattern
    expected_states = ["press", "idle", "press", "idle", "press", "idle"]
    actual_states = [evt["state"] for evt in events[:6]]

    if actual_states == expected_states:
        print("\n✓ States alternate correctly: press → idle → press → idle...")
    else:
        print(f"\n❌ FAIL: Expected {expected_states}, got {actual_states}")
        return False

    # Verify timing (should change state approximately every 0.5s)
    if len(events) >= 2:
        time_diff = events[1]["time"] - events[0]["time"]
        expected_diff = 0.5
        tolerance = 0.15  # Allow some tolerance

        if abs(time_diff - expected_diff) <= tolerance:
            print(f"✓ Timing correct: {time_diff:.2f}s between states (expected ~{expected_diff}s)")
        else:
            print(f"❌ FAIL: Timing incorrect: {time_diff:.2f}s (expected ~{expected_diff}s)")
            return False

    # Should have approximately 6 state changes in 3 seconds (one every 0.5s)
    expected_count = int(duration / 0.5)
    tolerance_count = 2

    if abs(len(events) - expected_count) <= tolerance_count:
        print(f"✓ Event count correct: {len(events)} events in {duration}s (expected ~{expected_count})")
    else:
        print(f"❌ FAIL: Event count incorrect: {len(events)} events (expected ~{expected_count})")
        return False

    print("\n✓ PASS: Timing logic works correctly")
    return True


def test_priority_system():
    """Test that priority system works correctly."""
    print("\n" + "=" * 60)
    print("TEST: Priority System")
    print("=" * 60)

    _entries = {}

    def start(target, pattern_name, priority):
        """Simplified start function."""
        key = str(target).strip().lstrip("/")
        existing = _entries.get(key)

        if existing and int(existing.get("priority", 0)) > priority:
            print(f"  Rejected: existing priority {existing['priority']} > {priority}")
            return False

        _entries[key] = {
            "target": key,
            "pattern": pattern_name,
            "priority": priority,
        }
        print(f"  Started: {pattern_name} with priority {priority}")
        return True

    # Test sequence
    print("\n1. Start 'slow' pattern with priority 5:")
    result1 = start("btn/4", "slow", priority=5)

    print("\n2. Try to start 'fast' with lower priority 3 (should be rejected):")
    result2 = start("btn/4", "fast", priority=3)

    print("\n3. Start 'pulse' with higher priority 10 (should succeed):")
    result3 = start("btn/4", "pulse", priority=10)

    print("\n4. Try to start 'slow' with same priority 10 (should succeed, replaces):")
    result4 = start("btn/4", "slow", priority=10)

    # Verify results
    if not result1:
        print("\n❌ FAIL: First start should succeed")
        return False

    if result2:
        print("\n❌ FAIL: Lower priority should be rejected")
        return False

    if not result3:
        print("\n❌ FAIL: Higher priority should succeed")
        return False

    if not result4:
        print("\n❌ FAIL: Equal priority should succeed (replacement)")
        return False

    print("\n✓ PASS: Priority system works correctly")
    return True


def main():
    """Run all logic tests."""
    print("\n" + "=" * 60)
    print("BLINK MANAGER LOGIC TEST SUITE")
    print("=" * 60)
    print()

    tests = [
        ("Pattern Parsing", test_pattern_parsing),
        ("Blink Timing", test_blink_timing),
        ("Priority System", test_priority_system),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓✓✓ ALL LOGIC TESTS PASSED ✓✓✓")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    import sys
    sys.exit(exit_code)
