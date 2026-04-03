# mcudbg

**Let AI debug your embedded board.**

`mcudbg` is an MCP server for embedded debugging. It gives AI assistants direct access to the things that matter on real hardware: debug probes, CPU registers, memory, ELF/DWARF symbols, UART logs, and peripheral registers.

> Human connects the wires. AI debugs the board.

## What mcudbg is for

Most AI coding tools stop at generating firmware. Real embedded failures happen after flashing:

- the board does not boot
- there is no UART output
- the firmware crashes into `HardFault`
- a peripheral is configured wrong
- execution is stuck in startup code, an ISR, or a loop

`mcudbg` is built so an AI assistant can observe the board, inspect evidence, and guide the next debugging step instead of guessing from source code alone.

## Current capabilities

### Probe and execution control

- connect to `pyOCD`-supported probes such as ST-Link and CMSIS-DAP
- halt, resume, reset, single-step, step over, and step out
- set and clear breakpoints by symbol or address
- set hardware watchpoints
- continue until an address or condition is hit
- erase, program, and verify flash ranges from MCP
- start, stop, and inspect a `pyOCD` GDB server process

### ELF and DWARF

- load ELF or AXF files for symbol resolution
- resolve addresses to function names and source lines
- source-level single step with `.debug_line`
- run directly to a source line or function
- disassemble code with source annotations
- list functions and inspect individual symbols
- read locals with DWARF debug info
- build heuristic and DWARF-based backtraces

### Memory and state inspection

- read and write target memory
- dump memory in multiple formats
- snapshot memory and diff it later
- find byte patterns in RAM
- compare ELF sections against flash contents
- inspect stopped CPU context, FPU registers, and MPU regions
- read symbol values directly from target memory

### SVD-based peripheral inspection

- load CMSIS-SVD files
- list peripherals and register layouts
- read decoded peripheral register state from hardware
- write full registers or individual fields with read-modify-write
- diagnose common peripheral issues such as clock gating or bad pin config

### Diagnosis tools

- `diagnose`
- `diagnose_hardfault`
- `diagnose_startup_failure`
- `diagnose_memory_corruption`
- `diagnose_stack_overflow`
- `diagnose_interrupt_issue`
- `diagnose_clock_issue`
- `diagnose_peripheral_stuck`

### RTOS and RTT entry points

- FreeRTOS task listing and task-context inspection
- Segger RTT log scanning and reading

These tools are implemented. They still require a matching firmware image to validate on hardware.

### Build and flash

- Keil UV4 build integration
- Keil UV4 flash integration
- combined debug loop support from MCP

## Real hardware status

The project has been exercised on real hardware, not just mocks.

Validated setup:

- target: `STM32L496VETx`
- board: `ATK_PICTURE`
- probe: `ST-Link`
- ELF: `ATK_PICTURE.axf`

Confirmed on hardware:

- ELF loading and symbol resolution
- DWARF source mapping
- `source_step`
- `run_to_function`
- `elf_symbol_info`
- `set_breakpoints_for_function_range`
- `disassemble`
- `read_memory_map`
- `probe_read_mpu_regions`
- `probe_set_watchpoint`
- `probe_remove_watchpoint`
- `probe_clear_all_watchpoints`
- `probe_read_fpu_registers`
- `erase_flash`
- `program_flash`
- `verify_flash`
- `start_gdb_server`
- `get_gdb_server_status`
- `stop_gdb_server`
- `read_rtt_log`
- `list_rtos_tasks`
- `rtos_task_context`
- `diagnose(symptom)`

Recent flash validation result on the STM32L496 board:

- `verify_flash()` matched the current image header at `0x08000000`
- a reversible scratch-sector test at `0x08010000` succeeded:
  `erase_flash()` returned all `0xFF`
  `program_flash()` wrote a 64-byte test pattern
  `verify_flash()` matched the programmed bytes
  a second `program_flash()` restored 64 bytes of `0x00`
- after the flash test, the board still booted and RTT continued to print:
  `FreeRTOS demo boot`
  `Starting scheduler`
  `RTTTask alive count=...`

Current firmware-specific gaps:

- richer RTOS scenarios beyond the current demo, such as mutex contention and ISR-to-task signaling, still benefit from more validation

Recent RTT validation result on the STM32L496 board:

- `read_rtt_log()` found the RTT control block at `0x20012b38`
- channel `0` was readable with `buffer_size = 1024`
- captured text included:
  `mcudbg RTT ready`
  `board=ATK_PICTURE target=STM32L496VETx`
  `mcudbg RTT waiting: open 0:/PICTURE`

Recent FreeRTOS validation result on the same board:

- switched the demo firmware to a minimal FreeRTOS image with `RTTTask` and `LEDTask`
- `list_rtos_tasks()` found 3 tasks:
  `RTTTask`, `LEDTask`, `IDLE`
- `rtos_task_context('LEDTask')` resolved blocked context at `vTaskDelay`
- `rtos_task_context('RTTTask')` resolved blocked context at `vTaskDelay`
- `rtos_task_context('IDLE')` returned live running registers at `prvCheckTasksWaitingTermination`

Recent richer FreeRTOS validation result on the same board:

- expanded the demo firmware to 5 application tasks plus `IDLE`
- `read_rtt_log()` captured queue and semaphore activity:
  `ProducerTask sent value=...`
  `ConsumerTask received value=...`
  `WorkerTask took semaphore`
- `list_rtos_tasks()` found 6 tasks:
  `RTTTask`, `ProducerTask`, `ConsumerTask`, `WorkerTask`, `LEDTask`, `IDLE`
- `rtos_task_context('ConsumerTask')` resolved to `xQueueGenericReceive`
- `rtos_task_context('WorkerTask')` resolved to `vTaskDelay`
- `ConsumerTask` appearing in the suspended list is expected for an indefinite wait with `portMAX_DELAY` on this FreeRTOS configuration

Recent timer-service validation result on the same board:

- enabled FreeRTOS software timers and added a periodic `DemoTimer`
- RTT now captures timer callbacks:
  `TimerCallback fired count=...`
- `list_rtos_tasks()` found 7 tasks including `Tmr Svc`
- `rtos_task_context('Tmr Svc')` resolved blocked context at `prvProcessTimerOrBlockTask`
- source resolution reached `..\FreeRTOS\timers.c:489`

Recent diagnosis-router validation result on the same board:

- `diagnose("board does not boot", include_logs=False, auto_halt=True)` routed to `diagnose_startup_failure`
- the returned symbol context included:
  `pc_symbol = prvCheckTasksWaitingTermination`
  `source = ..\FreeRTOS\tasks.c:3031`

Recent GDB server validation result on the same board:

- `start_gdb_server()` successfully launched `pyOCD gdbserver`
- `get_gdb_server_status()` reported:
  `host = 127.0.0.1`
  `port = 3333`
  `state = running`
  `target = stm32l496vetx`
- `stop_gdb_server()` shut the background process down cleanly

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

Requirements:

- Python 3.10+
- a `pyOCD`-supported debug probe
- an ELF or AXF with debug symbols for symbol-aware features
- a CMSIS-SVD file for peripheral register inspection

## MCP configuration

### Claude Desktop on Windows

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python",
      "args": ["-m", "mcudbg"],
      "cwd": "C:/path/to/mcudbg"
    }
  }
}
```

### Claude Desktop on macOS or Linux

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python3",
      "args": ["-m", "mcudbg"],
      "cwd": "/path/to/mcudbg"
    }
  }
}
```

## Quick start

### 1. Discover and connect the probe

```python
list_connected_probes()
probe_connect(target="stm32l496vetx", unique_id="YOUR_PROBE_ID")
```

### 2. Load symbols and optional SVD

```python
elf_load("D:/path/to/firmware.axf")
svd_load("D:/path/to/STM32L4x6.svd")
```

### 3. Inspect where the CPU is stopped

```python
probe_halt()
read_stopped_context()
elf_addr_to_source(0x08001234)
```

### 4. Step at source level

```python
run_to_function("main")
source_step()
step_over()
step_out()
```

### 5. Inspect peripherals and memory

```python
svd_read_peripheral("USART2")
svd_write_field("RCC", "CR", "PLLON", 1)
dump_memory(0x20000000, 64)
read_symbol_value("SystemCoreClock", 4)
```

### 6. Diagnose failures

```python
diagnose("board does not boot")
diagnose_startup_failure()
diagnose_hardfault()
diagnose_peripheral_stuck("USART2", "no output from TX pin")
diagnose_memory_corruption()
```

### 7. Erase, program, and verify flash

```python
erase_flash(start_address=0x08010000, end_address=0x08010800)
program_flash(0x08010000, [0xAA, 0x55, 0x12, 0x34], verify=True)
verify_flash(0x08010000, [0xAA, 0x55, 0x12, 0x34])
```

### 8. Start a GDB server

```python
start_gdb_server()
get_gdb_server_status()
stop_gdb_server()
```

## Tool groups

### Configuration

- `get_runtime_config`
- `list_demo_profiles`
- `load_demo_profile`
- `configure_probe`
- `configure_log`
- `configure_elf`
- `configure_build`
- `connect_with_config`

### GDB server

- `start_gdb_server`
- `stop_gdb_server`
- `get_gdb_server_status`

### Probe control and stepping

- `list_connected_probes`
- `probe_connect`
- `probe_disconnect`
- `probe_halt`
- `probe_resume`
- `probe_reset`
- `probe_step`
- `continue_target`
- `probe_continue_until`
- `step_over`
- `step_out`
- `source_step`
- `run_to_source`
- `run_to_function`

### Breakpoints and watchpoints

- `set_breakpoint`
- `set_breakpoints_for_function_range`
- `clear_breakpoint`
- `clear_all_breakpoints`
- `probe_set_watchpoint`
- `probe_remove_watchpoint`
- `probe_clear_all_watchpoints`

### Registers, memory, and state

- `probe_read_registers`
- `probe_read_fpu_registers`
- `probe_read_mpu_regions`
- `probe_read_memory`
- `probe_write_memory`
- `dump_memory`
- `memory_find`
- `memory_snapshot`
- `memory_diff`
- `read_memory_map`
- `read_stopped_context`
- `erase_flash`
- `program_flash`
- `verify_flash`

### ELF and DWARF

- `elf_load`
- `elf_addr_to_source`
- `elf_list_functions`
- `elf_symbol_info`
- `read_symbol_value`
- `write_symbol_value`
- `watch_symbol`
- `disassemble`
- `backtrace`
- `dwarf_backtrace`
- `get_locals`
- `set_local`
- `log_trace`
- `reset_and_trace`
- `compare_elf_to_flash`

### Logs, RTOS, and RTT

- `log_connect`
- `log_disconnect`
- `log_tail`
- `list_rtos_tasks`
- `rtos_task_context`
- `read_rtt_log`
- `read_stack_usage`

### SVD and peripheral diagnosis

- `svd_load`
- `svd_list_peripherals`
- `svd_get_registers`
- `svd_read_peripheral`
- `svd_write_register`
- `svd_write_field`
- `diagnose_peripheral_stuck`

### Higher-level diagnosis

- `diagnose`
- `diagnose_hardfault`
- `diagnose_startup_failure`
- `diagnose_memory_corruption`
- `diagnose_stack_overflow`
- `diagnose_interrupt_issue`
- `diagnose_clock_issue`
- `run_debug_loop`

### Build, flash, lifecycle

- `build_project`
- `flash_firmware`
- `disconnect_all`

## Known limitations

- probe backend is currently `pyOCD` only
- build and flash integration currently targets Keil UV4 on Windows
- RTT and RTOS tooling need matching firmware support to validate end to end
- some advanced DWARF features depend on debug info quality and compiler settings
- SVD files are not bundled; you provide the file for your target

## Development status

- local automated test snapshot: `73 passed`
- current work is beyond the original Phase 2 scope and well into Phase 3 debugging features
- recent additions include `diagnose(symptom)`, hardware-validated flash erase/program/verify, and a hardware-validated `GDB server` lifecycle entry point
- the next big product step is a second probe backend such as J-Link

## Contributing

Issues and PRs are welcome. Hardware validation reports are especially useful if you test on targets beyond STM32L4.

## License

MIT. See [LICENSE](LICENSE).
