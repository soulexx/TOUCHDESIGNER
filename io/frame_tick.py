import sacn_dispatch

SACN_EXEC_DAT_PATH = "/project1/io/sacn_exec"
DEFAULT_CHOP_PATH = "/project1/io/EOS_Universe_016"


def _resolve_sacn_chop():
    dat = op(SACN_EXEC_DAT_PATH)
    if dat:
        if dat.inputs and dat.inputs[0].isCHOP:
            return dat.inputs[0]
        chop_par = getattr(dat.par, "CHOPs", None)
        if chop_par and chop_par.eval():
            chop = op(chop_par.eval())
            if chop and chop.isCHOP:
                return chop
    chop = op(DEFAULT_CHOP_PATH)
    if chop and chop.isCHOP:
        return chop
    debug("[s2l][tick] no CHOP source configured")
    return None


def _chop_to_bytes(chop):
    if chop.numSamples == 0:
        return bytes()
    data = []
    for channel in chop.chans():
        raw = channel[0]
        # CHOP delivers DMX values directly (0-255), not normalized (0-1)
        value = max(0.0, min(255.0, raw))
        data.append(int(round(value)))
    if len(data) > 512:
        data = data[-512:]
    elif len(data) < 512:
        data.extend([0] * (512 - len(data)))
    return bytes(data)


def onFrameStart(dat):
    chop = _resolve_sacn_chop()
    if not chop:
        return
    payload = _chop_to_bytes(chop)
    if not payload:
        return
    universe_par = getattr(chop.par, "Universe", None)
    try:
        universe = int(universe_par.eval()) if universe_par else 1
    except Exception:
        universe = 1
    sacn_dispatch.handle_universe(payload, universe)
