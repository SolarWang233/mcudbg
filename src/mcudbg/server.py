from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .session import SessionState
from .tools.build import build_project as _build_project
from .tools.build import flash_firmware as _flash_firmware
from .tools.configuration import configure_build as _configure_build
from .tools.configuration import configure_elf as _configure_elf
from .tools.configuration import configure_log as _configure_log
from .tools.configuration import configure_probe as _configure_probe
from .tools.configuration import connect_with_config as _connect_with_config
from .tools.configuration import get_runtime_config as _get_runtime_config
from .tools.configuration import list_demo_profiles as _list_demo_profiles
from .tools.configuration import load_demo_profile as _load_demo_profile
from .tools.debug_loop import run_debug_loop as _run_debug_loop
from .tools.diagnose import diagnose_hardfault as _diagnose_hardfault
from .tools.diagnose import diagnose_startup_failure as _diagnose_startup_failure
from .tools.svd import svd_load as _svd_load
from .tools.svd import svd_list_peripherals as _svd_list_peripherals
from .tools.svd import svd_get_registers as _svd_get_registers
from .tools.svd import svd_read_peripheral as _svd_read_peripheral
from .tools.phase3 import diagnose_peripheral_stuck as _diagnose_peripheral_stuck
from .tools.logs import connect_log as _connect_log
from .tools.logs import disconnect_log as _disconnect_log
from .tools.logs import tail_logs as _tail_logs
from .tools.lifecycle import disconnect_all as _disconnect_all
from .tools.probe import connect_probe as _connect_probe
from .tools.probe import continue_target as _continue_target
from .tools.probe import clear_all_breakpoints as _clear_all_breakpoints
from .tools.probe import clear_breakpoint as _clear_breakpoint
from .tools.probe import disconnect_probe as _disconnect_probe
from .tools.probe import halt_target as _halt_target
from .tools.probe import list_connected_probes as _list_connected_probes
from .tools.probe import read_registers as _read_registers
from .tools.probe import read_stopped_context as _read_stopped_context
from .tools.probe import reset_target as _reset_target
from .tools.probe import resume_target as _resume_target
from .tools.probe import set_breakpoint as _set_breakpoint
from .tools.probe import step_instruction as _step_instruction
from .tools.probe import write_memory as _write_memory

mcp = FastMCP("mcudbg")
session = SessionState()


@mcp.tool()
async def get_runtime_config() -> dict:
    return _get_runtime_config(session)


@mcp.tool()
async def list_demo_profiles() -> dict:
    return _list_demo_profiles()


@mcp.tool()
async def load_demo_profile(profile_name: str) -> dict:
    return _load_demo_profile(session, profile_name=profile_name)


@mcp.tool()
async def configure_probe(target: str | None = None, unique_id: str | None = None) -> dict:
    """Set probe connection parameters. Run list_connected_probes first to find unique_id."""
    return _configure_probe(session, target=target, unique_id=unique_id)


@mcp.tool()
async def configure_log(uart_port: str | None = None, uart_baudrate: int | None = None) -> dict:
    """Set UART log channel parameters (e.g. uart_port='COM5', uart_baudrate=115200)."""
    return _configure_log(session, uart_port=uart_port, uart_baudrate=uart_baudrate)


@mcp.tool()
async def configure_elf(elf_path: str) -> dict:
    """Set the ELF/AXF file path for symbol resolution."""
    return _configure_elf(session, elf_path=elf_path)


@mcp.tool()
async def configure_build(
    uv4_path: str | None = None,
    project_path: str | None = None,
    target_name: str | None = None,
    build_log_path: str | None = None,
    flash_log_path: str | None = None,
) -> dict:
    """Set Keil UV4 build/flash parameters. Only needed if using build_project or flash_firmware."""
    return _configure_build(
        session,
        uv4_path=uv4_path,
        project_path=project_path,
        target_name=target_name,
        build_log_path=build_log_path,
        flash_log_path=flash_log_path,
    )


@mcp.tool()
async def connect_with_config() -> dict:
    return _connect_with_config(session)


@mcp.tool()
async def run_debug_loop(
    issue_description: str,
    profile_name: str | None = None,
    build_before_debug: bool = False,
    flash_before_debug: bool = False,
    log_tail_lines: int = 30,
    suspected_stage: str | None = None,
) -> dict:
    return _run_debug_loop(
        session,
        issue_description=issue_description,
        profile_name=profile_name,
        build_before_debug=build_before_debug,
        flash_before_debug=flash_before_debug,
        log_tail_lines=log_tail_lines,
        suspected_stage=suspected_stage,
    )


@mcp.tool()
async def build_project(timeout_seconds: int = 120) -> dict:
    return _build_project(session, timeout_seconds=timeout_seconds)


@mcp.tool()
async def flash_firmware(timeout_seconds: int = 120) -> dict:
    return _flash_firmware(session, timeout_seconds=timeout_seconds)


@mcp.tool()
async def list_connected_probes() -> dict:
    """List all probes currently connected to this machine. Start here if unsure what probe to use."""
    return _list_connected_probes(session)


@mcp.tool()
async def probe_connect(target: str, unique_id: str | None = None) -> dict:
    return _connect_probe(session, target=target, unique_id=unique_id)


@mcp.tool()
async def probe_disconnect() -> dict:
    return _disconnect_probe(session)


@mcp.tool()
async def probe_halt() -> dict:
    return _halt_target(session)


@mcp.tool()
async def probe_resume() -> dict:
    return _resume_target(session)


@mcp.tool()
async def probe_reset(halt: bool = False) -> dict:
    return _reset_target(session, halt=halt)


@mcp.tool()
async def set_breakpoint(symbol: str | None = None, address: int | None = None) -> dict:
    return _set_breakpoint(session, symbol=symbol, address=address)


@mcp.tool()
async def clear_breakpoint(symbol: str | None = None, address: int | None = None) -> dict:
    return _clear_breakpoint(session, symbol=symbol, address=address)


@mcp.tool()
async def clear_all_breakpoints() -> dict:
    return _clear_all_breakpoints(session)


@mcp.tool()
async def continue_target(timeout_seconds: float = 5.0, poll_interval_ms: int = 50) -> dict:
    return _continue_target(
        session,
        timeout_seconds=timeout_seconds,
        poll_interval_ms=poll_interval_ms,
    )


@mcp.tool()
async def read_stopped_context(
    include_fault_registers: bool = True,
    include_logs: bool = False,
    log_tail_lines: int = 20,
    resolve_symbols: bool = True,
) -> dict:
    return _read_stopped_context(
        session,
        include_fault_registers=include_fault_registers,
        include_logs=include_logs,
        log_tail_lines=log_tail_lines,
        resolve_symbols=resolve_symbols,
    )


@mcp.tool()
async def probe_step() -> dict:
    """Execute one instruction and return the new PC (with symbol if ELF is loaded)."""
    return _step_instruction(session)


@mcp.tool()
async def probe_write_memory(address: int, data: list[int]) -> dict:
    """Write bytes to target memory. data is a list of integers (0-255)."""
    return _write_memory(session, address=address, data=data)


@mcp.tool()
async def probe_read_registers() -> dict:
    return _read_registers(session)


@mcp.tool()
async def elf_load(path: str) -> dict:
    return session.elf.load(path)


@mcp.tool()
async def log_connect(port: str, baudrate: int = 115200) -> dict:
    return _connect_log(session, port=port, baudrate=baudrate)


@mcp.tool()
async def log_disconnect() -> dict:
    return _disconnect_log(session)


@mcp.tool()
async def log_tail(line_count: int = 50) -> dict:
    return _tail_logs(session, line_count=line_count)


@mcp.tool()
async def disconnect_all() -> dict:
    return _disconnect_all(session)


@mcp.tool()
async def svd_load(svd_path: str) -> dict:
    """Load a CMSIS-SVD file to enable peripheral register interpretation.

    SVD files define the register map of a chip. You can find SVD files
    in your chip vendor's SDK, or at https://github.com/posborne/cmsis-svd-data
    Example: svd_load('/path/to/STM32L496.svd')
    """
    return _svd_load(session, svd_path=svd_path)


@mcp.tool()
async def svd_list_peripherals() -> dict:
    """List all peripherals in the loaded SVD (UART, SPI, I2C, GPIO, TIM, etc.)."""
    return _svd_list_peripherals(session)


@mcp.tool()
async def svd_get_registers(peripheral: str) -> dict:
    """Return the register layout for a peripheral without reading hardware.

    Useful to understand what registers and fields exist before reading values.
    Example: svd_get_registers('USART2')
    """
    return _svd_get_registers(session, peripheral=peripheral)


@mcp.tool()
async def svd_read_peripheral(peripheral: str) -> dict:
    """Read all register values for a peripheral and interpret each field.

    Combines hardware register reads with SVD field definitions to produce
    a structured, human-readable view of peripheral state.
    Requires probe connected and target halted.
    Example: svd_read_peripheral('USART2')
    """
    return _svd_read_peripheral(session, peripheral=peripheral)


@mcp.tool()
async def diagnose_peripheral_stuck(peripheral: str, symptom: str | None = None) -> dict:
    """Diagnose why a peripheral is not working.

    Reads peripheral registers (via SVD) and checks RCC clock enable.
    Common root causes: clock not enabled in RCC, wrong pin AF mode, wrong baud rate.
    Requires SVD loaded and probe connected.
    Example: diagnose_peripheral_stuck('USART2', 'no output from TX pin')
    """
    return _diagnose_peripheral_stuck(session, peripheral=peripheral, symptom=symptom)


@mcp.tool()
async def diagnose_hardfault(
    auto_halt: bool = True,
    include_logs: bool = True,
    log_tail_lines: int = 50,
    resolve_symbols: bool = True,
    include_fault_registers: bool = True,
    include_stack_snapshot: bool = True,
    stack_snapshot_bytes: int = 64,
    suspected_stage: str | None = None,
) -> dict:
    return _diagnose_hardfault(
        session,
        auto_halt=auto_halt,
        include_logs=include_logs,
        log_tail_lines=log_tail_lines,
        resolve_symbols=resolve_symbols,
        include_fault_registers=include_fault_registers,
        include_stack_snapshot=include_stack_snapshot,
        stack_snapshot_bytes=stack_snapshot_bytes,
        suspected_stage=suspected_stage,
    )


@mcp.tool()
async def diagnose_startup_failure(
    auto_halt: bool = True,
    include_logs: bool = True,
    log_tail_lines: int = 50,
    resolve_symbols: bool = True,
    suspected_stage: str | None = None,
) -> dict:
    return _diagnose_startup_failure(
        session,
        auto_halt=auto_halt,
        include_logs=include_logs,
        log_tail_lines=log_tail_lines,
        resolve_symbols=resolve_symbols,
        suspected_stage=suspected_stage,
    )


def main() -> None:
    mcp.run()
