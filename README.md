# mcudbg

**AI-native debugging and observability for embedded boards**

`mcudbg` is a tool layer that helps AI observe, control, and diagnose real embedded boards.

The long-term goal is simple:

**Human connects the wires. AI helps understand what the board is doing.**

---

## Why mcudbg

AI is getting good at writing firmware.

But embedded development is rarely blocked only by source code. Real problems often happen on the board:

- no boot log
- startup crash
- hardfault
- dead loop
- wrong pin state
- unstable power rail
- bad timing on the wire

To be useful in embedded debugging, AI needs more than text context. It needs access to board-side observations and actions.

`mcudbg` is built for that layer.

---

## What It Is

`mcudbg` is not just another probe wrapper.

It is an AI-facing debugging and observability layer for embedded boards. It sits between:

- AI assistants, IDEs, and agents
- debug probes, log channels, GPIO interfaces, and lab instruments

It turns those hardware interfaces into structured, diagnosis-oriented capabilities that AI can reason over.

---

## v0.1 Focus

The first release is intentionally narrow.

`v0.1` focuses on one useful loop:

- `pyOCD` as the probe runtime
- `ST-Link` as the current real-hardware validation path
- `UART` as the log backend
- `STM32L4` as the reference target
- startup failure and hardfault diagnosis as the primary scenario

For the current first real-board validation, the built-in demo profile uses the generic
`cortex_m` target in `pyOCD`, because `STM32L496VE` is not available in the default built-in
target list on this machine.

The goal of `v0.1` is to prove one thing:

**AI can already start participating in real board-level fault diagnosis.**

---

## Demo Scenario

The first demo is designed around a reproducible startup-stage failure on an `STM32L4` board.

Example flow:

1. The board boots and prints UART logs.
2. The log stops at `sensor init...`.
3. AI reads recent UART output.
4. AI connects through a `pyOCD`-supported probe.
5. AI halts the target and reads registers and fault status.
6. AI loads ELF symbols and resolves the fault location.
7. AI reports the most likely cause and the next debugging steps.

Example user prompt:

```text
This STM32L4 board doesn't boot after power-on. Help me inspect it.
```

Example result:

```text
UART output stops after "sensor init...".
The target is currently halted in HardFault_Handler.
Fault registers indicate a precise data bus fault.
The failing path is likely inside sensor initialization.
Most likely cause: invalid pointer or incorrect register access during startup.
```

---

## Current Capabilities

The current repository already supports this first useful slice:

- connect to target through a `pyOCD`-supported probe
- halt, resume, and reset target
- explicitly disconnect probe and UART resources
- read core registers and fault registers
- read target memory
- connect to UART log channel
- read recent UART logs
- load ELF symbols
- batch-build firmware through `Keil UV4`
- batch-flash firmware through `Keil UV4`
- diagnose hardfault
- diagnose startup failure

Current implementation lives under:

- [src/mcudbg/server.py](/d:/embed-mcp/mcudbg/src/mcudbg/server.py)
- [src/mcudbg/tools/diagnose.py](/d:/embed-mcp/mcudbg/src/mcudbg/tools/diagnose.py)
- [src/mcudbg/backends/probe/pyocd_backend.py](/d:/embed-mcp/mcudbg/src/mcudbg/backends/probe/pyocd_backend.py)
- [src/mcudbg/backends/log/uart_backend.py](/d:/embed-mcp/mcudbg/src/mcudbg/backends/log/uart_backend.py)
- [src/mcudbg/build_runtime.py](/d:/embed-mcp/mcudbg/src/mcudbg/build_runtime.py)
- [src/mcudbg/tools/build.py](/d:/embed-mcp/mcudbg/src/mcudbg/tools/build.py)
- [src/mcudbg/demo/demo_cli.py](/d:/embed-mcp/mcudbg/src/mcudbg/demo/demo_cli.py)

---

## What Works Today

`mcudbg` has now been validated on a real `STM32L496VETx` board with:

- `ST-Link`
- `pyOCD`
- `UART`
- `ELF/AXF`
- `Keil UV4` batch build
- `Keil UV4` batch flash download

The currently working loop is:

1. build firmware with `build_project()`
2. flash firmware with `flash_firmware()`
3. connect probe, UART, and ELF with `connect_with_config()`
4. read real board logs with `log_tail()`
5. diagnose startup failure and hardfault with `diagnose_startup_failure()` and `diagnose_hardfault()`
6. disconnect probe and UART cleanly with `disconnect_all()`

The repository also now supports a demo-friendly recovery flow:

- faulty firmware returns `startup_failure_with_fault`
- fixed firmware returns `startup_completed_normally`

This means the project has already crossed the line from mock-only demo to real hardware validation.

---

## Real Hardware Validation

The current first real-board validation was completed on an `STM32L496VETx` startup-fault scenario.

Board-side fault sample:

- startup logs print normally
- progress reaches `sensor init...`
- firmware enters `HardFault`
- UART prints the captured fault context

Representative real UART output:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
[HardFault]
CFSR = 0x00000001
HFSR = 0x40000000
```

Representative `mcudbg` diagnosis:

- `startup_failure_with_fault`
- `hardfault_detected`
- `instruction_access_violation`
- `PC -> HardFault_Handler`

The same demo flow was then validated with a fixed firmware variant. After the repair:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
sensor init ok
app loop running
```

And the resulting diagnosis becomes:

- `startup_completed_normally`

That gives `mcudbg` a real proof loop:

`buggy firmware -> real board fault -> AI diagnosis -> fixed firmware -> real board recovery`

Supporting validation documents:

- [docs/mvp-validation-report.md](/d:/embed-mcp/mcudbg/docs/mvp-validation-report.md)
- [docs/real-board-expected-diagnosis.md](/d:/embed-mcp/mcudbg/docs/real-board-expected-diagnosis.md)
- [docs/final-demo-runbook.md](/d:/embed-mcp/mcudbg/docs/final-demo-runbook.md)

---

## MCP Tools In v0.1

The planned `v0.1` tool surface is intentionally small:

- `get_runtime_config`
- `list_demo_profiles`
- `load_demo_profile`
- `configure_target`
- `connect_with_config`
- `build_project`
- `flash_firmware`
- `probe_connect`
- `probe_disconnect`
- `probe_halt`
- `probe_resume`
- `probe_reset`
- `probe_read_registers`
- `elf_load`
- `log_connect`
- `log_disconnect`
- `log_tail`
- `disconnect_all`
- `diagnose_hardfault`
- `diagnose_startup_failure`

The design priority is not tool count. It is producing useful diagnosis results with clear evidence and next-step suggestions.

---

## Architecture Direction

`mcudbg` is planned as a modular system:

- `mcudbg-core`
- `mcudbg-probe`
- `mcudbg-log`
- `mcudbg-io`
- `mcudbg-bench`

For `v0.1`, only the first useful slice is active:

- `probe`
- `log`
- `ELF`
- diagnosis-oriented tools

Future versions can expand toward:

- GPIO state inspection
- simple board control lines
- voltage and current measurement
- waveform capture
- instrument integration

---

## Design Principles

- AI-first, not wrapper-first
- structured results, not raw dumps
- diagnosis-oriented tools, not only low-level actions
- narrow first release, broad long-term vision

This means a high-level tool like `diagnose_hardfault` matters more than exposing many isolated commands.

---

## Repository Status

This repository is still in early development, but the first real hardware loop is already working.

Right now the focus is:

- stabilizing the `build + flash + diagnose + recover` demo loop
- improving lifecycle handling around `ST-Link` and UART ownership
- packaging the first public-facing demo and launch materials

Supporting documents in this workspace:

- [embedded-mcp-product-plan.md](/d:/embed-mcp/embedded-mcp-product-plan.md)
- [mcudbg-v0.1-mvp-spec.md](/d:/embed-mcp/mcudbg-v0.1-mvp-spec.md)
- [mcudbg-v0.1-demo-and-launch.md](/d:/embed-mcp/mcudbg-v0.1-demo-and-launch.md)
- [mcudbg-diagnose-hardfault-spec.md](/d:/embed-mcp/mcudbg-diagnose-hardfault-spec.md)
- [mcudbg-diagnose-startup-failure-spec.md](/d:/embed-mcp/mcudbg/mcudbg-diagnose-startup-failure-spec.md)

Documentation index:

- [docs/README.md](/d:/embed-mcp/mcudbg/docs/README.md)
- [docs/demo-script-3min.md](/d:/embed-mcp/mcudbg/docs/demo-script-3min.md)
- [docs/final-demo-runbook.md](/d:/embed-mcp/mcudbg/docs/final-demo-runbook.md)
- [docs/recording-preflight-checklist.md](/d:/embed-mcp/mcudbg/docs/recording-preflight-checklist.md)
- [docs/screenshot-selection-guide.md](/d:/embed-mcp/mcudbg/docs/screenshot-selection-guide.md)

---

## Getting Started

The project is still under active build-out, but the first real hardware path is already executable.

Current local workflow:

```bash
pip install -e .
python -m mcudbg
```

Current configuration workflow:

1. load the built-in STM32L4 demo profile
2. override `COM` port if needed
3. build and flash if needed
4. connect probe, UART, and ELF from one runtime config

Example flow:

```text
list_demo_profiles
load_demo_profile("stm32l4_atk_led_demo")
configure_target(uart_port="COM5")
build_project()
flash_firmware()
connect_with_config()
diagnose_startup_failure()
```

For the current real-board demo loop, it is recommended to add `disconnect_all()` before and after a run:

```text
disconnect_all()
load_demo_profile("stm32l4_atk_led_demo")
build_project()
flash_firmware()
connect_with_config()
probe_reset()
log_tail(30)
diagnose_startup_failure()
disconnect_all()
```

For mock-based local output shaping, a demo CLI scaffold is included:

```bash
python -m mcudbg.demo.demo_cli
```

It uses deterministic mock probe, log, and ELF backends so the diagnosis output
can be reviewed before hardware integration is fully ready.

---

## Long-Term Vision

Today, most AI tools stop at writing firmware.

`mcudbg` is built around the idea that the next step is helping AI debug real boards:

- read logs
- inspect debug state
- inspect board signals
- inspect voltage and waveform data
- combine evidence across tools
- explain what is most likely wrong

That is the direction this project is trying to define.

---

## Closing Line

**AI should not stop at writing firmware. It should help debug the board too.**
