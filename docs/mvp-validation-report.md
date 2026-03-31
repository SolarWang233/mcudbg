# mcudbg v0.1 MVP Validation Report

## Summary

`mcudbg v0.1` has passed its first real-board MVP validation on `STM32L496VETx`.

The validated loop is:

`real board -> ST-Link / pyOCD -> UART logs -> ELF symbol resolution -> mcudbg diagnosis`

This confirms that `mcudbg` is no longer only a mock/demo skeleton. It can already inspect a real startup-stage fault on hardware and return a diagnosis consistent with manual debugging.

## Validation Scope

This validation focused on the narrowest useful MVP path:

- Target board: `STM32L496VETx`
- Probe: `ST-Link`
- Probe runtime: `pyOCD`
- Log channel: `UART`
- Symbol source: `ATK_LED.axf`
- Scenario: startup reaches `sensor init...` and then enters `HardFault`

The goal was to verify that `mcudbg` can:

- connect to the real target
- capture real UART logs
- read real core and fault registers
- resolve symbols from the ELF
- return a diagnosis that matches the observed board state

## Validation Environment

- Host OS: `Windows`
- IDE/tooling used during bring-up: `Keil`, `VS Code`, `Codex`
- Firmware project: [ATK_LED.uvprojx](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/ATK_LED.uvprojx)
- ELF used by `mcudbg`: [ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)
- `mcudbg` profile: `stm32l4_atk_led_demo`

## Fault Sample

The firmware was modified to create a stable startup-stage fault sample:

- boot logs print successfully
- execution reaches `sensor init...`
- firmware intentionally jumps to an invalid execution target
- `HardFault_Handler` prints the captured fault context through UART

This created a deterministic, repeatable board-side signal for `mcudbg` to analyze.

## MCP Tools Validated

The following tools were exercised successfully in the real-board loop:

- `list_demo_profiles`
- `load_demo_profile`
- `get_runtime_config`
- `connect_with_config`
- `log_tail`
- `probe_reset`
- `diagnose_startup_failure`
- `diagnose_hardfault`

Supporting probe/log paths were also verified during bring-up:

- `probe_halt`
- `probe_read_registers`
- `probe_resume`
- `log_connect`
- `elf_load`

## Real UART Output

Observed UART output from the board:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...

[HardFault]
MSP  = 0x20000738
SP[0]= 0xFFFFFFFF
SP[1]= 0x08001975
SP[2]= 0x00010B61
SP[3]= 0x00010B61
SP[4]= 0x00013880
SP[5]= 0x000003E8
SP[6]= 0x00000001
SP[7]= 0x0800273D
CFSR = 0x00000001
HFSR = 0x40000000
MMFAR= 0xE000ED34
BFAR = 0xE000ED38
SHCSR= 0x00000000
```

This confirms that:

- startup progressed into the expected stage
- the fault was reproduced on real hardware
- the fault context was externally observable

## mcudbg Diagnosis Result

`mcudbg` successfully returned:

- `startup_failure_with_fault`
- `hardfault_detected`
- fault class: `instruction_access_violation`
- `PC` resolved to `HardFault_Handler`
- `LR` resolved to `_printf_char_file`

Representative diagnosis facts returned by the toolchain:

- `PC = 0x8001976`
- `LR = 0x8000725`
- `SP = 0x20000740`
- `CFSR = 0x1`
- `HFSR = 0x40000000`

The diagnosis matched the intended fault model:

- invalid execution target
- startup-stage failure near `sensor init`
- fault escalated into `HardFault`

## MVP Conclusion

`mcudbg v0.1` MVP is considered validated.

The project has now demonstrated all of the following on a real board:

- real probe connectivity
- real UART capture
- real ELF symbol resolution
- real startup fault observation
- real diagnosis output aligned with the board state

This is enough to claim a real MVP for the first narrow product promise:

`mcudbg can help AI diagnose a real embedded board startup fault through probe + log + ELF context.`

## Known Gaps

The MVP is validated, but still narrow.

Current limitations:

- validation is on one board and one main fault scenario
- probe target currently uses generic `cortex_m`
- fault address interpretation still needs refinement for fields such as `MMFAR` and `BFAR`
- the build/flash loop is not yet part of `v0.1`
- broader instrument access such as voltage, GPIO, and waveform capture is not yet included

## Recommended Next Step

The highest-value next step is not expanding scope immediately.

The next step should be:

- package this validation into public-facing proof

That means turning this result into:

- a README validation section
- a launch post with real logs and diagnosis output
- a short demo recording showing `connect_with_config -> log_tail -> diagnose_hardfault`
