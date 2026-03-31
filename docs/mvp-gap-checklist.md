# MVP Gap Checklist

This document answers one question:

**What is still missing before `mcudbg` becomes a real validated MVP?**

Current status:

- product direction is defined
- repository skeleton exists
- diagnosis tools are shaped
- mock demo exists
- STM32L4 sample project has been adapted for the demo scenario

So the remaining work is no longer “what should we build?”

The remaining work is:

**what is the shortest path to a real board-validated loop?**

---

## 1. MVP Definition

For the current phase, `mcudbg` counts as a validated MVP only if all of these are true:

1. the STM32L4 board runs the intended demo firmware
2. UART logs can be read reliably
3. a `pyOCD`-supported probe can attach reliably
4. `mcudbg` can load the matching ELF
5. `diagnose_startup_failure()` returns a sensible result on the real board
6. `diagnose_hardfault()` returns a sensible result on the real board
7. the whole flow can be repeated more than once

If one of these is missing, you still have a strong prototype, but not a fully validated MVP.

---

## 2. What You Already Have

These pieces are already in place:

1. product positioning
2. MVP scope and launch documents
3. independent `mcudbg` git repository
4. MCP server skeleton
5. `pyOCD` probe backend scaffold
6. `UART` log backend scaffold
7. ELF loading scaffold
8. `diagnose_startup_failure`
9. `diagnose_hardfault`
10. mock demo flow
11. STM32L4 hardware and MCP usage docs
12. demo firmware scenario in the STM32L4 sample project

That means the remaining gap is mostly integration and validation.

---

## 3. Minimum Remaining Actions

These are the minimum actions still required.

### A. Rebuild the STM32L4 firmware

You need to confirm the modified [main.c](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/main.c) is actually built into the current image.

Success means:

1. a fresh `.axf` is generated
2. the modified log sequence is present at runtime
3. the intentional fault really occurs after `sensor init...`

### B. Flash the board

You need the board to run the matching image.

Success means:

1. the board is definitely running the modified demo firmware
2. the flashed image matches the `.axf` you will load in `mcudbg`

### C. Verify UART manually

Before `mcudbg`, verify with a serial tool.

Success means you can see:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
```

### D. Verify probe manually

Before relying on diagnosis tools, verify:

1. the `pyOCD` probe path attaches
2. target can be halted
3. `PC/LR/SP` can be read

### E. Run the mcudbg configuration flow

Use the documented MCP flow:

1. `load_demo_profile("stm32l4_atk_led_demo")`
2. `configure_target(uart_port="COMx")`
3. `connect_with_config()`

Success means:

1. probe connects
2. UART connects
3. ELF loads

### F. Run real diagnosis

You need both of these to produce believable real-board results:

1. `diagnose_startup_failure()`
2. `diagnose_hardfault()`

Success means:

1. startup diagnosis identifies the correct stage
2. hardfault diagnosis reports plausible fault context
3. symbol resolution matches the actual board firmware

### G. Repeat once more

This is important.

Do not stop after one successful run.

Repeat the whole loop at least once more.

Success means:

1. same logs appear
2. same fault behavior appears
3. diagnosis results stay consistent

That is the difference between “lucky once” and “valid MVP”.

---

## 4. The Shortest Path From Here

If you want the absolute shortest path, do exactly this:

1. rebuild `ATK_LED`
2. flash the board
3. open a serial terminal and confirm the expected logs
4. connect `ST-Link` through the `pyOCD` path and confirm manual attach
5. run:

```text
load_demo_profile("stm32l4_atk_led_demo")
configure_target(uart_port="COM5")
connect_with_config()
log_tail(20)
diagnose_startup_failure()
diagnose_hardfault()
```

6. repeat the same sequence one more time

If that works, you have a real MVP.

---

## 5. What Is Not Required Yet

Do not delay MVP validation for these:

1. build automation
2. flash automation
3. richer UI
4. more hardware support
5. more probes
6. better branding
7. more docs

These are valuable later, but none of them are required to validate the first board-debugging loop.

---

## 6. Biggest Risks Still Remaining

The biggest remaining risks are not product-strategy risks anymore.

They are integration risks:

1. modified firmware not really flashed
2. UART port mismatch
3. probe attach instability
4. ELF and board image mismatch
5. diagnosis output not matching real fault state

That is good news.

It means the project has moved out of abstract planning and into concrete validation.

---

## 7. Exit Condition

You should consider the MVP validated when you can truthfully say:

**On a real STM32L4 board, mcudbg can combine a pyOCD-supported probe, UART, and ELF context to diagnose a reproducible startup-stage HardFault.**

That sentence is your current finish line.
