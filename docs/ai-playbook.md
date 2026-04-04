# AI Playbook

This document is a short operational guide for AI assistants using `mcudbg`.

Use it to decide:

- which tools to call first
- which preconditions must be satisfied
- how to combine probe, ELF, SVD, RTT, RTOS, and diagnosis flows
- when to stop collecting evidence and start reasoning

`mcudbg` is a structured evidence collector.  
The AI is responsible for interpretation, prioritization, and next-step decisions.

---

## 1. Core Principle

Default strategy:

1. connect to the board
2. collect broad evidence
3. narrow to the failing subsystem
4. only then perform targeted deep inspection

Prefer:

- non-destructive reads before writes
- direct evidence before speculation
- built-in diagnosis tools before manual low-level probing
- real hardware evidence over assumptions

---

## 2. Default Workflow

When the user reports a board problem and does not specify a tool sequence:

1. `probe_connect(...)`
2. `probe_halt()` or `probe_reset(halt=True)`
3. `read_stopped_context()`
4. If the symptom is broad, call `diagnose(...)`
5. If symbols are available, call `elf_load(...)`
6. If peripheral state matters, call `svd_load(...)`
7. If RTOS or logs matter, inspect `read_rtt_log()` and `list_rtos_tasks()`

Use this as the default decision tree:

- boot failure: `diagnose("board won't boot")`
- crash/hardfault: `diagnose_hardfault()`
- silent peripheral: `diagnose_peripheral_stuck(...)`
- RTOS stall: `list_rtos_tasks()` -> `rtos_task_context(...)`
- suspicious code path: `run_to_function()` / `run_to_source()` / `source_step()`

---

## 3. Preconditions Matrix

### Probe-only tools

Require:

- connected probe

Examples:

- `probe_halt`
- `probe_resume`
- `probe_reset`
- `probe_step`
- `dump_memory`
- `probe_read_registers`
- `erase_flash`
- `program_flash`
- `verify_flash`

### ELF/DWARF tools

Require:

- probe connected for live state
- `elf_load(...)` for symbol/source resolution

Examples:

- `elf_addr_to_source`
- `elf_list_functions`
- `elf_symbol_info`
- `disassemble`
- `backtrace`
- `dwarf_backtrace`
- `get_locals`
- `run_to_function`
- `run_to_source`
- `source_step`

### SVD/peripheral tools

Require:

- probe connected
- `svd_load(...)`

Examples:

- `svd_read_peripheral`
- `svd_write_register`
- `svd_write_field`
- `diagnose_peripheral_stuck`

### RTOS tools

Require:

- probe connected
- matching ELF
- FreeRTOS symbols present in the image

Examples:

- `list_rtos_tasks`
- `rtos_task_context`
- `read_stack_usage`

### RTT tools

Require:

- probe connected
- target firmware compiled with RTT support

Notes:

- `pyOCD` path may use RAM-scan fallback
- `J-Link` path now supports native RTT reads and may still fall back when needed
- finding the RTT control block is not the same as having text available immediately

### GDB server tools

Require:

- matching backend/runtime available
- target name configured

Examples:

- `start_gdb_server`
- `start_jlink_gdb_server`

---

## 4. Backend Guidance

### pyOCD

Use when:

- board is attached through ST-Link or CMSIS-DAP
- you want the most mature default backend path

Strengths:

- broad coverage
- strong STM32 workflow
- good default path for ST-Link

### J-Link

Use when:

- board is attached through J-Link
- you need J-Link-specific flows such as native RTT or J-Link GDB server

Validated capabilities:

- connect / halt / reset / continue / step
- source-level debugging
- watchpoints
- flash erase / program / verify
- J-Link GDB server
- native RTT reads

Notes:

- DLL auto-discovery is supported
- some setups may reject explicit serial selection for `JLinkGDBServerCL`
- stale local processes can block new J-Link sessions; clean shutdown matters

---

## 5. Recommended Tool Groups

### Bring-up and execution control

Use first when the board is unresponsive or you need a known stop point.

Primary tools:

- `probe_connect`
- `probe_halt`
- `probe_reset`
- `continue_target`
- `probe_step`
- `step_over`
- `step_out`
- `source_step`

### Symbol and source inspection

Use when the CPU is halted and you need to know where execution is.

Primary tools:

- `read_stopped_context`
- `elf_addr_to_source`
- `elf_symbol_info`
- `run_to_function`
- `run_to_source`
- `disassemble`
- `get_locals`

### Memory and registers

Use when validating raw state or corruption.

Primary tools:

- `probe_read_registers`
- `probe_read_memory`
- `dump_memory`
- `memory_snapshot`
- `memory_diff`
- `read_symbol_value`
- `write_symbol_value`

### Peripheral diagnosis

Use when UART/SPI/I2C/GPIO/clocking seems wrong.

Primary tools:

- `svd_read_peripheral`
- `svd_write_field`
- `diagnose_peripheral_stuck`
- `diagnose_clock_issue`

### RTOS and logs

Use when the firmware is alive but behavior is wrong.

Primary tools:

- `read_rtt_log`
- `list_rtos_tasks`
- `rtos_task_context`
- `read_stack_usage`

### Flash and recovery

Use only after non-destructive inspection unless the user is clearly asking to reflash.

Primary tools:

- `erase_flash`
- `program_flash`
- `verify_flash`
- `compare_elf_to_flash`

---

## 6. Diagnosis Patterns

### Pattern: board won't boot

1. `probe_connect`
2. `probe_reset(halt=True)`
3. `read_stopped_context`
4. `diagnose("board won't boot")`
5. If PC is in startup or a fault handler, use `backtrace` / `disassemble`

### Pattern: hardfault after reset

1. `probe_connect`
2. `probe_halt`
3. `diagnose_hardfault`
4. `backtrace` or `dwarf_backtrace`
5. `get_locals`
6. inspect fault registers and nearby memory

### Pattern: UART has no output

1. `diagnose("UART has no output")`
2. `svd_read_peripheral("USARTx")`
3. inspect GPIO alternate function / RCC enable / baud settings
4. if firmware should log, inspect `read_rtt_log()` or UART logs

### Pattern: FreeRTOS task appears stuck

1. `list_rtos_tasks`
2. `rtos_task_context(task_name=...)`
3. `read_stack_usage`
4. inspect blocked primitive:
   - queue
   - semaphore
   - timer service

### Pattern: verify J-Link RTT

1. `probe_connect(backend="jlink", ...)`
2. `read_rtt_log(channel=0)`
3. if text is empty but control block is visible, retry
4. if needed, use `scripts/jlink_rtt_smoke.py`

---

## 7. Interpretation Rules

### Treat these as evidence, not conclusions

- `status`
- `summary`
- `evidence`
- register dumps
- fault bits
- peripheral fields
- RTOS state
- RTT text

### Common interpretation tips

- `status = error` often means missing preconditions, not necessarily a broken implementation
- `source` and `symbol` usually provide the fastest next debugging branch
- `bytes_available = 0` for RTT does not prove RTT is broken
- RTOS state labels should be interpreted together with PC/source context
- `condition_skip_count` on conditional breakpoints is useful evidence of retry behavior

---

## 8. Validated Hardware Paths

The most trustworthy current paths are:

- `STM32L496VETx + ST-Link (pyOCD)`
- `STM32F103C8 + J-Link`

Validated J-Link path includes:

- source-level debug
- flash operations
- GDB server
- RTT

---

## 9. Safe Operation Rules

Prefer this order:

1. read state
2. inspect symbols/source
3. inspect peripherals/logs/RTOS
4. only then write memory, change registers, or flash

Before using temporary validation scripts:

- prefer checked-in scripts under `scripts/`
- avoid ad-hoc `python -u -` pipelines
- ensure probe disconnect happens in `finally`

If a probe session behaves strangely:

- suspect stale local processes
- clean J-Link / GDB / Python helpers before retrying

---

## 10. Suggested Companion Material

This playbook works best together with:

- `README.md` for capability overview
- `PROGRESS.md` for current verified status
- scenario demos for board-specific debugging flows

When adding a new major capability:

1. update implementation
2. add tests
3. validate on real hardware when possible
4. update `PROGRESS.md`
5. update this playbook if the default AI workflow should change
