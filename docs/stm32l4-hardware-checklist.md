# STM32L4 Hardware Checklist for mcudbg v0.1

This checklist is for the current real-board demo path:

- target: `STM32L496VETx`
- project: `实验1 跑马灯(RGB)实验`
- probe runtime: `pyOCD`
- current real-hardware probe: `ST-Link`
- log: `UART`
- scenario: startup log stops at `sensor init...`, then target enters `HardFault`

Related files:

- [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c)
- [usart.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/SYSTEM/usart/usart.c)
- [ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)

---

## 1. Goal

The goal of this setup is to validate one narrow but complete loop:

1. connect the probe through `pyOCD`
2. connect `UART`
3. boot the board
4. observe startup logs
5. confirm the log stops at `sensor init...`
6. halt and inspect the target
7. confirm the target is in `HardFault`
8. use the ELF file for symbol-aware diagnosis

---

## 2. Required Hardware

Prepare:

1. one `STM32L496VETx` board
2. one `ST-Link` probe
3. one USB-to-UART adapter
4. jumper wires
5. one USB cable for board power if needed

Optional but useful:

1. a second serial terminal for manual comparison
2. a multimeter for basic power sanity check

---

## 3. Required Files

You should have these ready:

1. project file: [ATK_LED.uvprojx](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/ATK_LED.uvprojx)
2. ELF/AXF file: [ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)
3. modified source: [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c)

For `mcudbg`, the important symbol file is:

`d:\embed-mcp\实验1 跑马灯(RGB)实验\OBJ\ATK_LED.axf`

---

## 4. Probe Wiring

Use standard `SWD` wiring between `ST-Link` and the STM32 board:

1. `SWDIO`
2. `SWCLK`
3. `GND`
4. `VTref` or target voltage sense

Optional but recommended:

1. `NRST`

Checklist:

- `GND` must be shared
- target voltage reference must be valid
- the probe should detect the board at the correct logic level

If the probe cannot attach, the first things to check are:

1. ground continuity
2. board power
3. `SWDIO/SWCLK` swapped wires
4. target held in reset

---

## 5. UART Wiring

From the current project code in [usart.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/SYSTEM/usart/usart.c):

- `USART1_TX = PA9`
- `USART1_RX = PA10`
- baudrate configured in [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) is `115200`

For log capture, the minimum useful wiring is:

1. board `PA9 (TX)` -> USB-UART `RX`
2. board `GND` -> USB-UART `GND`

Optional:

1. USB-UART `TX` -> board `PA10 (RX)`

Recommended serial settings:

1. `115200`
2. `8-N-1`
3. no flow control

Important:

- connect `TX -> RX`, not `TX -> TX`
- keep UART ground shared with the board

---

## 6. Expected Boot Log

With the current modified demo source, the expected UART output is:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
```

After that, there should be no more normal progress logs.

This is expected for the demo.

---

## 7. Expected Fault Behavior

The current demo intentionally triggers a fault after `sensor init...` in [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c).

Expected outcome:

1. UART log stops after `sensor init...`
2. target no longer progresses into normal LED loop behavior
3. probe inspection through `pyOCD` should show a fault state
4. symbol-aware inspection should resolve into `HardFault_Handler`
5. fault analysis should point back toward the artificial startup path

---

## 8. Pre-Debug Sanity Checklist

Before using `mcudbg`, manually confirm:

1. the board powers on
2. the probe is detected by the host
3. the UART adapter is detected by the host
4. the correct serial port is known
5. the correct ELF/AXF path is known
6. the firmware running on the board matches the symbol file you will load

The last point is very important:

If the board firmware and the ELF do not match, symbol resolution will mislead the diagnosis.

---

## 9. Minimum mcudbg Inputs

For the first real-board run, you should have these values ready:

1. target name: `stm32l496ve` or the exact `pyocd` target name you decide to use
2. UART port: for example `COM3`
3. UART baudrate: `115200`
4. ELF path: `d:\embed-mcp\实验1 跑马灯(RGB)实验\OBJ\ATK_LED.axf`
5. suspected stage: `sensor init`

The current built-in profile name is:

`stm32l4_atk_led_demo`

---

## 10. Recommended Manual Validation Order

Do not jump straight into full automation.

Validate in this order:

### Step 1

Use a serial terminal first.

Confirm you can see:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
```

### Step 2

Use the probe separately.

Confirm:

1. you can connect through the `pyOCD` probe path
2. you can halt the target
3. you can read `PC/LR/SP`

### Step 3

Load the ELF and resolve `PC`.

Confirm the current location resolves to `HardFault_Handler`.

### Step 4

Then run `mcudbg` against the same board.

This sequence will save time because it isolates wiring issues from tool issues.

---

## 11. Most Likely Failure Cases

### No UART output

Check:

1. wrong COM port
2. wrong baudrate
3. `PA9` not actually connected to adapter `RX`
4. missing shared ground

### Probe cannot connect

Check:

1. wrong `SWD` wiring
2. target not powered
3. reset line held low
4. probe logic reference missing

### UART works but symbols look wrong

Check:

1. wrong ELF/AXF file
2. old binary still flashed
3. board firmware does not match current source

### Board keeps running instead of faulting

Check:

1. modified [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) was actually rebuilt
2. the updated image was really flashed
3. the build output matches the loaded ELF

---

## 12. Success Criteria

This setup is successful when all of the following are true:

1. UART shows logs up to `sensor init...`
2. no normal logs appear after that point
3. the probe can halt and inspect the target
4. the loaded ELF resolves the failing location correctly
5. `mcudbg` can produce a startup-failure or HardFault diagnosis consistent with the observed board state

---

## 13. Recommendation

For the first real demo, do not optimize for elegance.

Optimize for repeatability:

1. one fixed board
2. one fixed probe
3. one fixed UART adapter
4. one fixed firmware image
5. one fixed fault pattern

That repeatability is what will make your first public demo credible.
