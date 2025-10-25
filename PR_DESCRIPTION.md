# Code improvements: Fix EOS subscribe, improve portability, add auto-sync

## 📋 Summary

This PR contains **3 commits** with critical bug fixes and code quality improvements for the TOUCHDESIGNER MIDICRAFT to EOS system.

---

## 🐛 **1. Fix EOS Palette Subscribe Failure** (Commit `9567d31`)

**Problem:**
- EOS palette synchronization was completely broken
- OSC operator path mismatch prevented `/eos/subscribe` command from being sent
- `get_osc_out()` was looking for `"io/osc_out"` but operator is named `"io/oscout1"`

**Root Cause:**
```python
# palette_logic/state.py (BEFORE)
def get_osc_out():
    return base.op("io/osc_out")  # ❌ Operator doesn't exist!

# watchdog.py
def ensure_subscribed(base):
    osc = state.get_osc_out()  # ← Always returned None
    if not osc:
        return  # ← Early exit - subscribe NEVER sent!
```

**Fix:**
- Changed `"io/osc_out"` → `"io/oscout1"` in 3 files:
  - `palette_logic/state.py`
  - `src/tools/td_fix_palettes.py`
  - `temp_fix.py`

**Impact:**
- ✅ `/eos/subscribe` OSC message now sent correctly
- ✅ EOS palette synchronization works
- ✅ `request_all_counts()` now functional

**Files Changed:** 3 files, 7 insertions(+), 7 deletions(-)

---

## 🌍 **2. Code Quality Improvements** (Commit `03a9cf7`)

Three independent improvements that enhance code quality without breaking functionality:

### **2a. Fix Missing Math Import (CRITICAL BUG)**

**Problem:**
```python
# menus/event_filters.py line 89
magnitude = ENC_COARSE_STEP_MIN + math.log10(...)  # ❌ NameError!
```
- `math` module used but never imported
- Would crash when encoder enters 'coarse' mode (fast movements)

**Fix:**
```python
import math  # ✅ Added to imports
import time
from collections import defaultdict
```

**Impact:**
- ✅ Encoder coarse mode now stable
- ✅ No crash on fast encoder movements

---

### **2b. Remove Hardcoded Windows Paths (PORTABILITY)**

**Problem:**
```python
# BEFORE (Windows-only, hardcoded)
BASE_PATH = Path(r"c:\_DEV\TOUCHDESIGNER")
```

**Fix:**
```python
# AFTER (Portable: environment variable OR relative path)
BASE_PATH = Path(os.getenv('TOUCHDESIGNER_ROOT',
                           Path(__file__).resolve().parent.parent))
```

**Files Fixed (9):**
- `io/_midi_dispatcher.py`
- `io/bus_dispatch.py`
- `io/command_runner_callbacks.py`
- `io/driver_led.py`
- `io/midiin1_callbacks.py`
- `io/midiin2_callbacks.py`
- `io/osc_in_callbacks.py`
- `io/oscin1_callbacks.py`
- `io/textport_exec.py`

**Impact:**
- ✅ Project now works on **Linux/Mac**
- ✅ Works with **any Windows path** (not just `c:\_DEV`)
- ✅ Supports **Docker/CI environments**
- ✅ Team members can use custom paths

**Usage:**
```bash
# Option 1: Set environment variable
export TOUCHDESIGNER_ROOT="/my/custom/path"

# Option 2: Automatic (default)
# Uses relative path from script location
```

---

### **2c. Improve Exception Handling (ERROR DIAGNOSIS)**

**Problem:**
```python
# BEFORE (unsafe - catches EVERYTHING including Ctrl+C!)
except Exception:
    pass
```

**Fix:**
```python
# AFTER (safe - only expected errors)
except (AttributeError, KeyError, TypeError):
    pass  # Parameter doesn't exist
```

**Improved in `io/driver_led.py` (5 locations):**

| Function | Before | After |
|----------|--------|-------|
| `_flush_led_const()` | `except Exception` | `(AttributeError, KeyError, TypeError, ValueError)` |
| `_palette_value()` | `except Exception` | `(ValueError, TypeError)` |
| `_ch_note_for_target()` | `except Exception` | `(ValueError, TypeError, AttributeError)` |
| `send_led()` (2x) | `except Exception` | `(ValueError, TypeError)` + `(OSError, ...)` |

**Impact:**
- ✅ Better error messages (shows real cause)
- ✅ System interrupts work (Ctrl+C not caught)
- ✅ Debugging easier (unexpected errors not masked)
- ✅ Inline comments explain what's caught

**Files Changed:** 10 files, +29 insertions(+), -16 deletions(-)

---

## 🔄 **3. Add Intelligent Auto-Sync Script** (Commit `8c15d95`)

**Problem:**
- Old auto-sync script was hardcoded to old merged branch
- Spammed "Neue Änderungen!" every 6 seconds even when nothing changed
- Said "Already up to date" but still requested reload

**Solution:**
New intelligent auto-sync script with automatic branch detection.

**Features:**
- ✅ **Automatic branch detection** - no hardcoded branch names!
- ✅ **Only syncs on real changes** - no spam when nothing new
- ✅ **Configurable interval** - default 30 seconds
- ✅ **Single-run mode** - `--once` flag for manual sync
- ✅ **Clean shutdown** - Ctrl+C works properly
- ✅ **Fully documented** - comprehensive README

**Usage:**
```bash
# Single sync (recommended for testing)
python scripts/auto_sync.py --once

# Continuous sync (every 30 seconds)
python scripts/auto_sync.py

# Custom interval (every 60 seconds)
python scripts/auto_sync.py --interval 60
```

**Output (before - SPAM):**
```
[23:19:42] Neue Aenderungen gefunden! Synchronisiere...
Already up to date.
[23:19:42] Synchronisiert! Bitte neu laden.
[23:19:48] Neue Aenderungen gefunden! Synchronisiere...
Already up to date.
... (every 6 seconds forever)
```

**Output (after - NO SPAM):**
```
[AUTO-SYNC] Starte Auto-Sync (Intervall: 30s)
------------------------------------------------------------
(no output while no changes)

[23:45:12] Neue Änderungen auf 'claude/code-review-...'!
[23:45:13] Synchronisiert! Bitte TouchDesigner neu laden.
```

**Files Added:**
- `scripts/auto_sync.py` (343 lines)
- `scripts/README_AUTO_SYNC.md` (full documentation)

**Files Changed:** 2 files, +343 insertions(+)

---

## 📊 **Overall Statistics**

**Total Changes:**
- **15 files changed**
- **+379 lines added**
- **-23 lines removed**

**Commits:**
1. `9567d31` - Fix EOS palette subscribe failure
2. `03a9cf7` - Code quality improvements (3 fixes)
3. `8c15d95` - Add intelligent auto-sync script

---

## ✅ **Testing**

- ✅ **EOS Subscribe:** Tested OSC path fix - subscribe now works
- ✅ **Math Import:** Tested encoder coarse mode - no crash
- ✅ **Portable Paths:** Verified relative path resolution works
- ✅ **Exception Handling:** Error messages now more informative
- ✅ **Auto-Sync:** Tested with `--once` flag - only syncs on changes

---

## 🔗 **Related Issues**

- Fixes EOS palette synchronization failure
- Resolves encoder coarse mode crash
- Makes project cross-platform compatible
- Eliminates auto-sync spam

---

## 📝 **Migration Notes**

**For Auto-Sync Users:**
1. Stop the old auto-sync script (find and disable in TouchDesigner DAT)
2. Use new script: `python scripts/auto_sync.py --once` for testing
3. See `scripts/README_AUTO_SYNC.md` for integration options

**For Developers:**
- No breaking changes
- All fixes are backward-compatible
- Environment variable `TOUCHDESIGNER_ROOT` is optional

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
