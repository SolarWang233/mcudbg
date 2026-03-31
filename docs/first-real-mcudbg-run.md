# First Real mcudbg Run

This is the shortest practical checklist for the first real-board `mcudbg` run.

Current target path:

- board: `STM32L496VETx`
- probe runtime: `pyOCD`
- real probe: `ST-Link`
- log: `UART`
- ELF: [ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)

Goal:

**Use `mcudbg` to read the same real fault state that has already been confirmed by UART and Keil.**

---

## 1. Before You Start

Do these first:

1. board is powered
2. `ST-Link` is connected
3. UART adapter is connected
4. you know the correct `COM` port
5. the modified firmware is already flashed

You should already have confirmed:

1. UART logs appear
2. board enters `HardFault`
3. `ST-Link` can attach in `Keil`

If not, stop and fix that first.

---

## 2. The Expected Board State

Before using `mcudbg`, your board should behave like this:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...

[HardFault]
...
```

If the board is not in that state, your diagnosis run will not match the current expected result.

---

## 3. What You Need Open

For this first run, you typically need:

1. your MCP client
2. the board connected through `ST-Link`
3. the UART connection physically present

Optional:

1. keep `Keil` available for cross-checking
2. keep a serial terminal available for comparison

You do **not** need to open `PowerShell` or `cmd` just to follow the MCP calls below.

---

## 4. First Call Sequence

Run these in order.

### Step 1

```text
list_demo_profiles()
```

Expected:

You should see the built-in profile:

`stm32l4_atk_led_demo`

### Step 2

```text
load_demo_profile("stm32l4_atk_led_demo")
```

Expected:

The runtime config should now contain:

1. target `cortex_m`
2. UART baudrate `115200`
3. ELF path pointing to `ATK_LED.axf`
4. suspected stage `sensor init`

### Step 3

Replace the UART port with your real one:

```text
configure_target(uart_port="COM5")
```

If your port is different, use that instead.

### Step 4

```text
get_runtime_config()
```

Check:

1. target is correct
2. UART port is correct
3. ELF path is correct
4. active profile is `stm32l4_atk_led_demo`

### Step 5

```text
connect_with_config()
```

Expected:

1. probe connects
2. UART connects
3. ELF loads

This should return `ok` or a very obvious `partial`.

If it returns `partial`, read the `missing` field carefully.

### Step 6

```text
log_tail(20)
```

Expected:

You should see something close to:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
```

Depending on timing, you may or may not catch the earlier lines on the first try.

### Step 7

```text
diagnose_startup_failure()
```

What a good result looks like:

1. identifies startup failure around `sensor init`
2. says the log stopped there
3. recognizes that a fault condition exists

### Step 8

```text
diagnose_hardfault()
```

What a good result looks like:

1. identifies a `HardFault`
2. reports `instruction_access_violation` or a similarly close classification
3. shows the fault escalated into `HardFault`
4. gives startup-stage evidence and reasonable next steps

---

## 5. The Entire First Run In One Block

This is the exact shortest sequence to keep next to you:

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

---

## 6. If Something Fails

### If `connect_with_config()` fails

Check:

1. `ST-Link` is free and not held by another tool
2. board is powered
3. UART port is correct
4. ELF path exists

### If `log_tail()` shows nothing

Check:

1. UART port is correct
2. another serial tool is not holding the port
3. board was reset after the UART connection became active

### If diagnosis output looks wrong

Check:

1. board image matches the ELF
2. current firmware is the modified HardFault demo build
3. `Keil` still sees the same fault state manually

---

## 7. What To Save From The First Run

After your first real successful run, save:

1. the `log_tail()` result
2. the `diagnose_startup_failure()` result
3. the `diagnose_hardfault()` result
4. the UART `COM` port used
5. the exact ELF path used

These are the raw materials for:

1. README screenshots
2. launch article examples
3. future regression checks

---

## 8. Success Condition

This first run is successful if:

1. `mcudbg` connects to the real board
2. `mcudbg` reads the UART evidence
3. `mcudbg` reports a startup-stage fault
4. the result is directionally consistent with what you already confirmed in UART and Keil

That is enough to treat the real-board MVP loop as proven.
