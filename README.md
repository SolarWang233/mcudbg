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

- `CMSIS-DAP` as the probe backend
- `UART` as the log backend
- `STM32L4` as the reference target
- startup failure and hardfault diagnosis as the primary scenario

The goal of `v0.1` is to prove one thing:

**AI can already start participating in real board-level fault diagnosis.**

---

## Demo Scenario

The first demo is designed around a reproducible startup-stage failure on an `STM32L4` board.

Example flow:

1. The board boots and prints UART logs.
2. The log stops at `sensor init...`.
3. AI reads recent UART output.
4. AI connects through `CMSIS-DAP`.
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

The current repository skeleton already targets these capabilities:

- connect to target through `CMSIS-DAP`
- halt, resume, and reset target
- read core registers and fault registers
- read target memory
- connect to UART log channel
- read recent UART logs
- load ELF symbols
- diagnose hardfault
- diagnose startup failure

Current implementation lives under:

- [src/mcudbg/server.py](/d:/embed-mcp/mcudbg/src/mcudbg/server.py)
- [src/mcudbg/tools/diagnose.py](/d:/embed-mcp/mcudbg/src/mcudbg/tools/diagnose.py)
- [src/mcudbg/backends/probe/pyocd_backend.py](/d:/embed-mcp/mcudbg/src/mcudbg/backends/probe/pyocd_backend.py)
- [src/mcudbg/backends/log/uart_backend.py](/d:/embed-mcp/mcudbg/src/mcudbg/backends/log/uart_backend.py)
- [src/mcudbg/demo/demo_cli.py](/d:/embed-mcp/mcudbg/src/mcudbg/demo/demo_cli.py)

---

## MCP Tools In v0.1

The planned `v0.1` tool surface is intentionally small:

- `probe_connect`
- `probe_halt`
- `probe_resume`
- `probe_reset`
- `probe_read_registers`
- `elf_load`
- `log_connect`
- `log_tail`
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

This repository is in early development.

Right now the focus is:

- shaping the `v0.1` MCP tool interface
- implementing the `CMSIS-DAP + UART + ELF` loop
- preparing a strong first demo on `STM32L4`

Supporting documents in this workspace:

- [embedded-mcp-product-plan.md](/d:/embed-mcp/embedded-mcp-product-plan.md)
- [mcudbg-v0.1-mvp-spec.md](/d:/embed-mcp/mcudbg-v0.1-mvp-spec.md)
- [mcudbg-v0.1-demo-and-launch.md](/d:/embed-mcp/mcudbg-v0.1-demo-and-launch.md)
- [mcudbg-diagnose-hardfault-spec.md](/d:/embed-mcp/mcudbg-diagnose-hardfault-spec.md)
- [mcudbg-diagnose-startup-failure-spec.md](/d:/embed-mcp/mcudbg/mcudbg-diagnose-startup-failure-spec.md)

---

## Getting Started

The packaging skeleton is already in place, but the project is still under active build-out.

Planned local workflow:

```bash
pip install -e .
python -m mcudbg
```

Before the first public release, this README will be expanded with:

- installation steps
- MCP config example
- hardware setup guide
- demo walkthrough

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
