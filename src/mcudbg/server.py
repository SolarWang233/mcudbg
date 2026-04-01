from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .session import SessionState
from .tools.build import build_project as _build_project
from .tools.build import flash_firmware as _flash_firmware
from .tools.configuration import configure_target as _configure_target
from .tools.configuration import connect_with_config as _connect_with_config
from .tools.configuration import get_runtime_config as _get_runtime_config
from .tools.configuration import list_demo_profiles as _list_demo_profiles
from .tools.configuration import load_demo_profile as _load_demo_profile
from .tools.debug_loop import run_debug_loop as _run_debug_loop
from .tools.diagnose import diagnose_hardfault as _diagnose_hardfault
from .tools.diagnose import diagnose_startup_failure as _diagnose_startup_failure
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
from .tools.probe import read_registers as _read_registers
from .tools.probe import read_stopped_context as _read_stopped_context
from .tools.probe import reset_target as _reset_target
from .tools.probe import resume_target as _resume_target
from .tools.probe import set_breakpoint as _set_breakpoint

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
async def configure_target(
    target: str | None = None,
    unique_id: str | None = None,
    uart_port: str | None = None,
    uart_baudrate: int | None = None,
    elf_path: str | None = None,
    uv4_path: str | None = None,
    project_path: str | None = None,
    target_name: str | None = None,
    build_log_path: str | None = None,
    flash_log_path: str | None = None,
    suspected_stage: str | None = None,
) -> dict:
    return _configure_target(
        session,
        target=target,
        unique_id=unique_id,
        uart_port=uart_port,
        uart_baudrate=uart_baudrate,
        elf_path=elf_path,
        uv4_path=uv4_path,
        project_path=project_path,
        target_name=target_name,
        build_log_path=build_log_path,
        flash_log_path=flash_log_path,
        suspected_stage=suspected_stage,
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
