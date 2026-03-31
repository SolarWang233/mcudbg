# ST-Link Attach Checklist

This checklist is for the first real attach test with:

- board: `STM32L496VETx`
- probe: `ST-Link`
- transport: `SWD`
- project: [ATK_LED.uvprojx](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/ATK_LED.uvprojx)

Goal:

**attach to the running target, halt it, and confirm that registers can be read.**

---

## 1. What “attach” means

Here, `attach` means:

1. connect to the target without assuming a fresh reset cycle
2. attach to the currently running firmware
3. halt the CPU when needed
4. inspect `PC / LR / SP` and later fault state

For `mcudbg`, attach is important because the board may already be in the failure state when AI starts inspecting it.

---

## 2. What you need before starting

Hardware:

1. `STM32L496VETx` board
2. `ST-Link`
3. jumper wires
4. board power

Recommended wiring:

1. `SWDIO`
2. `SWCLK`
3. `GND`
4. `VTref`
5. `NRST` recommended

Minimum success condition:

1. the board is powered
2. `ST-Link` can see target voltage
3. `SWD` lines are connected correctly

---

## 3. Step 1: Check wiring

Do this physically first. No software yet.

Verify:

1. `ST-Link SWDIO -> target SWDIO`
2. `ST-Link SWCLK -> target SWCLK`
3. `ST-Link GND -> target GND`
4. `ST-Link VTref -> target VTref / target voltage sense`
5. `ST-Link NRST -> target NRST` if available

If any of these are missing or wrong, attach may fail or be unstable.

---

## 4. Step 2: Confirm the board is powered

No terminal needed yet.

Confirm:

1. board power LED is on
2. target is not held in reset
3. UART or LEDs show the board is alive

If the target has no power, attach will fail no matter what tool you use.

---

## 5. Step 3: First attach test in Keil

This step uses:

- `Keil uVision`

You do **not** need `cmd` or `PowerShell` for this step.

Steps:

1. Open [ATK_LED.uvprojx](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/USER/ATK_LED.uvprojx) in `Keil`
2. Open `Options for Target`
3. Go to the `Debug` tab
4. Select `ST-Link Debugger`
5. Make sure interface is `SWD`
6. Start a debug session

Success means:

1. Keil enters debug mode
2. target is visible
3. you can pause execution
4. you can inspect registers

If Keil cannot attach, stop here and fix this first.  
Do not blame `mcudbg` yet.

---

## 6. Step 4: Halt the CPU in Keil

Still inside `Keil`.

After entering debug mode:

1. click `Stop`
2. inspect CPU registers
3. confirm `PC`, `LR`, and `SP` are readable

Expected result:

1. CPU halts
2. register window shows valid values

If Keil can halt and read registers, your hardware path is basically good.

---

## 7. Step 5: Confirm the expected failure shape

This step can use:

- serial terminal
- `Keil`

No `PowerShell` required yet unless you want to use CLI tools.

Expected runtime behavior for the current demo firmware:

```text
boot start
clock init ok
uart init ok
led init ok
sensor init...
```

Then:

1. no more startup progress logs
2. target should be in a fault path

If this pattern does not happen, attach may still work, but your diagnosis demo state is not ready yet.

---

## 8. Step 6: Optional CLI probe test

This step uses:

- `PowerShell` or `cmd`

Only do this if:

1. you already have `pyocd` installed
2. you want to test the same runtime path that `mcudbg` will use

Recommended commands:

```powershell
pyocd list
```

and later:

```powershell
pyocd commander --target stm32l496ve
```

What this helps confirm:

1. `ST-Link` is visible to `pyOCD`
2. the target name is accepted
3. you can talk to the board outside Keil

If you do not have `pyocd` installed yet, skip this step for now.

---

## 9. Step 7: mcudbg attach flow

This step depends on your MCP client environment.

Conceptually, the attach path in `mcudbg` is:

```text
load_demo_profile("stm32l4_atk_led_demo")
configure_target(uart_port="COMx")
connect_with_config()
probe_halt()
probe_read_registers()
diagnose_startup_failure()
diagnose_hardfault()
```

Meaning of each step:

1. load the built-in profile
2. override the machine-local UART port
3. connect probe + UART + ELF
4. halt target
5. read registers
6. inspect startup failure
7. inspect hardfault

---

## 10. If you need to open PowerShell or cmd

Use `PowerShell` or `cmd` only for CLI-style checks such as:

1. `pyocd list`
2. `pyocd commander`
3. future build / flash commands

You do **not** need `PowerShell` or `cmd` just to prove that `ST-Link` can attach.  
The simplest first proof is still `Keil`.

Recommended order:

1. first prove attach in `Keil`
2. then use `PowerShell` for `pyOCD` checks if needed
3. then use `mcudbg`

---

## 11. Most common attach failures

### Failure 1: Keil cannot enter debug

Check:

1. wrong `SWD` wiring
2. missing ground
3. board not powered
4. wrong debug interface selected

### Failure 2: Target is detected but halt fails

Check:

1. target is constantly resetting
2. power is unstable
3. `NRST` wiring is missing when needed

### Failure 3: Registers look invalid

Check:

1. attach did not really succeed
2. wrong target selected
3. target power / reference voltage is unstable

### Failure 4: pyOCD cannot see ST-Link

Check:

1. `pyocd` installation
2. ST-Link driver environment
3. whether another tool is holding the probe

---

## 12. Fastest practical path

If you want the fastest route, do exactly this:

1. wire `ST-Link`
2. power the board
3. open `Keil`
4. attach with `ST-Link Debugger`
5. halt CPU
6. read `PC/LR/SP`
7. confirm UART logs stop at `sensor init...`
8. only after that, move to `mcudbg`

That is the shortest and safest path to your first real attach validation.
