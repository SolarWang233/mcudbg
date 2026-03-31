# Windows MCP Config Example

This document shows how to register `mcudbg` as an MCP server on Windows.

Goal:

**make the local `mcudbg` repository callable from an MCP client so you can run the first real board workflow.**

---

## 1. Before You Configure MCP

Make sure these are true first:

1. the repository exists at [mcudbg](/d:/embed-mcp/mcudbg)
2. your board setup is already working
3. `ST-Link` attach works in `Keil`
4. UART logs are visible

This config step is only for exposing `mcudbg` to an MCP client.

---

## 2. Recommended Working Directory

Use this repository root as the working directory:

`d:\embed-mcp\mcudbg`

That is where:

1. `pyproject.toml` lives
2. `src/mcudbg` lives
3. local editable install should be run from

---

## 3. Recommended Launch Command On Windows

Because Windows Python environments vary, the most practical command forms are:

### Option A

```text
py -3 -m mcudbg
```

### Option B

```text
python -m mcudbg
```

### Option C

If installed as a script entry point:

```text
mcudbg
```

Recommended:

Start with `py -3 -m mcudbg` if your Windows machine uses the Python launcher.

---

## 4. Minimal MCP Config Example

Use a config shaped like this in your MCP client:

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "py",
      "args": ["-3", "-m", "mcudbg"],
      "cwd": "d:\\embed-mcp\\mcudbg"
    }
  }
}
```

If your MCP client does not support `cwd`, then you should install the package first and use a globally resolvable Python environment.

---

## 5. Alternative Config With python

If `python` works directly on your machine:

```json
{
  "mcpServers": {
    "mcudbg": {
      "command": "python",
      "args": ["-m", "mcudbg"],
      "cwd": "d:\\embed-mcp\\mcudbg"
    }
  }
}
```

---

## 6. Editable Install First

If you want the repository code to run directly after edits, do an editable install.

This step uses:

- `PowerShell` or `cmd`

Run from:

`d:\embed-mcp\mcudbg`

Recommended command:

```powershell
py -3 -m pip install -e .
```

Alternative:

```powershell
python -m pip install -e .
```

After that, the MCP client can usually launch `mcudbg` with `-m mcudbg`.

---

## 7. If You Need A Virtual Environment

This also uses:

- `PowerShell` or `cmd`

Example:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
py -3 -m pip install -e .
```

Then your MCP config may need to point to the virtualenv Python explicitly.

Example:

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

This is often the most stable option on Windows.

---

## 8. First Real Workflow After MCP Registration

Once the client can see the server, the first real workflow should be:

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

Replace `COM5` with your real UART port.

---

## 9. If Server Launch Fails

### If `py -3 -m mcudbg` fails

Check:

1. Python launcher is installed
2. editable install was completed
3. current environment can import `mcudbg`

### If import fails

Check:

1. you ran install from [mcudbg](/d:/embed-mcp/mcudbg)
2. dependencies are installed
3. the MCP client is using the same Python environment you installed into

### If the client starts the server but tools do not work

Check:

1. the server process is actually running in the right environment
2. `pyocd` is installed in that same environment
3. `pyserial` is installed in that same environment

---

## 10. Recommendation

For the first working Windows setup, the most stable path is usually:

1. create a virtualenv
2. install `mcudbg` editable
3. point the MCP client at that virtualenv's `python.exe`

That avoids a lot of Windows environment ambiguity.
