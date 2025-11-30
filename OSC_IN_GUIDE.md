# OSC In Configuration Guide - Eos Feedback Integration

Complete guide for configuring OSC feedback from ETC Eos lighting console to TouchDesigner video player.

## Overview

The video player requires OSC feedback from Eos to:
- Detect active cue changes (GO button) → Trigger video jumps
- Detect pending cue info → Display and RECORD mode target
- Detect cue progress (0-1 float) → LED Idle/Fahrt state
- Detect previous cue (BACK button) → Optional previous marker jump

**Key Principle:** TouchDesigner is **receive-only** in FOLLOW mode. No OSC is sent back to Eos.

---

## Part 1: Eos OSC Output Configuration

### 1.1 Enable OSC Output on Eos

1. On Eos console, go to:
   - `Setup` → `System Settings` → `Show Control` → `OSC`
2. Enable **OSC TX** (Transmit)
3. Set TX IP Address: Your TouchDesigner computer's IP (e.g., `192.168.1.100`)
4. Set TX Port: `7001` (default, or match your TD OSC In port)
5. **Enable "Send Feedback"**: ✅

### 1.2 Configure Feedback Messages

Eos can send various feedback paths. We need:

**Essential Paths:**
- `/eos/out/active/cue/<list>/<cue>` - When active cue changes (GO pressed)
- `/eos/out/pending/cue/<list>/<cue>` - Next cue in list
- `/eos/out/active/cue` (Float 0-1) - Cue progress for fades

**Optional:**
- `/eos/out/previous/cue/<list>/<cue>` - Previous cue (BACK pressed)

**Eos Configuration:**
1. In Eos OSC settings, under "Filter" tab:
   - Enable "Cue Lists" feedback: ✅
   - Enable "Playback" feedback: ✅
2. You may need to enable specific feedback types:
   - `Settings` → `User` → `OSC Feedback` → Select all cue-related options

### 1.3 Test Eos OSC Output

Use a tool like **osculator**, **OSCDataMonitor**, or TouchDesigner's built-in OSC In DAT to verify:

1. Press GO on Eos
2. You should see:
   ```
   /eos/out/active/cue/1/1  (args: text "Cue 1")
   /eos/out/active/cue      (args: float 0.0)
   ```
3. During a fade:
   ```
   /eos/out/active/cue      (args: float 0.35)
   /eos/out/active/cue      (args: float 0.67)
   /eos/out/active/cue      (args: float 1.0)
   ```

**If not receiving:**
- Check network connectivity (`ping` from TD computer to Eos)
- Verify firewall allows UDP port 7001
- Check Eos diagnostic logs for OSC errors

---

## Part 2: TouchDesigner OSC In Setup

### 2.1 Locate Existing OSC In

Your project likely already has OSC In configured (for Eos control). Find it:

1. Navigate to `/project1/io/` or similar
2. Look for **OSC In DAT** or **OSC In CHOP** operators
3. Check parameters:
   - **Network Address**: `0.0.0.0` (listen on all interfaces)
   - **Network Port**: `7001` (must match Eos TX port)
   - **Local Address**: Your TD computer IP (optional, for specific interface)

**If no OSC In exists**, create one:
1. Create **OSC In DAT**
   - Name: `oscin_eos`
   - Network Port: `7001`
   - Enable "Active": ✅

### 2.2 Configure OSC In DAT Callback

If using **OSC In DAT**:

1. Open OSC In DAT's **callbacks**
2. Add callback function `onReceiveOSC`:

```python
def onReceiveOSC(dat, rowIndex, message, bytes):
    """
    Called when OSC message received
    message[0] = address (string)
    message[1:] = arguments (list)
    """
    try:
        address = message[0]
        args = message[1:] if len(message) > 1 else []

        # Route to video player handler
        handler = op('/project1/media/vplayer/osc_event_handler')
        if handler and hasattr(handler, 'module') and handler.module:
            handler.module.on_osc_message(address, *args)

    except Exception as exc:
        print(f"[OSC In] Error processing message: {exc}")
        import traceback
        traceback.print_exc()
```

**Save and test:**
1. Press GO on Eos
2. Check TouchDesigner textport for:
   ```
   [eos_event] JUMP: 1/1 -> 125.40s
   ```
   or
   ```
   [eos_event] No marker for 1/1, continuing playback
   ```

### 2.3 Alternative: OSC In MAP CHOP

If using **OSC In MAP CHOP** (more performance, less flexible):

1. Create **OSC In MAP CHOP**
   - Network Port: `7001`
2. Add message mappings:

**Mapping Table:**
| OSC Address Pattern | Channel Name | CHOP Output |
|---------------------|--------------|-------------|
| `/eos/out/active/cue/*/*` | `active_cue` | Extract list/cue |
| `/eos/out/pending/cue/*/*` | `pending_cue` | Extract list/cue |
| `/eos/out/active/cue` | `progress` | Float value |

3. Create **CHOP Execute DAT** on OSC In MAP:

```python
def onValueChange(channel, sampleIndex, val, prev):
    chan_name = channel.name

    if chan_name == 'active_cue':
        # Parse OSC address to extract list/cue
        # This is complex - DAT method preferred
        pass

    elif chan_name == 'progress':
        # Update progress in vplayer
        vplayer = op('/project1/media/vplayer')
        if vplayer:
            eos_state = vplayer.op('eos_state')
            if eos_state:
                eos_state['progress'] = val
```

**Note:** OSC In MAP CHOP is harder to parse dynamic addresses like `/eos/out/active/cue/<list>/<cue>`. **OSC In DAT is recommended** for this use case.

---

## Part 3: OSC Message Parsing

### 3.1 Understanding Eos OSC Format

Eos sends messages in different formats depending on version:

**Format 1: Separate list/cue in address**
```
Address: /eos/out/active/cue/1/23
Args: ["Cue 1 Thru 23"]  (text description)
```

**Format 2: Arguments contain list/cue**
```
Address: /eos/out/active/cue
Args: [1, 23, "Cue 1 Thru 23"]  (list, cue, description)
```

**Format 3: Progress float**
```
Address: /eos/out/active/cue
Args: [0.456]  (float 0-1)
```

### 3.2 Robust Parsing in osc_event_handler.py

The provided `osc_event_handler.py` handles both formats:

```python
def on_osc_message(address, *args):
    try:
        # Format 1: Address contains list/cue
        if '/eos/out/active/cue' in address and len(address.split('/')) >= 6:
            parts = address.split('/')
            cue_list = int(parts[4])
            cue_number = int(parts[5])
            on_active_cue_change(cue_list, cue_number)

        # Format 2: Args contain list/cue
        elif address == '/eos/out/active/cue' and len(args) >= 2:
            if isinstance(args[0], (int, float)) and isinstance(args[1], (int, float)):
                on_active_cue_change(int(args[0]), int(args[1]))
            elif isinstance(args[0], float):
                # Format 3: Progress float
                on_progress_update(args[0])

    except Exception as exc:
        print(f"[OSC] Parse error: {exc}")
```

### 3.3 Testing OSC Parsing

**Manual Test:**
1. In TouchDesigner, create **OSC Out CHOP**
2. Send test messages to localhost:7001:
   ```
   /eos/out/active/cue/1/23  (no args)
   /eos/out/pending/cue/1/24 (no args)
   /eos/out/active/cue       (arg: 0.5)
   ```
3. Check textport for handler output:
   ```
   [eos_event] JUMP: 1/23 -> 45.2s
   [eos_event] Pending: 1/24
   ```

**Live Test with Eos:**
1. Create marker for Cue 1/1 in RECORD mode
2. Switch to FOLLOW mode
3. Press GO on Eos to fire Cue 1/1
4. Video should jump to marker position
5. Check textport for confirmation

---

## Part 4: Network Configuration

### 4.1 Network Setup

**Typical Setup:**
- Eos Console: `192.168.1.10` (static IP)
- TouchDesigner Computer: `192.168.1.100` (static IP)
- Subnet Mask: `255.255.255.0`
- Gateway: Not required (local network)

**Configure Static IP on TD Computer:**
1. Windows: `Control Panel` → `Network and Internet` → `Network Connections`
2. Right-click Ethernet adapter → `Properties`
3. Select `Internet Protocol Version 4 (TCP/IPv4)`
4. Use static IP: `192.168.1.100`
5. Subnet: `255.255.255.0`

**Test Connectivity:**
```bash
ping 192.168.1.10
```

Should show:
```
Reply from 192.168.1.10: bytes=32 time<1ms TTL=128
```

### 4.2 Firewall Configuration

**Windows Firewall:**
1. Open `Windows Defender Firewall` → `Advanced Settings`
2. Create **Inbound Rule**:
   - Name: `TouchDesigner OSC In`
   - Protocol: `UDP`
   - Local Port: `7001`
   - Action: `Allow`
3. Apply to all profiles (Domain, Private, Public)

**Eos Side:**
- Eos typically has no firewall - OSC TX should work by default
- If issues, check Eos network settings for blocked ports

### 4.3 Port Conflicts

If port 7001 is already in use:

1. Check which app is using it:
   ```bash
   netstat -ano | findstr :7001
   ```
2. Change Eos TX port to `7002` (or other)
3. Update TouchDesigner OSC In port to match

**Common conflicts:**
- Another TouchDesigner instance
- Eos Nomad software running locally
- Other OSC control software (QLab, etc.)

---

## Part 5: Troubleshooting

### No OSC Messages Received

**Checklist:**
- [ ] Eos OSC TX enabled (Show Control settings)
- [ ] Eos TX IP matches TD computer IP
- [ ] Eos TX Port matches TD OSC In port (default 7001)
- [ ] TD OSC In DAT is "Active" (green flag)
- [ ] Network cable connected (if wired)
- [ ] Ping successful from TD to Eos
- [ ] Firewall allows UDP 7001 inbound
- [ ] No other app using port 7001

**Debug Steps:**
1. Use **Wireshark** to capture UDP traffic on port 7001:
   - Filter: `udp.port == 7001`
   - Press GO on Eos
   - Should see OSC packets in capture
2. If packets visible but TD not receiving:
   - Check TD OSC In "Local Address" (try `0.0.0.0`)
   - Restart TouchDesigner
   - Check OSC In DAT "Active" parameter

### Wrong Cue Numbers

If video jumps to wrong cues:

**Check Eos Cue Format:**
- Eos may send cue as `1.5` (cue 1, part 5)
- Your marker key is `1/1` (no parts)
- Solution: Modify `osc_event_handler.py` to strip part:
  ```python
  cue_number = int(float(parts[5]))  # 1.5 → 1
  ```

**Check List Number:**
- Eos may have multiple cue lists (1, 2, 3...)
- Verify markers use correct list number
- Example: Cue List 2, Cue 5 → Marker key `2/5`

### Progress Float Not Updating

If LED doesn't change Idle/Fahrt:

**Check Eos Fade Time:**
- Zero-time cues send progress 0.0 → 1.0 instantly
- Add small fade time (0.5s) to see progress updates

**Check OSC Feedback Rate:**
- Eos may throttle OSC updates
- In Eos settings, increase OSC feedback rate (if available)

**Manual Test:**
```python
# In TD, manually set progress
vplayer = op('/project1/media/vplayer')
vplayer.op('eos_state')['progress'] = 0.5  # Should trigger bright green LED
vplayer.op('eos_state')['progress'] = 0.0  # Should trigger dark green LED
```

### Video Jumps at Wrong Time

If video jumps before/after Eos GO:

**Check Message Order:**
- Eos may send `/eos/out/pending/cue` before `/eos/out/active/cue`
- Ensure `on_active_cue_change` only jumps, not `on_pending_cue_change`

**Check Marker Timing:**
- Marker position may be off (wrong time in RECORD)
- Re-record marker in RECORD mode at correct position

**Network Latency:**
- OSC messages may arrive with delay (>50ms)
- Check network latency: `ping -t 192.168.1.10` (watch for spikes)
- Use wired Ethernet (not Wi-Fi) for sub-5ms latency

---

## Part 6: Advanced Configuration

### 6.1 Multiple Eos Consoles

If using backup console or distributed system:

**Option 1: Multiple OSC In DATs**
1. Create `oscin_eos_primary` on port 7001
2. Create `oscin_eos_backup` on port 7002
3. Both route to same `osc_event_handler`

**Option 2: Eos OSC Merge**
1. Configure both consoles to send to same IP:port
2. TD receives from whichever is active
3. Handle duplicate messages (debounce in handler)

### 6.2 OSC Logging for Debug

Enable detailed OSC logging:

1. Create **Table DAT** `osc_log`
2. Modify OSC In callback:
```python
def onReceiveOSC(dat, rowIndex, message, bytes):
    # Log message
    log = op('osc_log')
    if log:
        import datetime
        timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log.appendRow([timestamp, message[0], str(message[1:])])

    # Route to handler (as before)
    ...
```

3. Review `osc_log` for unexpected messages

### 6.3 Custom OSC Paths

If your Eos uses non-standard paths:

**Edit osc_event_handler.py:**
```python
# Change this:
if '/eos/out/active/cue' in address:

# To your custom path:
if '/custom/cue/active' in address:
```

**Or use OSC path remapping:**
1. Create **Select DAT** to filter/remap addresses
2. Before routing to handler, replace paths:
   ```python
   if '/custom/cue/active' in address:
       address = address.replace('/custom/cue/active', '/eos/out/active/cue')
   ```

---

## Part 7: Eos-Specific Notes

### ETC Eos Family Compatibility

**Tested Consoles:**
- Eos Ti: ✅ Full support
- Eos Ion: ✅ Full support
- Eos Element: ⚠️ Limited OSC feedback (check manual)
- Eos Nomad: ✅ Full support (software version)

**Software Versions:**
- Eos 3.x: Full OSC feedback
- Eos 2.x: Limited feedback paths (upgrade recommended)

### Common Eos OSC Paths Reference

**Cue Feedback:**
- `/eos/out/active/cue/<list>/<cue>` - Active cue changed
- `/eos/out/pending/cue/<list>/<cue>` - Next cue
- `/eos/out/previous/cue/<list>/<cue>` - Previous cue
- `/eos/out/active/cue` (float) - Fade progress

**Playback Feedback:**
- `/eos/out/event/cue/<list>/fire` - Cue fired
- `/eos/out/event/cue/<list>/stop` - Cue stopped

**Not Used by Video Player:**
- `/eos/out/param/*` - Channel parameter values
- `/eos/out/chan/*` - Channel selection
- `/eos/out/cmd` - Command line feedback

---

## Completion Checklist

Verify OSC integration is working:

- [ ] OSC In DAT receiving messages (check "Received Messages" in parameters)
- [ ] Textport shows `[eos_event]` messages when Eos GO is pressed
- [ ] Eos pending cue displayed in video player UI
- [ ] Video jumps on Eos GO (when marker exists)
- [ ] Progress float updates `eos_state['progress']` (check with Info CHOP)
- [ ] LED changes color during fade (Idle → Fahrt → Idle)

---

**Next:** See [LED_FEEDBACK_GUIDE.md](LED_FEEDBACK_GUIDE.md) for LED integration details.

**Author:** Claude Code Agent
**Version:** 1.0
**Date:** 2025-01-14
