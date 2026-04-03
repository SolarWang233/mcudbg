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
from .tools.svd import svd_write_register as _svd_write_register
from .tools.phase3 import diagnose_clock_issue as _diagnose_clock_issue
from .tools.phase3 import diagnose_interrupt_issue as _diagnose_interrupt_issue
from .tools.phase3 import diagnose_peripheral_stuck as _diagnose_peripheral_stuck
from .tools.phase3 import diagnose_stack_overflow as _diagnose_stack_overflow
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
from .tools.probe import read_memory as _read_memory
from .tools.probe import read_fpu_registers as _read_fpu_registers
from .tools.probe import read_mpu_regions as _read_mpu_regions
from .tools.probe import read_registers as _read_registers
from .tools.probe import read_symbol_value as _read_symbol_value
from .tools.probe import read_stopped_context as _read_stopped_context
from .tools.probe import reset_target as _reset_target
from .tools.probe import resume_target as _resume_target
from .tools.probe import set_watchpoint as _set_watchpoint
from .tools.probe import remove_watchpoint as _remove_watchpoint
from .tools.probe import clear_all_watchpoints as _clear_all_watchpoints
from .tools.probe import continue_until as _continue_until
from .tools.probe import addr_to_source as _addr_to_source
from .tools.probe import set_breakpoint as _set_breakpoint
from .tools.probe import source_step as _source_step
from .tools.probe import disassemble as _disassemble
from .tools.probe import step_over as _step_over
from .tools.probe import step_instruction as _step_instruction
from .tools.probe import write_memory as _write_memory
from .tools.probe import write_symbol_value as _write_symbol_value

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
async def elf_addr_to_source(address: int) -> dict:
    """Look up the source file and line number for a given address using DWARF .debug_line.

    Returns file name, line number, and nearest function symbol.
    Requires ELF loaded with DWARF debug info.
    Example: elf_addr_to_source(0x08001234)
    """
    return _addr_to_source(session, address=address)


@mcp.tool()
async def source_step() -> dict:
    """Execute instructions until the source line changes (source-level single step).

    Uses DWARF .debug_line to detect line boundaries. Falls back to a single
    instruction step if no DWARF info is available.
    Requires ELF loaded with DWARF info and probe connected and target halted.
    """
    return _source_step(session)


@mcp.tool()
async def disassemble(address: int, count: int = 10) -> dict:
    """Disassemble Thumb/Thumb-2 instructions at the given address.

    Reads count*4 bytes from target memory and disassembles using capstone.
    Annotates each instruction with source file:line if DWARF is loaded.
    Requires probe connected and target halted.
    Example: disassemble(0x08001234, 10)
    """
    return _disassemble(session, address=address, count=count)


@mcp.tool()
async def step_over() -> dict:
    """Execute one source line, stepping OVER function calls (bl/blx).

    Disassembles the current instruction. If it is a BL/BLX call, sets a
    breakpoint at the return address and resumes, skipping the callee body.
    Otherwise falls through to source_step (step into).
    Requires probe connected and target halted.
    """
    return _step_over(session)


@mcp.tool()
async def probe_write_memory(address: int, data: list[int]) -> dict:
    """Write bytes to target memory. data is a list of integers (0-255)."""
    return _write_memory(session, address=address, data=data)


@mcp.tool()
async def probe_read_memory(address: int, size: int) -> dict:
    """Read bytes from target memory at the given address.

    Returns raw bytes plus convenience integer interpretations (u8/u16/u32 little-endian).
    Requires probe connected and target halted.
    Example: probe_read_memory(0x20000000, 4)
    """
    return _read_memory(session, address=address, size=size)


@mcp.tool()
async def read_symbol_value(name: str, size: int = 4) -> dict:
    """Read the value of a symbol (variable, linker symbol) by name from target memory.

    Resolves the symbol address via ELF, then reads 'size' bytes at that address.
    Returns raw bytes plus u8/u16/u32 interpretations (little-endian).
    Requires ELF loaded and probe connected.
    Example: read_symbol_value('g_error_count', 4)
    Example: read_symbol_value('_Min_Stack_Size', 4)
    """
    return _read_symbol_value(session, name=name, size=size)


@mcp.tool()
async def write_symbol_value(name: str, value: int, size: int = 4) -> dict:
    """Write an integer value to a symbol (variable) by name in target memory.

    Resolves the symbol address via ELF, then writes 'size' bytes (little-endian).
    Requires ELF loaded and probe connected.
    Example: write_symbol_value('g_error_count', 0, 4)
    Example: write_symbol_value('g_mode', 1, 1)
    """
    return _write_symbol_value(session, name=name, value=value, size=size)


@mcp.tool()
async def probe_set_watchpoint(
    address: int,
    size: int = 4,
    watch_type: str = 'write',
) -> dict:
    """Set a hardware data watchpoint on a memory address.

    Halts the target when the address is accessed according to watch_type.
    watch_type: 'read', 'write', or 'read_write'
    size: number of bytes to watch (1, 2, or 4; Cortex-M supports up to 4 watchpoints)
    Requires probe connected and target halted.
    Example: probe_set_watchpoint(0x20000010, 4, 'write')
    """
    return _set_watchpoint(session, address=address, size=size, watch_type=watch_type)


@mcp.tool()
async def probe_remove_watchpoint(address: int) -> dict:
    """Remove a hardware watchpoint at the given address."""
    return _remove_watchpoint(session, address=address)


@mcp.tool()
async def probe_clear_all_watchpoints() -> dict:
    """Remove all hardware watchpoints."""
    return _clear_all_watchpoints(session)


@mcp.tool()
async def probe_read_registers() -> dict:
    return _read_registers(session)


@mcp.tool()
async def probe_read_fpu_registers() -> dict:
    return _read_fpu_registers(session)


@mcp.tool()
async def probe_read_mpu_regions() -> dict:
    return _read_mpu_regions(session)


@mcp.tool()
async def probe_continue_until(
    address: int,
    condition_symbol: str | None = None,
    condition_register: str | None = None,
    condition_op: str = "eq",
    condition_value: int = 0,
    max_hits: int = 20,
    timeout_seconds: float = 5.0,
) -> dict:
    return _continue_until(
        session,
        address=address,
        condition_symbol=condition_symbol,
        condition_register=condition_register,
        condition_op=condition_op,
        condition_value=condition_value,
        max_hits=max_hits,
        timeout_seconds=timeout_seconds,
    )


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
async def svd_write_register(peripheral: str, register: str, value: int) -> dict:
    """Write a 32-bit value to a peripheral register by name using SVD addressing.

    Looks up the register address from the loaded SVD, then writes the value.
    Requires SVD loaded and probe connected.
    Example: svd_write_register('USART2', 'CR1', 0x000C)
    Example: svd_write_register('GPIOA', 'ODR', 0x0001)
    """
    return _svd_write_register(session, peripheral=peripheral, register=register, value=value)


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
async def diagnose_stack_overflow() -> dict:
    """Diagnose potential stack overflow on a Cortex-M target.

    Reads VTOR (0xE000ED08) to locate the vector table, extracts the
    initial SP from word 0, and compares it with the current SP.
    If an ELF is loaded and _Min_Stack_Size is available, reports
    remaining stack space and detects overflow.
    Requires probe connected and target halted.
    """
    return _diagnose_stack_overflow(session)


@mcp.tool()
async def diagnose_interrupt_issue() -> dict:
    return _diagnose_interrupt_issue(session)


@mcp.tool()
async def diagnose_clock_issue() -> dict:
    return _diagnose_clock_issue(session)


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
