# Final MCP Config Template

This is the final Windows MCP config template for the current local `mcudbg` setup.

Use this when registering the `mcudbg` server in your MCP client.

Current local facts:

- repository: [mcudbg](/d:/embed-mcp/mcudbg)
- virtualenv python: `d:\embed-mcp\mcudbg\.venv\Scripts\python.exe`
- server entry: `python -m mcudbg`

---

## Recommended Config

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "d:\\embed-mcp\\mcudbg\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcudbg"],
      "cwd": "d:\\embed-mcp\\mcudbg"
    }
  }
}
```

This is the most stable version because it:

1. does not rely on system `python`
2. does not rely on `py`
3. uses the exact virtualenv already prepared for `mcudbg`

---

## After Registration

Once the MCP client loads this server successfully, the first real run should be:

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

Replace `COM5` with your actual UART port.

---

## Expected Runtime Notes

For the current bring-up path:

1. built-in profile uses `cortex_m` as the probe target
2. probe runtime is `pyOCD`
3. real hardware probe is `ST-Link`
4. log backend is `UART`
5. ELF points to [ATK_LED.axf](/d:/embed-mcp/实验1%20跑马灯(RGB)实验/OBJ/ATK_LED.axf)

This is intentional and matches the current real-world validated path on this machine.

---

## If The MCP Client Cannot Start mcudbg

Check:

1. the path `d:\embed-mcp\mcudbg\.venv\Scripts\python.exe` exists
2. the working directory is `d:\embed-mcp\mcudbg`
3. the MCP client supports `cwd`

If `cwd` is not supported, keep the same `command` and `args`, but make sure the environment still has access to the installed editable package.

---

## If The Server Starts But Real Calls Fail

Check these separately:

1. `pyocd list` can see `ST-Link`
2. board is powered
3. UART `COM` port is correct
4. board firmware matches the loaded ELF

At this point, those are more likely failure points than the MCP config itself.
