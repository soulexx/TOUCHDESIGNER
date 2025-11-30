"""
Automatic VPlayer Builder for TouchDesigner
Builds complete /project1/media/vplayer component with all operators

Usage:
1. Open your TouchDesigner project (MIDICRAFT_to_EOS_1.1.toe)
2. Open Textport (Alt+T)
3. Run: exec(open('c:\\_DEV\\TOUCHDESIGNER\\build_vplayer.py').read())
4. Wait for "VPLAYER BUILD COMPLETE" message

Author: Claude Code Agent
Version: 1.0
"""

import os

# ==============================================================================
# CONFIGURATION
# ==============================================================================

VPLAYER_PATH = '/project1/media/vplayer'
SCRIPTS_DIR = 'c:\\_DEV\\TOUCHDESIGNER\\vplayer_scripts'

print("=" * 80)
print("VPLAYER AUTOMATIC BUILDER")
print("=" * 80)

# ==============================================================================
# STEP 1: Create Base COMP
# ==============================================================================

print("\n[1/8] Creating Base COMP...")

# Navigate to parent
parent_path = '/project1/media'
parent_comp = op(parent_path)

if not parent_comp:
    print(f"ERROR: Parent path {parent_path} not found!")
    print("Make sure your project structure is correct.")
else:
    # Delete existing vplayer if exists
    existing = op(VPLAYER_PATH)
    if existing:
        print(f"  - Deleting existing vplayer at {VPLAYER_PATH}")
        existing.destroy()

    # Create new Base COMP
    vplayer = parent_comp.create(baseCOMP, 'vplayer')
    print(f"  ✓ Created Base COMP: {vplayer.path}")

# ==============================================================================
# STEP 2: Create State CHOPs
# ==============================================================================

print("\n[2/8] Creating State CHOPs...")

# State CHOP (player state)
state = vplayer.create(constantCHOP, 'state')
state.par.name0 = 'mode'
state.par.value0 = 0  # 0=FOLLOW, 1=RECORD
state.par.name1 = 'speed'
state.par.value1 = 1.0
state.par.name2 = 'volume'
state.par.value2 = 0.8
state.par.name3 = 'loop'
state.par.value3 = 0
state.par.name4 = 'scrub_value'
state.par.value4 = 0
print(f"  ✓ Created state CHOP with 5 channels")

# Eos State CHOP (Eos feedback)
eos_state = vplayer.create(constantCHOP, 'eos_state')
eos_state.par.name0 = 'active_list'
eos_state.par.value0 = 0
eos_state.par.name1 = 'active_cue'
eos_state.par.value1 = 0
eos_state.par.name2 = 'pending_list'
eos_state.par.value2 = 0
eos_state.par.name3 = 'pending_cue'
eos_state.par.value3 = 0
eos_state.par.name4 = 'progress'
eos_state.par.value4 = 0
print(f"  ✓ Created eos_state CHOP with 5 channels")

# ==============================================================================
# STEP 3: Create Markers Table DAT
# ==============================================================================

print("\n[3/8] Creating Markers Table DAT...")

markers = vplayer.create(tableDAT, 'markers')
markers.par.rows = 1
markers.par.cols = 3
markers.par.rowheight = 20
markers.par.colstretch1 = 1

# Set header row
markers[0, 0] = 'key'
markers[0, 1] = 'pos_s'
markers[0, 2] = 'label'

print(f"  ✓ Created markers table (key, pos_s, label)")

# ==============================================================================
# STEP 4: Create Video & Audio Chain
# ==============================================================================

print("\n[4/8] Creating Video & Audio Chain...")

# Movie File In TOP
moviefilein1 = vplayer.create(moviefileinTOP, 'moviefilein1')
moviefilein1.par.file = ''  # Will be set by user
moviefilein1.par.play = True  # Always playing
moviefilein1.par.speed.expr = "op('state')['speed']"
moviefilein1.par.loop.expr = "op('state')['loop']"
moviefilein1.par.indexmode = 'cuepointseconds'
print(f"  ✓ Created moviefilein1 TOP")

# Null TOP
null_vid1 = vplayer.create(nullTOP, 'null_vid1')
null_vid1.setInput(0, moviefilein1)
print(f"  ✓ Created null_vid1 TOP")

# Out TOP
out1 = vplayer.create(outTOP, 'out1')
out1.setInput(0, null_vid1)
print(f"  ✓ Created out1 TOP")

# Audio Movie CHOP
audiomovie1 = vplayer.create(audiomovieCHOP, 'audiomovie1')
audiomovie1.par.top = moviefilein1
print(f"  ✓ Created audiomovie1 CHOP")

# Audio Device Out CHOP
audiodeviceout1 = vplayer.create(audiodeviceoutCHOP, 'audiodeviceout1')
audiodeviceout1.setInput(0, audiomovie1)
audiodeviceout1.par.volume.expr = "op('state')['volume']"
print(f"  ✓ Created audiodeviceout1 CHOP")

# Info CHOP
info_video = vplayer.create(infoCHOP, 'info_video')
info_video.par.op = moviefilein1
print(f"  ✓ Created info_video CHOP")

# ==============================================================================
# STEP 5: Create Fader Input CHOPs
# ==============================================================================

print("\n[5/8] Creating Fader Input CHOPs...")

# Scrub Input (Fader 1)
scrub_input = vplayer.create(constantCHOP, 'scrub_input')
scrub_input.par.name0 = 'value'
scrub_input.par.value0 = 0
print(f"  ✓ Created scrub_input CHOP")

# Scrub to Seconds Converter
scrub_to_seconds = vplayer.create(mathCHOP, 'scrub_to_seconds')
scrub_to_seconds.setInput(0, scrub_input)
scrub_to_seconds.par.combine = 'mult'
scrub_to_seconds.par.mult.expr = "op('info_video')['length_seconds'] if op('info_video').numChans > 0 else 1"
print(f"  ✓ Created scrub_to_seconds CHOP")

# Scrub Execute DAT
scrub_execute = vplayer.create(chopexecDAT, 'scrub_execute')
scrub_execute.par.chop = scrub_to_seconds

scrub_execute_code = """
def onValueChange(channel, sampleIndex, val, prev):
    # On scrub fader change, jump video
    moviefile = op('../moviefilein1')
    if moviefile and abs(val - prev) > 0.01:  # Debounce
        try:
            moviefile.par.cuepointseconds = val
            moviefile.par.cue.pulse()
        except:
            pass

def whileOn(channel, sampleIndex, val, prev):
    return

def whileOff(channel, sampleIndex, val, prev):
    return

def onOffToOn(channel, sampleIndex, val, prev):
    return

def onOnToOff(channel, sampleIndex, val, prev):
    return
"""
scrub_execute.text = scrub_execute_code
print(f"  ✓ Created scrub_execute DAT")

# Speed Input (Fader 2) - already bound to moviefilein1.speed
speed_input = vplayer.create(constantCHOP, 'speed_input')
speed_input.par.name0 = 'value'
speed_input.par.value0 = 1.0
print(f"  ✓ Created speed_input CHOP")

# Volume Input (Fader 3) - already bound to audiodeviceout1.volume
volume_input = vplayer.create(constantCHOP, 'volume_input')
volume_input.par.name0 = 'value'
volume_input.par.value0 = 0.8
print(f"  ✓ Created volume_input CHOP")

# ==============================================================================
# STEP 6: Create Script DATs (from files)
# ==============================================================================

print("\n[6/8] Creating Script DATs...")

def load_script(filename):
    """Load script from vplayer_scripts directory"""
    filepath = os.path.join(SCRIPTS_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"    WARNING: Could not load {filename}: {e}")
        return f"# Error loading {filename}\n# {e}"

# OSC Event Handler
osc_event_handler = vplayer.create(textDAT, 'osc_event_handler')
osc_event_handler.text = load_script('osc_event_handler.py')
print(f"  ✓ Created osc_event_handler DAT")

# Marker Write
marker_write = vplayer.create(textDAT, 'marker_write')
marker_write.text = load_script('marker_write.py')
print(f"  ✓ Created marker_write DAT")

# Marker Delete
marker_delete = vplayer.create(textDAT, 'marker_delete')
marker_delete.text = load_script('marker_delete.py')
print(f"  ✓ Created marker_delete DAT")

# Marker Lookup
marker_lookup = vplayer.create(textDAT, 'marker_lookup')
marker_lookup.text = load_script('marker_lookup.py')
print(f"  ✓ Created marker_lookup DAT")

# ==============================================================================
# STEP 7: Create LED Feedback CHOPs
# ==============================================================================

print("\n[7/8] Creating LED Feedback CHOPs...")

# LFO for blink
led_blink_lfo = vplayer.create(lfoCHOP, 'led_blink_lfo')
led_blink_lfo.par.type = 'square'
led_blink_lfo.par.freq = 2  # 2 Hz = 500ms period
led_blink_lfo.par.amp = 1
led_blink_lfo.par.offset = 0
print(f"  ✓ Created led_blink_lfo CHOP")

# LED Values (constants for different states)
led_values = vplayer.create(constantCHOP, 'led_values')
led_values.par.name0 = 'dark_green'
led_values.par.value0 = 20
led_values.par.name1 = 'bright_green'
led_values.par.value1 = 100
led_values.par.name2 = 'off'
led_values.par.value2 = 0
print(f"  ✓ Created led_values CHOP")

# LED State Logic (Script CHOP)
led_state_select = vplayer.create(scriptCHOP, 'led_state_select')
led_state_code = """
# LED State Selector
# RECORD: Blink green
# FOLLOW Idle: Dark green
# FOLLOW Fahrt: Bright green

def cook(scriptOp):
    try:
        state = op('state')
        eos_state = op('eos_state')
        led_values = op('led_values')
        blink_lfo = op('led_blink_lfo')

        if not all([state, eos_state, led_values, blink_lfo]):
            return

        mode = state['mode'].eval()
        progress = eos_state['progress'].eval()

        # Get LED value
        if mode == 1:  # RECORD mode
            # Blink: Use LFO value to switch between bright and off
            blink_val = blink_lfo[0].eval()
            if blink_val > 0.5:
                led_val = led_values['bright_green'].eval()
            else:
                led_val = led_values['off'].eval()
        else:  # FOLLOW mode
            if progress < 0.01 or progress > 0.99:
                # Idle: Dark green
                led_val = led_values['dark_green'].eval()
            else:
                # Fahrt: Bright green
                led_val = led_values['bright_green'].eval()

        # Output
        scriptOp.clear()
        scriptOp.numChans = 1
        scriptOp[0].name = 'btn_21_led'
        scriptOp[0] = led_val

    except Exception as e:
        pass  # Suppress errors during init
"""
led_state_select.text = led_state_code
print(f"  ✓ Created led_state_select CHOP (Script)")

# LED Output (final constant for driver_led)
led_go_out = vplayer.create(constantCHOP, 'led_go_out')
led_go_out.par.name0 = 'btn_21'
led_go_out.par.value0.expr = "op('led_state_select')[0] if op('led_state_select').numChans > 0 else 0"
print(f"  ✓ Created led_go_out CHOP")

# Flash Timer (optional, for marker set/delete feedback)
led_flash_timer = vplayer.create(timerCHOP, 'led_flash_timer')
led_flash_timer.par.length = 0.2  # 200ms flash
led_flash_timer.par.start = 0  # Manual trigger
print(f"  ✓ Created led_flash_timer CHOP")

# ==============================================================================
# STEP 8: Layout & Organization
# ==============================================================================

print("\n[8/8] Organizing layout...")

# Set node positions for clean layout
# Top row: TOPs
moviefilein1.nodeX = 0
moviefilein1.nodeY = 0
null_vid1.nodeX = 200
null_vid1.nodeY = 0
out1.nodeX = 400
out1.nodeY = 0

# Second row: Audio CHOPs
audiomovie1.nodeX = 0
audiomovie1.nodeY = -150
audiodeviceout1.nodeX = 200
audiodeviceout1.nodeY = -150
info_video.nodeX = 400
info_video.nodeY = -150

# Third row: State CHOPs
state.nodeX = 0
state.nodeY = -300
eos_state.nodeX = 200
eos_state.nodeY = -300
markers.nodeX = 400
markers.nodeY = -300

# Fourth row: Fader CHOPs
scrub_input.nodeX = 0
scrub_input.nodeY = -450
scrub_to_seconds.nodeX = 200
scrub_to_seconds.nodeY = -450
scrub_execute.nodeX = 400
scrub_execute.nodeY = -450

speed_input.nodeX = 0
speed_input.nodeY = -550
volume_input.nodeX = 200
volume_input.nodeY = -550

# Fifth row: Scripts
osc_event_handler.nodeX = 0
osc_event_handler.nodeY = -700
marker_write.nodeX = 200
marker_write.nodeY = -700
marker_delete.nodeX = 400
marker_delete.nodeY = -700
marker_lookup.nodeX = 600
marker_lookup.nodeY = -700

# Sixth row: LED CHOPs
led_blink_lfo.nodeX = 0
led_blink_lfo.nodeY = -850
led_values.nodeX = 200
led_values.nodeY = -850
led_state_select.nodeX = 400
led_state_select.nodeY = -850
led_go_out.nodeX = 600
led_go_out.nodeY = -850
led_flash_timer.nodeX = 800
led_flash_timer.nodeY = -850

print(f"  ✓ Layout organized")

# ==============================================================================
# COMPLETION
# ==============================================================================

print("\n" + "=" * 80)
print("VPLAYER BUILD COMPLETE!")
print("=" * 80)
print(f"\nComponent created at: {VPLAYER_PATH}")
print("\nNext steps:")
print("1. Configure OSC In callbacks (see OSC_IN_GUIDE.md)")
print("2. Connect LED output to driver_led.py (see LED_FEEDBACK_GUIDE.md)")
print("3. Load video file in moviefilein1 parameter")
print("4. Test with MIDICRAFT ENC faders and Eos OSC feedback")
print("\nQuick Test:")
print("  - Set state['mode'] = 1 to test RECORD mode (LED should blink)")
print("  - Set eos_state['progress'] = 0.5 to test FOLLOW Fahrt (LED bright)")
print("\nFor full guide, see: VPLAYER_BUILD_GUIDE.md")
print("=" * 80)
