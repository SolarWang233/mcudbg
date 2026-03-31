# GitHub Launch Kit

This document contains the first public-facing copy for the `mcudbg` GitHub repository.

Use it for:

- repository description
- repository topics
- GitHub About section
- first release notes
- launch post copy

---

## Repository Name

`mcudbg`

---

## Short Repository Description

Choose one of these depending on how much space you have.

### Option A

AI-native debugging and observability for embedded boards.

### Option B

An AI-facing debug layer for embedded boards, starting with pyOCD probe support, UART, and STM32L4 startup fault diagnosis.

### Option C

Help AI inspect logs, debug state, and startup faults on real embedded boards.

Recommended:

**Option A** for the GitHub repo description.  
**Option B** for release posts and launch copy.

---

## GitHub About Blurb

Suggested About text:

`mcudbg` is an AI-facing debugging and observability layer for embedded boards.  
The first version focuses on `pyOCD probe support + UART + STM32L4`, with startup failure and HardFault diagnosis as the main scenario.

If you want a shorter version:

`mcudbg` helps AI inspect logs, probe state, and startup faults on embedded boards.

---

## Suggested GitHub Topics

Recommended first batch:

- `mcp`
- `model-context-protocol`
- `embedded`
- `embedded-systems`
- `firmware`
- `debugging`
- `arm`
- `cortex-m`
- `stm32`
- `stm32l4`
- `pyocd`
- `uart`
- `pyocd`
- `ai-tools`
- `observability`

If you want to stay tighter for the first week, use:

- `mcp`
- `embedded`
- `firmware`
- `debugging`
- `stm32`
- `pyocd`
- `uart`
- `pyocd`

---

## Social Preview Headline

If GitHub social preview or pinned repo subtitle needs one line:

**AI should not stop at writing firmware. It should help debug the board too.**

Alternative:

**Human connects the wires. AI helps inspect what the board is doing.**

---

## First Release Title

Recommended:

**v0.1.0-alpha.1 - Initial mcudbg skeleton**

Alternative:

**v0.1.0-alpha.1 - pyOCD + UART startup diagnosis skeleton**

If you want a softer first public tag:

**v0.1.0-dev1 - First public project skeleton**

Recommended:

Use `v0.1.0-alpha.1` if you plan to share publicly soon.

---

## First Release Summary

Use this as the opening paragraph:

`mcudbg` is an AI-facing debugging and observability layer for embedded boards.

This first public cut is intentionally narrow. It focuses on a single useful loop:

- `pyOCD` as the probe runtime
- `UART` as the log backend
- `STM32L4` as the reference target
- startup failure and HardFault diagnosis as the first scenario

The goal of this release is not to be feature-complete.  
The goal is to establish the first working shape of an AI-native board debugging workflow.

---

## First Release Notes

```markdown
## mcudbg v0.1.0-alpha.1

This is the first public skeleton of `mcudbg`.

`mcudbg` is an AI-facing debugging and observability layer for embedded boards. The initial version is intentionally narrow and built around one scenario:

- `pyOCD`
- `UART`
- `STM32L4`
- startup failure / HardFault diagnosis

### Included in this release

- project skeleton with packaging and repository structure
- MCP server scaffold
- `pyocd`-based probe backend scaffold
- UART log backend scaffold
- ELF loading and symbol resolution scaffold
- `diagnose_hardfault` tool skeleton
- `diagnose_startup_failure` tool skeleton
- mock demo flow for output shaping before full hardware integration
- initial docs for MVP scope, diagnosis tools, and launch planning

### Not in scope yet

- oscilloscope integration
- multimeter integration
- power supply control
- logic analyzer integration
- broad device support
- deep DWARF inspection

### Why this shape

The first goal is to prove that AI can begin participating in real board-level debugging by combining:

- recent UART logs
- probe-visible target state
- fault registers
- ELF symbol context

That first narrow loop matters more than starting with a large tool surface.

### Current status

This release should be treated as an early public skeleton, not a production-ready debugger.

The next major step is validating the full `pyOCD + UART + STM32L4` path on real hardware and polishing the first reproducible startup-failure demo.
```

---

## Launch Post Copy

### English Version

```text
I’m building `mcudbg`, an AI-facing debugging and observability layer for embedded boards.

The first version is intentionally narrow:
- pyOCD
- UART logs
- STM32L4
- startup failure / HardFault diagnosis

The idea is simple:
AI should not stop at writing firmware. It should help debug the board too.

This first public version is still an early skeleton, but the goal is to shape a real board-debugging loop that AI can participate in.
```

### Chinese Version

```text
我在做一个叫 `mcudbg` 的项目，想把 AI 从“会写嵌入式代码”推进到“能开始调板子”。

第一版我故意收得很窄，只聚焦：
- pyOCD
- UART log
- STM32L4
- 启动异常 / HardFault 诊断

我的判断是，AI 不应该停在写 firmware，它应该开始参与真实板级调试。

现在这个版本还是很早期的骨架，但目标很明确：先把一条 AI 能参与的真实调试闭环做出来。
```

---

## Pinned Repo Intro

If you pin the repo on your GitHub profile, this short intro works well:

**mcudbg is an early attempt to build an AI-native board debugging layer for embedded systems.**

Alternative:

**Helping AI move from firmware generation to real board diagnosis.**

---

## Launch Checklist

Before making the repository public, check:

1. repository description is set
2. topics are added
3. README first screen looks clean
4. first release note is ready
5. at least one screenshot or terminal output example is prepared

---

## Recommendation

For the first public push, keep the message very stable:

1. do not oversell broad hardware support yet
2. keep repeating `pyOCD + UART + STM32L4`
3. keep repeating `startup failure / HardFault diagnosis`
4. keep repeating `AI should help debug the board too`

That repetition is what builds recognition.
