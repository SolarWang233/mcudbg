# Real Board Expected Diagnosis

This document captures the expected diagnosis shape for the current real-board demo.

Board context:

- board: `STM32L496VETx`
- probe path: `pyOCD` with `ST-Link`
- log path: `UART`
- scenario: startup log stops at `sensor init...`, then the board enters `HardFault`

This file is meant to be the reference answer for comparing:

1. what the serial terminal shows
2. what Keil debug shows
3. what `mcudbg` should eventually report

---

## 1. Observed Real-Board Log

Observed UART output:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...

[HardFault]
MSP  = 0x20000738
SP[0]= 0xFFFFFFFF
SP[1]= 0x08001975
SP[2]= 0x00010B61
SP[3]= 0x00010B61
SP[4]= 0x00013880
SP[5]= 0x000003E8
SP[6]= 0x00000001
SP[7]= 0x0800273D
CFSR = 0x00000001
HFSR = 0x40000000
MMFAR= 0xE000ED34
BFAR = 0xE000ED38
SHCSR= 0x00000000
```

---

## 2. What This Means At A High Level

At a high level, the board behavior means:

1. boot is progressing normally through early startup
2. failure happens immediately after `sensor init...`
3. the target enters `HardFault`
4. the fault appears to originate from an invalid execution path
5. the event is deterministic enough to be used as the current MVP demo case

---

## 3. Expected Startup Diagnosis

This is the kind of result `diagnose_startup_failure()` should eventually produce on the real board.

### Human-readable summary

```text
Startup likely failed around sensor initialization.
UART output stops immediately after "sensor init...".
The board then enters HardFault instead of continuing normal startup.
The failure is highly likely caused by an invalid execution path triggered during startup.
```

### Expected structured interpretation

```json
{
  "status": "ok",
  "diagnosis_type": "startup_failure_with_fault",
  "summary": "Startup likely failed around sensor init, and the target shows a fault condition.",
  "confidence": "high",
  "startup_context": {
    "suspected_stage": "sensor init",
    "last_meaningful_log": "sensor init...",
    "progress_interrupted": true
  },
  "log_context": {
    "included": true,
    "last_meaningful_line": "sensor init...",
    "log_stopped_abruptly": true
  },
  "evidence": [
    "UART output stops after 'sensor init...'.",
    "The board enters HardFault immediately after the startup-stage log.",
    "Startup does not continue into normal application behavior."
  ],
  "suspected_root_causes": [
    {
      "label": "startup code fault near sensor init",
      "confidence": "high"
    },
    {
      "label": "invalid execution target or bad function pointer during initialization",
      "confidence": "high"
    }
  ]
}
```

---

## 4. Expected HardFault Diagnosis

This is the kind of result `diagnose_hardfault()` should eventually converge toward.

### Human-readable summary

```text
The target entered HardFault shortly after sensor initialization.
The fault context suggests an invalid execution path, likely caused by an illegal function entry or invalid control flow target.
The fault escalated into HardFault, and startup did not recover.
```

### Expected structured interpretation

```json
{
  "status": "ok",
  "diagnosis_type": "hardfault_detected",
  "summary": "Target entered HardFault shortly after sensor init.",
  "confidence": "high",
  "fault": {
    "fault_detected": true,
    "fault_handler_active": true,
    "fault_class": "memory_management_fault",
    "registers": {
      "msp": "0x20000738",
      "cfsr": "0x00000001",
      "hfsr": "0x40000000",
      "mmfar": "0xE000ED34",
      "bfar": "0xE000ED38",
      "shcsr": "0x00000000"
    }
  },
  "log_context": {
    "last_meaningful_line": "sensor init..."
  },
  "evidence": [
    "The last startup log line is 'sensor init...'.",
    "The board enters HardFault immediately after that point.",
    "CFSR is non-zero and indicates a memory-management class fault.",
    "HFSR indicates escalation into HardFault."
  ],
  "suspected_root_causes": [
    {
      "label": "invalid function pointer or invalid execution address",
      "confidence": "high"
    },
    {
      "label": "forced HardFault following an execution fault during startup",
      "confidence": "medium"
    }
  ],
  "suggested_next_steps": [
    "Resolve the stacked PC/LR values against the ELF symbols.",
    "Verify the exact call path that leads to the injected fault site.",
    "Confirm whether the failing control flow target is intentionally invalid or accidentally corrupted."
  ]
}
```

---

## 5. Important Interpretation Notes

These notes matter when comparing the real board with `mcudbg` output.

### Note 1

`MMFAR` and `BFAR` in the current UART dump should not automatically be treated as meaningful fault addresses.

They are currently printed unconditionally, so `mcudbg` should be careful not to over-claim what they mean.

### Note 2

The stacked values `SP[0..7]` are currently raw stack-frame values.

For `mcudbg`, these should eventually be mapped more explicitly to:

1. `R0`
2. `R1`
3. `R2`
4. `R3`
5. `R12`
6. `LR`
7. `PC`
8. `xPSR`

### Note 3

The current fault was intentionally injected.

So the ideal diagnosis should sound like:

1. technically correct
2. cautious in wording
3. evidence-based

It should not pretend to know a business-level root cause that does not exist.

---

## 6. What Counts As A Good mcudbg Result

When you compare the real run against `mcudbg`, a good first result means:

1. it correctly identifies the startup stage as `sensor init`
2. it correctly recognizes that a fault happened
3. it correctly reports that startup did not continue
4. it gives a technically plausible fault class
5. it suggests next steps that are consistent with the board evidence

It does **not** need to be perfect on the first run.

For MVP validation, the goal is:

**directionally correct, evidence-based, and consistent with the real board state**

---

## 7. Current Validation Target

Right now, this is the sentence you are trying to make true:

**On a real STM32L4 board, mcudbg can combine UART logs, probe-visible fault state, and ELF context to diagnose a reproducible startup-stage HardFault.**
