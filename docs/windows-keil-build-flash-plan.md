# Windows Keil Build And Flash Integration Plan

This document explains how `mcudbg` can integrate firmware build and flashing on Windows.

The target context is the current `v0.1` path:

- IDE/toolchain: `Keil uVision`
- board: `STM32L4`
- probe: `CMSIS-DAP`
- log: `UART`

The goal is to answer one question clearly:

**Can AI call Keil to build, then flash firmware to the board?**

Yes. It can.  
But it should be added in phases.

---

## 1. Short Answer

On Windows, AI can automate:

1. `Keil` project build
2. build log collection
3. artifact discovery such as `.axf`, `.hex`, `.bin`
4. firmware flashing
5. board reset
6. post-flash UART and probe-based diagnosis

The practical workflow is:

`AI -> build -> flash -> reboot -> observe -> diagnose`

That is a strong direction for `mcudbg`.

---

## 2. Why This Matters

If `mcudbg` only reads logs and debug state, it is already useful.

But once AI can also build and flash, the story becomes much stronger:

1. AI edits firmware
2. AI rebuilds the project
3. AI flashes the board
4. AI checks whether the failure still exists
5. AI compares behavior before and after changes

That turns `mcudbg` from a diagnosis helper into a real embedded debug workflow layer.

---

## 3. Recommended Product Position

This capability is worth building, but not as the first core pillar of `v0.1`.

Recommended staging:

### v0.1

Focus on:

1. connect to board
2. read UART logs
3. inspect target state
4. diagnose startup failure / HardFault

### v0.2 or later

Add:

1. `build_project`
2. `flash_firmware`
3. `reset_and_verify`

Reason:

Build and flash automation is valuable, but it introduces:

1. local toolchain path variability
2. multiple build targets
3. different flash tools
4. more Windows environment dependencies
5. harder first-run troubleshooting

You want your first public demo to succeed reliably.  
That means diagnosis first, build/flash second.

---

## 4. Recommended Architecture

Do not mix this directly into probe logic.

Recommended split:

1. `mcudbg-probe`
2. `mcudbg-log`
3. `mcudbg-build`
4. `mcudbg-flash`

At the tool level, the future shape can look like:

1. `build_project`
2. `get_build_status`
3. `find_build_artifacts`
4. `flash_firmware`
5. `reset_target`
6. `run_boot_check`

That keeps the model clean:

- build is not debug
- flash is not debug
- diagnosis is not build

But the AI can orchestrate all of them.

---

## 5. Building With Keil On Windows

In practice, Windows + Keil projects are usually built through command-line invocation of `UV4.exe` or `UV5.exe`.

Typical inputs:

1. path to `.uvprojx`
2. target name
3. rebuild vs build mode

Typical outputs:

1. build success/failure
2. compiler and linker logs
3. generated `.axf`
4. generated `.hex`

AI can automate:

1. locating the Keil executable
2. invoking build
3. parsing log output
4. identifying artifact paths
5. surfacing the error summary if build fails

For your current board sample, the project file is:

[ATK_LED.uvprojx](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/ATK_LED.uvprojx)

The main expected artifact is:

[ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)

---

## 6. Flashing Options

There are multiple valid flashing paths on Windows.

### Option A: Use the same debug stack as diagnosis

Recommended for your current path:

1. build with `Keil`
2. flash with `pyocd`
3. debug with `pyocd`

Why this is good:

1. matches your `CMSIS-DAP` choice
2. keeps probe stack more unified
3. avoids binding flash to Keil GUI behavior

### Option B: Use Keil download flow

This can work, but is less attractive for `mcudbg` as a programmable layer.

Why:

1. more tied to Keil environment behavior
2. less clean as a reusable automation surface

### Option C: Use vendor CLI tools

Examples:

1. `STM32_Programmer_CLI`
2. `JLinkExe`
3. OpenOCD

This is useful later when you broaden hardware support.

For now, your best fit is:

**Keil for build, pyOCD for flash and debug**

---

## 7. Recommended v0.2 Tool Set

If you add build/flash next, this is a good first tool set:

### `build_project`

Purpose:

Build a Keil project and return a structured result.

Suggested input:

```json
{
  "project_path": "d:\\embed-mcp\\实验1 跑马灯(RGB)实验\\USER\\ATK_LED.uvprojx",
  "target_name": "ATK_LED",
  "mode": "rebuild"
}
```

Suggested output:

1. `status`
2. `summary`
3. `exit_code`
4. `target_name`
5. `artifacts`
6. `errors`
7. `warnings`

### `find_build_artifacts`

Purpose:

Locate `.axf`, `.hex`, `.bin` after build.

### `flash_firmware`

Purpose:

Flash a given artifact to the board.

Suggested input:

```json
{
  "artifact_path": "d:\\embed-mcp\\实验1 跑马灯(RGB)实验\\OBJ\\ATK_LED.axf",
  "flash_backend": "pyocd",
  "target": "stm32l496ve"
}
```

### `reset_and_verify`

Purpose:

Reset the target and optionally validate that logs appear.

---

## 8. Recommended End-To-End Flow

This is the future workflow you should aim for:

1. AI edits firmware source
2. `build_project()`
3. `find_build_artifacts()`
4. `flash_firmware()`
5. `connect_with_config()`
6. `log_tail()`
7. `diagnose_startup_failure()`
8. `diagnose_hardfault()`

That gives you a full loop:

**change -> build -> flash -> observe -> diagnose**

---

## 9. What To Avoid In The First Version

Do not start with:

1. many build systems at once
2. many flash backends at once
3. generic “build anything” abstractions
4. UI-heavy orchestration

Do start with:

1. one Keil project
2. one target
3. one flash backend
4. one known board
5. one known fault scenario

The first build/flash loop should be just as narrow as your first diagnosis loop.

---

## 10. Windows-Specific Reality

On Windows, this feature is especially realistic because:

1. Keil is already widely used
2. many teams keep `.uvprojx` in source trees
3. build artifacts are predictable
4. local automation through shell commands is practical

But you should expect these first-run issues:

1. `Keil` install path differs by machine
2. license/toolchain availability differs by machine
3. some users build with `armcc`, others with `armclang`
4. project target names are not always obvious
5. command-line behavior may vary by Keil version

So the first implementation should always return rich error details, not just “build failed”.

---

## 11. What This Means For Your Product Story

Once this lands, your public story upgrades from:

**AI can inspect and diagnose a board**

to:

**AI can participate in the embedded debug loop from code change to board verification**

That is a much bigger category position.

It also makes your project more defensible, because the value is no longer a single debug tool wrapper.  
It becomes workflow automation across the whole firmware-debug cycle.

---

## 12. Recommendation

Your current order should be:

1. finish the first board diagnosis demo
2. prove `CMSIS-DAP + UART + STM32L4` is stable
3. then add `Keil build + pyOCD flash`

This is the highest-probability path.

If you try to do both at once, you will make first validation harder than it needs to be.

---

## 13. Next Step

When you are ready to move this into implementation, the next most useful document is:

**`mcudbg-build-flash-v0.2-spec.md`**

That spec should define:

1. `build_project`
2. `find_build_artifacts`
3. `flash_firmware`
4. `reset_and_verify`

with explicit Windows and Keil assumptions.
