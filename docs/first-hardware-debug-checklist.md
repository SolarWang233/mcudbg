# First Hardware Debug Checklist

This document is for the first real-board validation of `mcudbg v0.1`.

Current target path:

- board: `STM32L496VETx`
- probe: `CMSIS-DAP`
- log: `UART`
- symbol file: `ATK_LED.axf`
- scenario: startup log stops at `sensor init...`, then target enters `HardFault`

Related docs:

- [stm32l4-hardware-checklist.md](/d:/embed-mcp/mcudbg/docs/stm32l4-hardware-checklist.md)
- [mcp-usage-example.md](/d:/embed-mcp/mcudbg/docs/mcp-usage-example.md)

---

## 1. Goal

The first real-board session is successful if you can confirm:

1. UART logs are visible
2. the probe can attach
3. the ELF matches the flashed image
4. the board stops after `sensor init...`
5. `mcudbg` reports a startup failure or HardFault consistent with the real board state

---

## 2. Golden Rule

Do not debug everything at once.

Always isolate the problem in this order:

1. power
2. UART
3. probe attach
4. ELF match
5. diagnosis output

If you skip this order, you can lose a lot of time.

---

## 3. Stage 1: Power And Basic Board State

Before using any tool, confirm:

1. the board is powered
2. the board ground is shared with probe and UART adapter
3. there is no obvious reset hold condition
4. the board is actually running the expected image

If the board is not powered correctly, everything else will look broken.

Quick checks:

1. power LED on board is lit
2. `VTref` is visible to the probe
3. no connector is loose

---

## 4. Stage 2: UART Validation

First use a normal serial terminal, not `mcudbg`.

Expected output:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
```

If you do not see logs:

1. check the correct `COM` port
2. check baudrate is `115200`
3. check `PA9 -> USB-UART RX`
4. check shared `GND`
5. confirm the modified firmware was really flashed

If the output is garbled:

1. wrong baudrate
2. wrong clock setup
3. weak or noisy UART wiring

If you only see partial logs:

1. this may be normal if the fault happens quickly
2. compare multiple resets
3. make sure the serial terminal opens before power-up or reset

---

## 5. Stage 3: Probe Attach Validation

Before involving `mcudbg`, confirm the probe works with a direct debug tool flow.

You need to verify:

1. `CMSIS-DAP` is detected
2. target can be attached
3. target can be halted
4. `PC/LR/SP` can be read

If the probe cannot connect:

1. check `SWDIO`
2. check `SWCLK`
3. check `GND`
4. check `VTref`
5. check whether `NRST` is stuck low
6. lower SWD frequency if needed

If the probe connects but register reads fail:

1. target may be continuously resetting
2. target may be in an unstable power state
3. wrong target name may be selected

---

## 6. Stage 4: ELF Match Validation

This is a very common source of false conclusions.

You must confirm:

1. the flashed firmware is built from the same source you are reading
2. the loaded ELF/AXF matches that flashed image
3. the path points to the current build output

Use:

[ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)

If symbol resolution looks wrong:

1. old binary may still be on the board
2. current `.axf` may not match the flashed image
3. rebuild may not have happened after source changes

---

## 7. Stage 5: Expected Fault Validation

With the current demo source in [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c), the expected behavior is:

1. logs stop after `sensor init...`
2. program does not continue into the normal LED loop
3. target ends in a fault path

If the board keeps blinking normally:

1. your modified firmware was not flashed
2. the source was changed but not rebuilt
3. you are running a different image than expected

If the board hardfaults too early:

1. source may have been edited incorrectly
2. UART may not have initialized before the fault
3. the fault may be happening before log flush completes

---

## 8. Stage 6: mcudbg Validation

Only after manual checks are good should you use `mcudbg`.

Recommended sequence:

```text
list_demo_profiles()
load_demo_profile("stm32l4_atk_led_demo")
configure_target(uart_port="COM5")
get_runtime_config()
connect_with_config()
log_tail(20)
diagnose_startup_failure()
diagnose_hardfault()
```

What to check:

1. `connect_with_config()` returns `ok` or a useful `partial`
2. `log_tail()` shows `sensor init...`
3. `diagnose_startup_failure()` identifies the correct startup stage
4. `diagnose_hardfault()` reports a fault class and symbol context

---

## 9. If UART Works But mcudbg Log Does Not

Possible causes:

1. wrong `COM` port configured in `mcudbg`
2. another serial tool still holds the port open
3. `mcudbg` opens the port after the short log burst has already passed

What to do:

1. close all other serial terminals
2. power-cycle or reset the board after `mcudbg` connects
3. make sure the configured port matches Device Manager

---

## 10. If Probe Works But Diagnosis Looks Wrong

Possible causes:

1. wrong ELF
2. target name mismatch
3. fault register interpretation bug
4. firmware image and source are out of sync

What to do:

1. compare `probe_read_registers()` output with diagnosis output
2. inspect `log_tail()` separately
3. verify the ELF path in `get_runtime_config()`
4. try a fresh rebuild and reflash

---

## 11. If connect_with_config() Returns partial

This is not always a blocker.

Read the `missing` field carefully.

Typical meanings:

1. missing `log.port`: UART port not configured
2. missing `elf.path`: no symbol file configured
3. probe connection succeeded but UART did not

Best practice:

1. fix one missing item at a time
2. do not rewire everything blindly

---

## 12. Most Likely First-Day Failure Modes

### Failure Mode 1

No UART logs at all.

Most likely:

1. wrong UART port
2. TX/RX crossed wrong
3. firmware not updated

### Failure Mode 2

Probe cannot halt target.

Most likely:

1. SWD wiring issue
2. target power issue
3. reset state issue

### Failure Mode 3

Diagnosis says wrong symbol.

Most likely:

1. wrong ELF
2. old `.axf`
3. flashed image mismatch

### Failure Mode 4

Logs stop, but no fault is detected.

Most likely:

1. firmware stuck in a loop rather than faulting
2. attach timing issue
3. diagnosis happened too late or too early

---

## 13. Recommended Evidence To Save

For the first successful real demo, save these:

1. screenshot of serial terminal showing logs
2. screenshot or dump of diagnosis output
3. exact ELF path used
4. exact UART port used
5. probe type used

This will help a lot when you write the launch article or reproduce the demo later.

---

## 14. Recommendation

Your first goal is not elegance. It is repeatability.

If you can make one board, one firmware image, one UART port, one probe, and one fault pattern behave the same way every time, you already have something very valuable.
