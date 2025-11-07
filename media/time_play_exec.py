# CHOP Execute - increments time_play when playing
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

try:
    import video_control
except Exception:
    video_control = None

_OP_CACHE = {}
_CONTROLLER = None
TRANSPORT_PATH = '/project1/media/transport_control'
VELOCITY_PATH = '/project1/media/constant1'
TIME_PLAY_PATH = '/project1/media/time_play'
PLAY_CHAN = 'playing'
VELOCITY_CHAN = 'vel'
SECONDS_CHAN = 'seconds'


def _video_enabled() -> bool:
    if project_flags:
        try:
            return project_flags.bool_flag('VIDEO_CONTROL_ENABLED', True)
        except Exception:
            pass
    return True


def _get_op(path):
    cached = _OP_CACHE.get(path)
    if cached is not None and getattr(cached, 'valid', True):
        return cached
    node = op(path)
    if node is not None:
        _OP_CACHE[path] = node
    return node


def _get_controller():
    global _CONTROLLER
    if video_control is None:
        return None
    if _CONTROLLER is not None:
        return _CONTROLLER
    try:
        _CONTROLLER = video_control.get_controller()
    except Exception:
        _CONTROLLER = None
    return _CONTROLLER


def _frame_delta() -> float:
    try:
        rate = float(project.cookRate)  # type: ignore[name-defined]
        if rate > 0.0:
            return 1.0 / rate
    except Exception:
        pass
    return 1.0 / 60.0


def onFrameStart(channel, sampleIndex, val, prev):
    if not _video_enabled():
        return

    time_play = _get_op(TIME_PLAY_PATH)
    controller = _get_controller()
    if controller and time_play:
        try:
            info = controller.info()
        except Exception:
            info = None
        if info and info.seconds is not None:
            try:
                time_play.par.value0 = float(info.seconds)
            except Exception:
                pass
        return

    transport = _get_op(TRANSPORT_PATH)
    velocity = _get_op(VELOCITY_PATH)
    if not (transport and velocity and time_play):
        return

    try:
        playing = float(transport[PLAY_CHAN].eval())
        vel = float(velocity[VELOCITY_CHAN].eval())
        current = float(time_play[SECONDS_CHAN].eval())
    except Exception:
        return

    if playing <= 0.5 or vel <= 0.0:
        return

    delta = _frame_delta() * vel
    time_play.par.value0 = current + delta

def onValueChange(channel, sampleIndex, val, prev):
    return
def whileOn(channel, sampleIndex, val, prev):
    return
def whileOff(channel, sampleIndex, val, prev):
    return
def onOffToOn(channel, sampleIndex, val, prev):
    return
def onOnToOff(channel, sampleIndex, val, prev):
    return
