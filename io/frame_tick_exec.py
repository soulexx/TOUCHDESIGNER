"""Execute DAT wrapper that calls the shared frame tick helper."""

from s2l_unit.frame_tick import process_frame


def onFrameStart(dat):
    process_frame()
    return
