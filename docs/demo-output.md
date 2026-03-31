# Demo Output Reference

This document captures the expected mock-demo output for `mcudbg v0.1`.

It is meant for:

- README screenshots
- launch article examples
- terminal recording scripts
- output-shape review before hardware integration is complete

---

## Scenario

Reference setup:

- target: `STM32L4`
- probe: `CMSIS-DAP`
- log channel: `UART`
- failure pattern: startup log stops at `sensor init...`, then the target enters `HardFault`

User prompt:

```text
This STM32L4 board doesn't boot after power-on. Help me inspect it.
```

---

## Demo Flow

Suggested terminal sequence:

1. connect UART
2. connect probe
3. load ELF
4. diagnose startup failure
5. diagnose hardfault

---

## Example Output

```text
== mcudbg mock demo ==

User: This STM32L4 board doesn't boot after power-on. Help me inspect it.

[1/4] Connect UART log
{
  "status": "ok",
  "summary": "Connected mock UART on COM-MOCK at 115200 baud."
}

[2/4] Connect CMSIS-DAP probe
{
  "status": "ok",
  "summary": "Connected to mock target stm32l4 via CMSIS-DAP.",
  "backend": "mock-cmsis-dap",
  "target": "stm32l4",
  "unique_id": null
}

[3/4] Load ELF
{
  "status": "ok",
  "summary": "Loaded mock ELF symbols from firmware.elf.",
  "symbol_count": 3
}

[4/4] Diagnose startup failure
{
  "status": "ok",
  "diagnosis_type": "startup_failure_with_fault",
  "summary": "Startup likely failed around sensor init, and the target shows a fault condition.",
  "confidence": "high",
  "target_state": {
    "halted": true,
    "reason": "halted_for_analysis"
  },
  "startup_context": {
    "suspected_stage": "sensor init",
    "last_meaningful_log": "sensor init...",
    "progress_interrupted": true
  },
  "fault": {
    "fault_detected": true,
    "fault_class": "precise_data_bus_error",
    "registers": {
      "pc": "0x8001234",
      "lr": "0x8004567",
      "sp": "0x20001f80",
      "xpsr": "0x21000000",
      "cfsr": "0x8200",
      "hfsr": "0x40000000",
      "mmfar": "0x0",
      "bfar": "0x20010000",
      "shcsr": "0x70000"
    }
  },
  "symbol_context": {
    "pc_symbol": "HardFault_Handler",
    "lr_symbol": "sensor_init",
    "source": {
      "file": "src/startup_stm32l4xx.s",
      "line": 121
    }
  },
  "log_context": {
    "included": true,
    "last_lines": [
      "boot start",
      "clock init ok",
      "uart init ok",
      "sensor init..."
    ],
    "last_meaningful_line": "sensor init...",
    "log_stopped_abruptly": true
  },
  "evidence": [
    "UART output stops after 'sensor init...'.",
    "Current PC resolves to HardFault_Handler.",
    "PC=0x8001234, LR=0x8004567, SP=0x20001f80.",
    "Fault registers suggest precise_data_bus_error."
  ],
  "suspected_root_causes": [
    {
      "label": "startup code fault near sensor init",
      "confidence": "high"
    },
    {
      "label": "invalid pointer or register access during initialization",
      "confidence": "medium"
    }
  ],
  "suggested_next_steps": [
    "Inspect the initialization path around sensor init.",
    "Check the last memory or register access before the fault.",
    "Verify all init-time handles, buffers, and register addresses."
  ],
  "raw_refs": {
    "elf_loaded": true,
    "probe_backend": "cmsis-dap",
    "log_backend": "uart"
  }
}

HardFault-focused result
{
  "status": "ok",
  "diagnosis_type": "hardfault_detected",
  "summary": "Target entered HardFault shortly after sensor init.",
  "confidence": "high",
  "target_state": {
    "halted": true,
    "reason": "halted_for_analysis"
  },
  "fault": {
    "fault_detected": true,
    "fault_handler_active": true,
    "fault_class": "precise_data_bus_error",
    "fault_description": "A precise data bus fault was reported by CFSR.",
    "registers": {
      "pc": "0x8001234",
      "lr": "0x8004567",
      "sp": "0x20001f80",
      "xpsr": "0x21000000",
      "cfsr": "0x8200",
      "hfsr": "0x40000000",
      "mmfar": "0x0",
      "bfar": "0x20010000",
      "shcsr": "0x70000"
    }
  },
  "symbol_context": {
    "pc_symbol": "HardFault_Handler",
    "lr_symbol": "sensor_init",
    "source": {
      "file": "src/startup_stm32l4xx.s",
      "line": 121
    }
  },
  "log_context": {
    "included": true,
    "last_lines": [
      "boot start",
      "clock init ok",
      "uart init ok",
      "sensor init..."
    ],
    "last_meaningful_line": "sensor init...",
    "log_stopped_abruptly": true
  },
  "stack_snapshot": {
    "included": true,
    "start_address": "0x20001f80",
    "size_bytes": 64,
    "data_hex": "80 1f 00 20 34 12 00 08 67 45 00 08 aa bb cc dd 80 1f 00 20 34 12 00 08 67 45 00 08 aa bb cc dd 80 1f 00 20 34 12 00 08 67 45 00 08 aa bb cc dd 80 1f 00 20 34 12 00 08 67 45 00 08 aa bb cc dd"
  },
  "evidence": [
    "UART output stopped after 'sensor init...'.",
    "PC=0x8001234, LR=0x8004567, SP=0x20001f80.",
    "PC resolved to HardFault_Handler.",
    "CFSR=0x8200 indicates precise_data_bus_error."
  ],
  "suspected_root_causes": [
    {
      "label": "invalid pointer dereference during initialization",
      "confidence": "high"
    },
    {
      "label": "incorrect peripheral register access",
      "confidence": "medium"
    }
  ],
  "suggested_next_steps": [
    "Inspect the last memory access in the failing init path.",
    "Verify all startup handles are initialized before use.",
    "Check register base addresses used around the fault site."
  ],
  "raw_refs": {
    "elf_loaded": true,
    "probe_backend": "cmsis-dap",
    "log_backend": "uart"
  }
}
```

---

## Short Human-Readable Version

This is the compressed version that works well in README callouts or posts:

```text
UART output stops after "sensor init...".
The target is currently in HardFault_Handler.
Fault registers indicate a precise data bus fault.
The failing path is likely inside sensor initialization.
Most likely cause: invalid pointer or incorrect register access during startup.
```

---

## Screenshot Guidance

If you need a clean README screenshot, keep only these parts visible:

1. user prompt
2. UART tail
3. one-line diagnosis summary
4. one or two strongest evidence lines

Do not include the full JSON dump in the main hero screenshot.

Use the full JSON output:

- deeper in the README
- in docs
- in launch articles
- in technical explanation posts

---

## GIF Guidance

For a 15 to 30 second GIF:

1. show the user prompt
2. show the UART log stopping at `sensor init...`
3. show one line indicating `HardFault_Handler`
4. end on the diagnosis summary

Final frame suggestion:

```text
AI combined UART + CMSIS-DAP + ELF context
and located a startup-stage HardFault on STM32L4.
```
