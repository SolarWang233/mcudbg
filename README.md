# mcudbg

**AI-native debugging and observability for embedded boards.**

> Human connects the wires. AI debugs the board.

`mcudbg` is an [MCP](https://modelcontextprotocol.io/) server that gives AI assistants direct access to debug probes, CPU registers, memory, ELF/DWARF symbols, UART logs, SVD peripheral registers, and RTOS state on real hardware.

Most AI coding tools stop at generating firmware. `mcudbg` picks up where they leave off: when the board doesn't boot, the UART is silent, or the firmware crashes into HardFault.

<!-- TODO: replace with actual demo GIF -->
<!-- ![demo](docs/demo.gif) -->

## Quick demo

```text
User:  This board doesn't boot after power-on. Help me check.

AI:    Connecting probe, halting target, reading registers...
       PC = 0x08001A3C -> HardFault_Handler (startup.s:42)
       CFSR = 0x00008200 -> precise data bus fault
       BFAR = 0x00000000 -> null pointer dereference
       The firmware hit a null pointer during sensor_init().
       Suggestion: check the I2C handle passed to HAL_I2C_Init().
```

## Features

### Probe backends

| Backend | Status |
|---------|--------|
| pyOCD (ST-Link, CMSIS-DAP) | Fully supported |
| J-Link (via `pylink-square`) | Fully supported |

Both backends support:

- connect / disconnect
- halt / resume / reset / single-step
- breakpoints / watchpoints
- memory read / write
- flash erase / program / verify
- fault and FPU register access

### ELF and DWARF

Load ELF/AXF files for:

- symbol resolution
- source-level stepping
- disassembly with source annotations
- function listing
- local variable inspection
- backtrace

### SVD peripheral inspection

Load CMSIS-SVD files to decode peripheral registers, inspect clock gating, and diagnose misconfigured peripherals with field-level read-modify-write.

### Symptom-driven diagnosis

Tell the AI what is wrong. It decides what to inspect first.

| Tool | Use case |
|------|----------|
| `diagnose("board won't boot")` | Routes to the right diagnostic path |
| `diagnose_hardfault` | Fault register decode + PC resolution |
| `diagnose_startup_failure` | Log + execution state analysis |
| `diagnose_peripheral_stuck` | Clock gating, pin mux, enable bits |
| `diagnose_memory_corruption` | Stack overflow, buffer overrun |
| `diagnose_interrupt_issue` | NVIC priority, enable, pending |
| `diagnose_clock_issue` | PLL, HSE, system clock tree |
| `diagnose_stack_overflow` | SP vs stack bounds, canary check |

### RTOS and RTT

FreeRTOS task listing and per-task context inspection. Segger RTT log scanning and reading, including native J-Link RTT reads with RAM-scan fallback.

Hardware-validated FreeRTOS synchronization scenarios now include:

- queue send / receive
- binary semaphore handoff
- software timer (`Tmr Svc`)
- event group wait / sync
- task notify
- mutex handoff and blocked waiter inspection
- ISR-to-task notify via timer interrupt

### Build and flash

Keil UV4 build and flash integration. Full debug loop:

`diagnose -> fix code -> build -> flash -> verify`

### GDB server

Start, stop, and inspect either a pyOCD or J-Link GDB server process from MCP.

## Installation

```bash
pip install mcudbg
```

Or from source:

```bash
git clone https://github.com/SolarWang233/mcudbg
cd mcudbg
pip install -e .
```

**Requirements:** Python 3.10+, a supported debug probe, and an ELF/AXF with debug symbols.

**Optional:** CMSIS-SVD file for peripheral register decoding. J-Link backend requires `pylink-square`.

## Documentation

- [AI Playbook](docs/ai-playbook.md) - operational guidance for AI assistants using `mcudbg`
- [v0.6 Roadmap](docs/v0.6-roadmap.md) - current post-core roadmap and remaining high-value gaps
- [Support Matrix](docs/support-matrix.md) - backend, target, and hardware-validated capability coverage

## MCP configuration

### Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python",
      "args": ["-m", "mcudbg"]
    }
  }
}
```

On macOS/Linux, use `python3` instead of `python`.

## Quick start

### 1. Connect probe and load symbols

```python
list_supported_targets("pyocd")  # optional preflight support matrix
probe_connect(target="stm32l496vetx", backend="pyocd")
elf_load("firmware.axf")
svd_load("STM32L4x6.svd")  # optional
```

For J-Link:

```python
probe_connect(target="STM32F103C8", backend="jlink", unique_id="240710115")
```

### 2. Inspect where the CPU is

```python
probe_halt()
read_stopped_context()
```

### 3. Source-level debugging

```python
run_to_function("main")
source_step()
step_over()
step_out()
```

### 4. Inspect peripherals and memory

```python
svd_read_peripheral("USART2")
dump_memory(0x20000000, 64)
read_symbol_value("SystemCoreClock", 4)
```

### 5. Diagnose failures

```python
diagnose("UART2 has no output")
diagnose_hardfault()
```

### 6. Flash operations

```python
erase_flash(start_address=0x08010000, end_address=0x08010800)
program_flash(0x08010000, [0xAA, 0x55, 0x12, 0x34], verify=True)
```

## All tools (70+)

<details>
<summary>Configuration</summary>

`get_runtime_config` · `list_demo_profiles` · `load_demo_profile` · `configure_probe` · `configure_log` · `configure_elf` · `configure_build` · `connect_with_config` · `match_chip_name` · `get_target_info` · `list_supported_targets`
</details>

<details>
<summary>Probe control and stepping</summary>

`list_connected_probes` · `probe_connect` · `probe_disconnect` · `probe_halt` · `probe_resume` · `probe_reset` · `probe_step` · `continue_target` · `probe_continue_until` · `step_over` · `step_out` · `source_step` · `run_to_source` · `run_to_function`
</details>

<details>
<summary>Breakpoints and watchpoints</summary>

`set_breakpoint` · `set_breakpoints_for_function_range` · `clear_breakpoint` · `clear_all_breakpoints` · `probe_set_watchpoint` · `probe_remove_watchpoint` · `probe_clear_all_watchpoints`
</details>

<details>
<summary>Registers, memory, and state</summary>

`probe_read_registers` · `probe_read_fpu_registers` · `probe_read_mpu_regions` · `probe_read_memory` · `probe_write_memory` · `dump_memory` · `memory_find` · `memory_snapshot` · `memory_diff` · `read_memory_map` · `read_stopped_context` · `erase_flash` · `program_flash` · `verify_flash` · `read_cycle_counter` · `read_swo_log`
</details>

<details>
<summary>ELF and DWARF</summary>

`elf_load` · `elf_addr_to_source` · `elf_list_functions` · `elf_symbol_info` · `read_symbol_value` · `write_symbol_value` · `watch_symbol` · `disassemble` · `backtrace` · `dwarf_backtrace` · `get_locals` · `set_local` · `log_trace` · `reset_and_trace` · `compare_elf_to_flash`
</details>

<details>
<summary>Logs, RTOS, and RTT</summary>

`log_connect` · `log_disconnect` · `log_tail` · `list_rtos_tasks` · `rtos_task_context` · `read_rtt_log` · `read_stack_usage`
</details>

<details>
<summary>SVD and peripheral diagnosis</summary>

`svd_load` · `svd_list_peripherals` · `svd_get_registers` · `svd_read_peripheral` · `svd_write_register` · `svd_write_field` · `diagnose_peripheral_stuck`
</details>

<details>
<summary>Higher-level diagnosis</summary>

`diagnose` · `diagnose_hardfault` · `diagnose_startup_failure` · `diagnose_memory_corruption` · `diagnose_stack_overflow` · `diagnose_interrupt_issue` · `diagnose_clock_issue` · `run_debug_loop`
</details>

<details>
<summary>Build, flash, GDB, lifecycle</summary>

`build_project` · `flash_firmware` · `start_gdb_server` · `stop_gdb_server` · `get_gdb_server_status` · `start_jlink_gdb_server` · `stop_jlink_gdb_server` · `get_jlink_gdb_server_status` · `disconnect_all`
</details>

## Tested on real hardware

| Board | MCU | Probe | Capabilities verified |
|-------|-----|-------|----------------------|
| ATK_PICTURE | STM32L496VETx | ST-Link (pyOCD) | Full: ELF, DWARF, SVD, flash, RTT, RTOS, diagnosis, GDB server; FreeRTOS queue/semaphore/timer/event-group/task-notify/mutex/ISR-notify validated |
| Custom | STM32F103C8 | J-Link | Full: connect, registers, memory, watchpoints, flash erase/program/verify, J-Link GDB server, RTT, DWT cycle counter |

Recent J-Link RTT validation on `STM32F103C8`:

- Connected with `JLink_x64.dll` auto-discovery
- Detected RTT control block at `0x20004644`
- Read live channel 0 text via the J-Link backend:
  - `vTaskMsgPro alive`

For exact test snapshots and milestone-specific counts, see `PROGRESS.md`.

## Architecture

```text
AI assistant / IDE / Agent
        |
        v
     mcudbg MCP server
        |
        +-- core / session / tools / result shaping
        |
        +-- probe backends
        |    +-- pyOCD (ST-Link, CMSIS-DAP)
        |    +-- J-Link (pylink-square)
        |
        +-- UART log / RTT / SVD / ELF-DWARF / RTOS
```

Future modules:

- `mcudbg-io` (GPIO)
- `mcudbg-bench` (DMM, PSU, scope, logic analyzer)

## Known limitations

- Build/flash integration currently targets Keil UV4 on Windows.
- RTOS inspection requires FreeRTOS with matching config and symbols.
- Advanced DWARF features depend on compiler debug info quality.
- `JLinkGDBServerCL` may reject an explicit serial number on some setups; `mcudbg` falls back to auto-selected J-Link when that happens.
- SVD files are not bundled; provide the file for your target chip.
- SWO text capture remains board-dependent even when the backend path itself works.

## Contributing

Issues and PRs are welcome. Hardware validation reports on targets beyond STM32 are especially useful.

## License

MIT. See [LICENSE](LICENSE).
