import sys
from pathlib import Path

try:
    BASE_PATH = Path(project.folder).resolve()  # type: ignore[name-defined]
except Exception:
    BASE_PATH = Path(__file__).resolve().parent.parent if "__file__" in globals() else None
SRC_PATH = BASE_PATH / "src" if BASE_PATH else None
if SRC_PATH and SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

try:
    from td_helpers import project_flags
except Exception:
    project_flags = None

ENABLE_PALETTE_SYNC = True


def _palette_sync_enabled(base) -> bool:
    if not base:
        return False
    if project_flags:
        try:
            return project_flags.bool_flag('PALETTE_SYNC_ENABLED', ENABLE_PALETTE_SYNC)
        except Exception:
            pass
    try:
        override = base.fetch('PALETTE_SYNC_ENABLED', None)
        if override is not None:
            return bool(override)
    except Exception:
        pass
    return bool(ENABLE_PALETTE_SYNC)


def onFrameStart(frame):
    base = op('/project1')
    if not base:
        return
    if not _palette_sync_enabled(base):
        # Palette sync disabled; keep DAT quiet.
        return
    try:
        watchdog = mod('/project1/palette_logic/watchdog')
        pump = mod('/project1/palette_logic/pump')
        state = mod('/project1/palette_logic/state')
    except Exception as exc:
        print('[tick_exec] palette modules unavailable:', exc)
        return
    state.attach_base(base)
    # Use project timeline FPS (default 60 if not set)
    fps = max(int(project.cookRate), 1) if hasattr(project, 'cookRate') else 60
    if frame % fps == 0:
        watchdog.ensure_subscribed(base)
    pump_div = max(int(fps / 5), 1)
    if frame % pump_div == 0:
        pump.tick(base)
    return
