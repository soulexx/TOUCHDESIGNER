# CHOP Execute - increments time_play when playing

def onFrameStart(channel, sampleIndex, val, prev):
    try:
        transport = op('/project1/media/transport_control')
        constant1 = op('/project1/media/constant1')
        time_play = op('/project1/media/time_play')
        
        if not (transport and constant1 and time_play):
            return
        
        playing = transport['playing'].eval()
        vel = constant1['vel'].eval()
        
        if playing > 0.5 and vel > 0.5:
            current = time_play['seconds'].eval()
            time_play.par.value0 = current + (1.0 / 60.0)
    except:
        pass
    return

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
