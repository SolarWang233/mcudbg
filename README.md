# mcudbg

**Let AI debug your embedded board.**

`mcudbg` is an MCP server that gives AI assistants direct access to embedded hardware — debug probes, UART logs, ELF symbols, and peripheral registers — so AI can observe, diagnose, and help fix real board problems.

> Human connects the wires. AI debugs the board.

---

## What It Does

Most AI tools stop at writing firmware. Real embedded problems happen on the board:

- no boot log
- startup crash or hardfault
- peripheral not responding (UART, SPI, I2C, GPIO)
- firmware stuck in a loop

`mcudbg` gives AI the tools to actually investigate these problems — not just explain them from code.

```
User: "This STM32L4 board won't boot. Help me find out why."

AI: reads UART log → halts CPU → reads fault registers →
    loads ELF symbols → reads USART2 register state →
    "CR1.UE=0, transmitter disabled — UART was never initialized"
```

---

## Capabilities

### Phase 1 — Probe + Log + Fault Diagnosis
- Connect to target via `pyOCD`-supported probe (ST-Link, CMSIS-DAP, etc.)
- Halt, resume, reset, step target
- Read CPU registers and Cortex-M fault registers (CFSR, HFSR, MMFAR, BFAR)
- Read and write target memory
- Set and clear breakpoints
- Load ELF/AXF and resolve PC addresses to function names
- Connect to UART and tail logs in real time
- `diagnose_hardfault` — structured fault analysis with evidence
- `diagnose_startup_failure` — startup stage analysis

### Phase 2 — SVD Peripheral Register Inspection
- Load any CMSIS-SVD file (available in your chip vendor's SDK or Keil MDK pack)
- `svd_list_peripherals` — list all peripherals defined in the SVD
- `svd_get_registers` — inspect register layout without touching hardware
- `svd_read_peripheral` — read all register values from hardware, decoded field by field
- Automatic diagnosis for UART, SPI, I2C, GPIO peripherals

---

## Quick Example

```
# AI workflow for "UART not printing anything"

svd_load('/path/to/STM32L4x6.svd')
svd_read_peripheral('USART2')

# Returns:
# CR1 = 0x0000  [UE=0, TE=0, RE=0]
# BRR = 0x0000
# Diagnosis: "USART is disabled (CR1.UE=0). Enable with CR1.UE=1."
#            "Transmitter is disabled (CR1.TE=0). No TX output possible."
```

---

## Installation

```bash
pip install mcudbg
```

Or from source:

```bash
git clone https://github.com/SolarWang233/mcudbg
cd mcudbg
pip install -e .
```

**Requirements:**
- Python 3.10+
- A `pyOCD`-supported debug probe (ST-Link, CMSIS-DAP, J-Link via CMSIS-DAP mode)
- CMSIS-SVD file for your target chip (for peripheral register inspection)

SVD files for STM32 are included in Keil MDK (`<pack>/CMSIS/SVD/`) or available at
[cmsis-svd-data](https://github.com/posborne/cmsis-svd-data).

---

## MCP Configuration

### Claude Desktop (Windows)

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python",
      "args": ["-m", "mcudbg"],
      "cwd": "C:/path/to/mcudbg"
    }
  }
}
```

### Claude Desktop (macOS / Linux)

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python3",
      "args": ["-m", "mcudbg"],
      "cwd": "/path/to/mcudbg"
    }
  }
}
```

---

## Getting Started

### 1. Load a demo profile (optional)

```
list_demo_profiles()
load_demo_profile("stm32l4_atk_led_demo")
```

### 2. Configure manually

```
configure_probe(target="stm32l496vetx")
configure_log(uart_port="COM5", uart_baudrate=115200)
configure_elf(elf_path="/path/to/firmware.axf")
connect_with_config()
```

### 3. Diagnose a startup failure

```
log_tail(30)
diagnose_startup_failure()
```

### 4. Inspect a peripheral

```
svd_load('/path/to/STM32L4x6.svd')
svd_read_peripheral('USART2')
svd_read_peripheral('GPIOA')
```

### 5. Full hardfault investigation

```
connect_with_config()
probe_halt()
diagnose_hardfault()
svd_read_peripheral('USART1')
```

---

## MCP Tools Reference

### Configuration
| Tool | Description |
|------|-------------|
| `configure_probe` | Set probe target and unique ID |
| `configure_log` | Set UART port and baudrate |
| `configure_elf` | Set ELF/AXF file path |
| `configure_build` | Set Keil UV4 build parameters |
| `connect_with_config` | Connect all configured resources at once |
| `get_runtime_config` | Show current configuration |

### Probe Control
| Tool | Description |
|------|-------------|
| `list_connected_probes` | List all connected debug probes |
| `probe_connect` | Connect to target |
| `probe_disconnect` | Disconnect probe |
| `probe_halt` | Halt target |
| `probe_resume` | Resume target |
| `probe_reset` | Reset target |
| `probe_step` | Execute one instruction |
| `probe_read_registers` | Read all CPU registers |
| `probe_write_memory` | Write bytes to target memory |
| `continue_target` | Resume and wait for halt (with timeout) |
| `read_stopped_context` | Read registers + fault state when halted |
| `set_breakpoint` | Set breakpoint by symbol or address |
| `clear_breakpoint` | Clear a breakpoint |
| `clear_all_breakpoints` | Clear all breakpoints |

### Logs
| Tool | Description |
|------|-------------|
| `log_connect` | Connect to UART log channel |
| `log_disconnect` | Disconnect log |
| `log_tail` | Read recent log lines |

### ELF Symbols
| Tool | Description |
|------|-------------|
| `elf_load` | Load ELF/AXF for symbol resolution |

### SVD Peripheral Registers
| Tool | Description |
|------|-------------|
| `svd_load` | Load a CMSIS-SVD file |
| `svd_list_peripherals` | List all peripherals in the SVD |
| `svd_get_registers` | Get register layout (no hardware read) |
| `svd_read_peripheral` | Read register values + field decode + diagnosis |

### Diagnosis
| Tool | Description |
|------|-------------|
| `diagnose_hardfault` | Full Cortex-M hardfault analysis |
| `diagnose_startup_failure` | Startup stage analysis |
| `run_debug_loop` | AI-driven multi-step debug loop |

### Build & Flash (Keil UV4)
| Tool | Description |
|------|-------------|
| `build_project` | Build firmware via Keil UV4 |
| `flash_firmware` | Flash firmware via Keil UV4 |

### Lifecycle
| Tool | Description |
|------|-------------|
| `disconnect_all` | Cleanly disconnect all resources |

---

## Validated Hardware

| Component | Details |
|-----------|---------|
| Target | STM32L496VETx |
| Probe | ST-Link (via pyOCD) |
| Log | UART 115200 baud |
| SVD | STM32L4x6.svd (Keil STM32L4xx_DFP pack) |

Other `pyOCD`-supported targets (STM32F4, RP2040, nRF52, etc.) should work but are untested.

---

## Known Limitations

- **Probe backend**: only `pyOCD` is supported. JLink and OpenOCD backends are planned.
- **Build and flash**: `build_project` / `flash_firmware` require **Keil UV4** on Windows. Other toolchains (CMake/GCC/IAR) are planned.
- **Log channel**: only UART is supported. RTT support is planned.
- **SVD**: user must provide the SVD file for their chip. Files are not bundled.

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Probe + UART log + ELF + hardfault/startup diagnosis |
| 2 | ✅ Done | SVD peripheral register inspection and auto-diagnosis |
| 3 | Planned | Symptom-driven general diagnosis (peripheral stuck, interrupt issues, memory corruption) |
| 4 | Planned | Full closed loop — diagnose → edit code → build → flash → verify |
| 5 | Planned | DWARF deep debug — local variables, call stack |
| 6 | Planned | Board-level observation — GPIO, voltage, waveforms |

---

## Contributing

Issues and PRs are welcome.

If you test on a target other than STM32L4, please open an issue with your results — expanding validated hardware coverage is a priority.

---

## License

MIT — see [LICENSE](LICENSE)
