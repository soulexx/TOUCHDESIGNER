# me - this DAT
#
# frame - the current frame
# state - True if the timeline is paused
#
# Make sure the corresponding toggle is enabled in the Execute DAT.

import time

_MANAGER = op("/project1/io/led_blink_manager")


def _tick():
    if not _MANAGER:
        return
    mod = getattr(_MANAGER, "module", None)
    if not mod:
        return
    try:
        mod.tick(time.monotonic())
    except Exception as exc:
        print("[led_blink_exec] EXC tick:", exc)


def onStart():
    _tick()


def onCreate():
    _tick()


def onExit():
    return


def onFrameStart(frame):
    _tick()


def onFrameEnd(frame):
    return


def onPlayStateChange(state):
    return


def onDeviceChange():
    return


def onProjectPreSave():
    return


def onProjectPostSave():
    return
