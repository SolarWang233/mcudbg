# MCP Usage Example

This document shows the smallest useful `mcudbg v0.1` workflow for the current real-board path:

- target: `STM32L4`
- probe runtime: `pyOCD`
- current probe: `ST-Link`
- log: `UART`
- symbol file: `ATK_LED.axf`
- scenario: startup log stops at `sensor init...`, then target enters `HardFault`

Related docs:

- [stm32l4-hardware-checklist.md](/d:/embed-mcp/mcudbg/docs/stm32l4-hardware-checklist.md)
- [demo-output.md](/d:/embed-mcp/mcudbg/docs/demo-output.md)

---

## 1. Recommended Flow

The recommended first-use flow is:

1. list available built-in profiles
2. load the `STM32L4` demo profile
3. override the `COM` port if needed
4. connect all configured resources
5. inspect recent logs
6. diagnose startup failure
7. diagnose hardfault if needed

This keeps the session simple and reproducible.

---

## 2. Built-In Demo Profile

The current built-in profile is:

`stm32l4_atk_led_demo`

It currently points to:

- target: `cortex_m`
- baudrate: `115200`
- ELF: [ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)
- suspected stage: `sensor init`

You will usually only need to override the UART port.

The use of `cortex_m` here is intentional for the current MVP bring-up, because `pyOCD`
can attach successfully with the generic Cortex-M target even though `stm32l496ve`
is not present in the built-in target list on this machine.

---

## 3. Minimal MCP Session

### Step 1: inspect profiles

```text
list_demo_profiles()
```

Expected idea:

```text
Found 1 built-in demo profile:
- stm32l4_atk_led_demo
```

### Step 2: load the STM32L4 profile

```text
load_demo_profile("stm32l4_atk_led_demo")
```

Expected effect:

1. probe target is set
2. UART baudrate is set
3. ELF path is set
4. suspected stage is set to `sensor init`

### Step 3: override local UART port

If your serial adapter is on `COM5`:

```text
configure_target(uart_port="COM5")
```

You can also override other values if needed:

```text
configure_target(
  target="stm32l496ve",
  uart_port="COM5",
  uart_baudrate=115200,
  elf_path="d:\\embed-mcp\\实验1 跑马灯(RGB)实验\\OBJ\\ATK_LED.axf",
  suspected_stage="sensor init"
)
```

### Step 4: inspect effective runtime config

```text
get_runtime_config()
```

Use this to confirm:

1. the profile is loaded
2. the UART port is correct
3. the ELF path is correct

### Step 5: connect probe, UART, and ELF in one step

```text
connect_with_config()
```

Expected outcome:

1. the configured `pyOCD` probe connects
2. UART log channel connects
3. ELF symbols load

If one item is missing, this tool should still try to connect the available ones and report a `partial` result.

---

## 4. First Debug Session

After configuration is loaded and resources are connected:

### Read recent logs

```text
log_tail(20)
```

Expected lines:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
```

### Diagnose startup failure

```text
diagnose_startup_failure()
```

Expected direction of result:

1. startup likely failed around `sensor init`
2. recent UART output stopped there
3. fault state may already be visible
4. next steps should point to the init path

### Diagnose hardfault

```text
diagnose_hardfault()
```

Expected direction of result:

1. `HardFault` is detected
2. `PC` resolves to `HardFault_Handler`
3. `LR` points back toward the startup path
4. fault class is likely reported as a data bus fault

---

## 5. End-to-End Example

This is the most useful example to keep nearby during first hardware bring-up:

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

## 6. Example Result Shape

Compressed human-readable result:

```text
UART output stops after "sensor init...".
The target is currently in HardFault_Handler.
Fault registers indicate a precise data bus fault.
The failing path is likely inside sensor initialization.
Most likely cause: invalid pointer or incorrect register access during startup.
```

For fuller example output, see:

[demo-output.md](/d:/embed-mcp/mcudbg/docs/demo-output.md)

---

## 7. When To Use Manual Tools

If the diagnosis output looks wrong, fall back to the lower-level tools:

```text
probe_read_registers()
log_tail(50)
probe_halt()
probe_reset(halt=true)
```

Use these when you need to separate:

1. wiring issues
2. UART issues
3. target attach issues
4. diagnosis logic issues

---

## 8. Most Common First-Run Adjustments

You will most likely only need to change:

1. `uart_port`
2. maybe `target`
3. maybe `elf_path` if the build output moved

Recommended pattern:

1. keep the built-in profile
2. override only the machine-local values

That makes your demo more repeatable.

---

## 9. Recommendation

For the first real hardware session:

1. manually confirm UART output first
2. manually confirm probe attach second
3. then run the MCP flow

This avoids confusing hardware setup failures with tool-design issues.
