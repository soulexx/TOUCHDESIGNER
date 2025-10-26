"""
Test script for LED Blink Manager
Tests basic functionality without requiring TouchDesigner operators.
"""

import sys
import time
from pathlib import Path

# Add src to path
BASE_PATH = Path(__file__).resolve().parent.parent
SRC_PATH = BASE_PATH / "io"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def test_pattern_loading():
    """Test if pattern definitions can be loaded from TSV."""
    print("=" * 60)
    print("TEST 1: Pattern Loading")
    print("=" * 60)

    patterns_file = BASE_PATH / "io" / "led_blink_patterns.tsv"
    if not patterns_file.exists():
        print(f"❌ FAIL: Pattern file not found: {patterns_file}")
        return False

    with open(patterns_file, 'r') as f:
        lines = f.readlines()

    if len(lines) < 2:
        print("❌ FAIL: Pattern file has no data rows")
        return False

    # Check header
    header = lines[0].strip().split('\t')
    if 'name' not in header or 'stages' not in header:
        print(f"❌ FAIL: Invalid header. Expected 'name' and 'stages', got: {header}")
        return False

    print(f"✓ Header OK: {header}")

    # Check patterns
    patterns = []
    for i, line in enumerate(lines[1:], 1):
        parts = line.strip().split('\t')
        if len(parts) >= 2:
            name = parts[0]
            stages = parts[1]
            patterns.append(name)
            print(f"  Pattern {i}: {name}")
            print(f"    Stages: {stages[:80]}{'...' if len(stages) > 80 else ''}")

    expected_patterns = ['slow', 'fast', 'pulse']
    for pattern in expected_patterns:
        if pattern in patterns:
            print(f"✓ Pattern '{pattern}' found")
        else:
            print(f"❌ FAIL: Pattern '{pattern}' not found")
            return False

    print(f"\n✓ PASS: All {len(expected_patterns)} expected patterns found")
    return True


def test_manager_module_structure():
    """Test if manager module has required functions."""
    print("\n" + "=" * 60)
    print("TEST 2: Manager Module Structure")
    print("=" * 60)

    manager_file = BASE_PATH / "io" / "led_blink_manager.py"
    if not manager_file.exists():
        print(f"❌ FAIL: Manager file not found: {manager_file}")
        return False

    with open(manager_file, 'r') as f:
        content = f.read()

    required_functions = [
        'def tick(',
        'def start(',
        'def stop(',
        'def update_base(',
        'def is_active(',
        'def reload_patterns(',
    ]

    for func in required_functions:
        if func in content:
            print(f"✓ Function {func.split('(')[0]} found")
        else:
            print(f"❌ FAIL: Function {func.split('(')[0]} not found")
            return False

    print("\n✓ PASS: All required functions found")
    return True


def test_exec_module_structure():
    """Test if exec module is properly structured."""
    print("\n" + "=" * 60)
    print("TEST 3: Exec Module Structure")
    print("=" * 60)

    exec_file = BASE_PATH / "io" / "led_blink_exec.py"
    if not exec_file.exists():
        print(f"❌ FAIL: Exec file not found: {exec_file}")
        return False

    with open(exec_file, 'r') as f:
        content = f.read()

    # Check for required callbacks
    required_callbacks = [
        'def onFrameStart(',
        'def onStart(',
    ]

    for callback in required_callbacks:
        if callback in content:
            print(f"✓ Callback {callback.split('(')[0]} found")
        else:
            print(f"❌ FAIL: Callback {callback.split('(')[0]} not found")
            return False

    # Check for manager reference
    if '_MANAGER = op("/project1/io/led_blink_manager")' in content:
        print("✓ Manager reference found")
    else:
        print("❌ FAIL: Manager reference not found or incorrect")
        return False

    # Check if tick is called
    if 'mod.tick(' in content:
        print("✓ tick() call found")
    else:
        print("❌ FAIL: tick() call not found")
        return False

    print("\n✓ PASS: Exec module properly structured")
    return True


def test_menu_integration():
    """Test if menu_engine properly integrates with blink manager."""
    print("\n" + "=" * 60)
    print("TEST 4: Menu Engine Integration")
    print("=" * 60)

    menu_file = BASE_PATH / "menus" / "menu_engine.py"
    if not menu_file.exists():
        print(f"❌ FAIL: Menu engine file not found: {menu_file}")
        return False

    with open(menu_file, 'r') as f:
        content = f.read()

    # Check for BLINK reference
    if "BLINK  = op('/project1/io/led_blink_manager')" in content:
        print("✓ BLINK operator reference found")
    else:
        print("❌ FAIL: BLINK operator reference not found or incorrect")
        return False

    # Check for blink manager usage
    checks = [
        ('mod.update_base(', 'update_base() call'),
        ('mod.start(', 'start() call'),
        ('mod.stop(', 'stop() call'),
        ('_update_submenu_led_feedback', 'submenu LED feedback function'),
    ]

    for check_str, desc in checks:
        if check_str in content:
            print(f"✓ {desc} found")
        else:
            print(f"❌ FAIL: {desc} not found")
            return False

    # Check submenu config has blink patterns
    if '"blink":' in content:
        print("✓ Submenu blink configuration found")
    else:
        print("⚠ WARNING: No blink configuration in submenu")

    print("\n✓ PASS: Menu integration properly structured")
    return True


def test_driver_integration():
    """Test if driver_led is properly integrated."""
    print("\n" + "=" * 60)
    print("TEST 5: Driver LED Integration")
    print("=" * 60)

    driver_file = BASE_PATH / "io" / "driver_led.py"
    if not driver_file.exists():
        print(f"❌ FAIL: Driver file not found: {driver_file}")
        return False

    with open(driver_file, 'r') as f:
        content = f.read()

    # Check for send_led function
    if 'def send_led(' in content:
        print("✓ send_led() function found")
    else:
        print("❌ FAIL: send_led() function not found")
        return False

    # Check parameters
    if 'target, state, color, do_send' in content:
        print("✓ send_led() has correct parameters")
    else:
        print("⚠ WARNING: send_led() parameters may be incorrect")

    # Check operator references
    refs = [
        ('LED_CONST = op("/project1/io/led_const")', 'LED_CONST'),
        ('API = op("/project1/io/midicraft_enc_api")', 'API'),
        ('PALETTE = op("/project1/io/midicraft_enc_led_palette")', 'PALETTE'),
    ]

    for ref, name in refs:
        if ref in content:
            print(f"✓ {name} operator reference found")
        else:
            print(f"❌ FAIL: {name} operator reference not found or incorrect")
            return False

    print("\n✓ PASS: Driver properly structured")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BLINK MANAGER TEST SUITE")
    print("=" * 60)
    print(f"Base Path: {BASE_PATH}")
    print()

    tests = [
        ("Pattern Loading", test_pattern_loading),
        ("Manager Structure", test_manager_module_structure),
        ("Exec Structure", test_exec_module_structure),
        ("Menu Integration", test_menu_integration),
        ("Driver Integration", test_driver_integration),
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
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
