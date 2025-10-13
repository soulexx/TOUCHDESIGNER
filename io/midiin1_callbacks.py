
def _append_bus(path, etype, ch, idx, val, raw=None):
    import time
    BUS = op('/project1/io/bus_events')
    if BUS.numRows == 0:
        BUS.appendRow(['ts','src','etype','ch','id','val','raw','path'])
    BUS.appendRow([time.time(),'device',etype,ch,idx,val,'' if raw is None else raw,'/'+path.lstrip('/')])

def onReceiveMIDI(dat, rowIndex, message, channel, index, value, input, bytes):
    api = op('/project1/io/midicraft_enc_api').module
    filt_op = op('/project1/layers/menus/event_filters')
    filt_mod = filt_op.module if filt_op else None
    topic, kind = api.midi_to_topic(message, int(channel), int(index))
    if not topic:
        return
    if message in ('Note On','Note Off'):
        v = 1 if (message=='Note On' and int(value)>0) else 0
        _append_bus(topic, 'note', channel, index, v, raw=value); return
    if message == 'Control Change':
        if kind == 'enc_rel':
            d = int(value) if int(value) < 64 else int(value) - 128
            _append_bus(topic, 'enc_rel', channel, index, d, raw=value); return
        if kind in ('fader_msb', 'fader_lsb'):
            part = 'msb' if kind == 'fader_msb' else 'lsb'
            norm = float(value) / 127.0
            combined = None
            if filt_mod:
                func = getattr(filt_mod, 'fader_smooth', None)
                if callable(func):
                    combined = func(topic + '/' + part, norm)
            if combined is None and part == 'msb':
                combined = norm  # fallback auf 7-bit falls kein Filter
            if combined is not None:
                _append_bus(topic, 'cc7', channel, index, float(combined), raw=value)
            return
        # sonst normalisierte CC7
        _append_bus(topic, 'cc7', channel, index, float(value)/127.0, raw=value); return
