# Fix EOS Palette Subscribe: Complete Implementation

## Summary
Fixes critical bugs preventing EOS palette subscription from working, adds comprehensive debug logging, and resolves all TouchDesigner compatibility issues.

## Problems Fixed

### 🔴 Critical Bugs
1. **Wrong OSC API endpoints** - Used non-existent `/eos/get/{type}/index/{idx}` instead of correct `/eos/get/{type}/{num}/list/0/1`
2. **0-based indexing** - Used 0-based arrays instead of EOS's 1-based palette numbering
3. **Import errors** - Python relative imports failed in TouchDesigner DAT context
4. **TouchDesigner API errors** - Used `absTime.rate` (doesn't exist), `td.op()` (wrong context)
5. **OSC callback signature** - Function signature incompatible with TouchDesigner's call convention
6. **No rate limiting** - Caused performance issues when syncing many palettes

## Changes

### OSC API Fixes
**Before (Broken):**
```python
/eos/get/ip/index/5  # Does not exist in EOS!
```

**After (Fixed):**
```python
/eos/get/ip/5/list/0/1  # Correct EOS OSC API
```

### Palette Numbering
**Before:** `range(count)` → palettes 0, 1, 2, ...
**After:** `range(1, count + 1)` → palettes 1, 2, 3, ... (EOS standard)

### Import System
**Before:**
```python
from . import state  # Fails in TouchDesigner
```

**After:**
```python
state = mod('/project1/palette_logic/state')  # TouchDesigner pattern
```

### Rate Limiting
- Added `MIN_REQUEST_INTERVAL = 50ms` (max 20 requests/sec per type)
- Prevents OSC spam that caused TD slowdowns
- Progressive sync keeps TD responsive

### Debug Logging
Comprehensive debug output throughout:
```
[palette] DEBUG sending subscribe (last activity: 5.2s ago)
[palette] subscribe sent
[palette] DEBUG received count: ip=42 | OSC: /eos/out/get/ip/count [42.0]
[palette] DEBUG ip queue initialized: 42 palettes (1-42)
[palette] send ip palette #1
[palette] DEBUG received list: ip #1 idx=0 uid='...' label='...'
[palette] DEBUG ip palette #1 ACK (queue: 41 remaining)
```

## Files Changed

### Core Fixes
- `palette_logic/pump.py` - OSC API, rate limiting, 1-based indexing, debug logs
- `palette_logic/eos_notify_handler.py` - table row calculations, td.op() fix, debug logs
- `palette_logic/subscribe_manager.py` - both async and blocking sync fixed
- `palette_logic/watchdog.py` - import fixes, debug logs
- `palette_logic/state.py` - import compatibility

### Integration Fixes
- `io/tick_exec.py` - project.cookRate instead of absTime.rate
- `io/oscin1_callbacks.py` - removed importlib, fixed function signature
- `io/osc_in_callbacks.py` - palette event handler integration

### Documentation
- `PALETTE_SYNC_TEST.md` - Complete testing guide with Textport commands
- Debug logging added throughout for easy troubleshooting

## Testing

### Test Commands (Textport)
```python
# Activate sync
op('/project1').store('PALETTE_SYNC_ENABLED', True)

# Trigger subscribe
watchdog = op('/project1/palette_logic/watchdog').module
watchdog.ensure_subscribed(op('/project1'))

# Check state (after 5-10 seconds)
state_mod = op('/project1/palette_logic/state').module
st = state_mod.state
print(f"Counts: {st.counts}")

# Check tables
table = op('/project1/palette_logic/pal_ip')
print(f"Intensity Palettes: {table.numRows} rows")
```

### Expected Behavior
- ✅ Subscribe command sent to EOS
- ✅ Count requests for all palette types (ip, fp, cp, bp)
- ✅ EOS responds with palette counts
- ✅ Palette requests sent with rate limiting (20/sec)
- ✅ Palette tables populate with data
- ✅ TouchDesigner remains responsive

### Debug Output Helps Identify
- OSC connection issues
- EOS response problems
- Queue status and progress
- Request/response mismatches
- Rate limiting behavior

## Impact

### Before (Broken)
- ❌ Subscribe never worked (wrong OSC paths)
- ❌ TD became very slow when enabled
- ❌ Palette numbers mismatched
- ❌ No way to debug issues
- ❌ Import errors prevented execution

### After (Fixed)
- ✅ Subscribe uses correct EOS OSC API
- ✅ Performance improved (rate limited)
- ✅ Palette tables correctly indexed
- ✅ Handles palette number gaps (1, 3, 7, 42...)
- ✅ Comprehensive debug logging
- ✅ All TouchDesigner compatibility issues resolved

## Commits Included

1. Fix EOS palette subscribe: Use correct OSC API and add rate limiting
2. Add comprehensive debug logging for palette sync troubleshooting
3. Add comprehensive Textport test guide for palette sync
4. Fix TouchDesigner import errors: Replace relative imports with mod()
5. Fix TouchDesigner API error: Use project.cookRate instead of absTime.rate
6. Fix OSC callback import: Remove importlib, inline implementation
7. Merge branch 'main' (resolved conflicts)
8. Fix onReceiveOSC signature: Accept variable arguments
9. Fix NameError in eos_notify_handler: Use op() instead of td.op()

## Notes

- Tested with EOS via OSC on standard ports (3032/3033)
- Rate limiting configurable via `MIN_REQUEST_INTERVAL` in `pump.py`
- Supports up to 1000 palettes per type (configurable limit)
- Works with non-sequential palette numbers
- Verbose rate-limit logging available (commented out by default)

## Related Issues

Addresses: "subscribe hat noch nie funktioniert und TD wurde sehr langsam"

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
