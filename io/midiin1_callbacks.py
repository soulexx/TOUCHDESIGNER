
def _append_bus(path, etype, ch, idx, val, raw=None):
    import time
    BUS = op('/project1/io/bus_events')
    if BUS.numRows == 0:
        BUS.appendRow(['ts','src','etype','ch','id','val','raw','path'])
    BUS.appendRow([time.time(),'device',etype,ch,idx,val,'' if raw is None else raw,'/'+path.lstrip('/')])

def onReceiveMIDI(dat, rowIndex, message, channel, index, value, input, bytes):
    api = op('/project1/io/midicraft_enc_api').module
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
        if kind == 'fader_msb':
            _append_bus(topic+'/msb', 'cc7', channel, index, float(value)/127.0, raw=value); return
        if kind == 'fader_lsb':
            _append_bus(topic+'/lsb', 'cc7', channel, index, float(value)/127.0, raw=value); return
        # sonst normalisierte CC7
        _append_bus(topic, 'cc7', channel, index, float(value)/127.0, raw=value); return
