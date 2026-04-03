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
from .tools.svd import svd_write_field as _svd_write_field
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
from .tools.probe import diagnose_memory_corruption as _diagnose_memory_corruption
from .tools.probe import memory_find as _memory_find
from .tools.probe import step_n_instructions as _step_n_instructions
from .tools.probe import read_memory_map as _read_memory_map
from .tools.probe import watch_symbol as _watch_symbol
from .tools.probe import compare_elf_to_flash as _compare_elf_to_flash
from .tools.probe import log_trace as _log_trace
from .tools.probe import reset_and_trace as _reset_and_trace
from .tools.probe import read_stack_usage as _read_stack_usage
from .tools.probe import elf_list_functions as _elf_list_functions
from .tools.probe import list_rtos_tasks as _list_rtos_tasks
from .tools.probe import rtos_task_context as _rtos_task_context
from .tools.probe import read_rtt_log as _read_rtt_log
from .tools.probe import dump_memory as _dump_memory
from .tools.probe import memory_snapshot as _memory_snapshot
from .tools.probe import memory_diff as _memory_diff
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
from .tools.probe import backtrace as _backtrace
from .tools.probe import dwarf_backtrace as _dwarf_backtrace
from .tools.probe import get_locals as _get_locals
from .tools.probe import set_local as _set_local
from .tools.probe import run_to_source as _run_to_source
from .tools.probe import disassemble as _disassemble
from .tools.probe import step_out as _step_out
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
async def get_locals() -> dict:
    """Read local variables and parameters at the current PC using DWARF .debug_info.

    Resolves each variable's location (stack offset, register, or absolute address)
    and reads its current value from the target. Variables optimized out or using
    complex location expressions will have value=null.
    Requires ELF with DWARF loaded and probe connected and target halted.
    """
    return _get_locals(session)


@mcp.tool()
async def set_local(name: str, value: int) -> dict:
    """Write an integer value to a local variable by name at the current PC.

    Resolves the variable's location via DWARF .debug_info and writes the value
    to the corresponding stack address or absolute address.
    Variables in registers or with complex locations cannot be written this way.
    Requires ELF with DWARF loaded and probe connected and target halted.
    Example: set_local('count', 0)
    """
    return _set_local(session, name=name, value=value)


@mcp.tool()
async def run_to_source(file: str, line: int, timeout_seconds: float = 10.0) -> dict:
    """Run target until execution reaches a specific source file and line number.

    Looks up the address for file:line in the DWARF line table, sets a
    breakpoint there, and resumes. Matches on filename suffix so you can
    pass just the basename (e.g. 'main.c') or a full path.
    Requires ELF with DWARF loaded and probe connected.
    Example: run_to_source('main.c', 42)
    """
    return _run_to_source(session, file=file, line=line, timeout_seconds=timeout_seconds)


@mcp.tool()
async def dwarf_backtrace(max_frames: int = 16) -> dict:
    """Accurate call stack using DWARF .debug_frame CFI rules.

    For each frame, computes the Canonical Frame Address (CFA) from the CFI
    table and reads the saved return address from the stack. Falls back to LR
    for leaf functions or frames without CFI entries.
    More accurate than the heuristic backtrace(); requires ELF with .debug_frame.
    Requires probe connected and target halted.
    """
    return _dwarf_backtrace(session, max_frames=max_frames)


@mcp.tool()
async def backtrace(max_frames: int = 20, stack_scan_words: int = 64) -> dict:
    """Heuristic call stack reconstruction for Cortex-M targets.

    Frame 0 is the current PC. Frame 1 is LR (return address).
    Further frames are found by scanning the stack for addresses that
    resolve to known function symbols in the loaded ELF.
    Accuracy depends on compiler optimizations; best with -O0 or -O1.
    Requires probe connected and target halted.
    """
    return _backtrace(session, max_frames=max_frames, stack_scan_words=stack_scan_words)


@mcp.tool()
async def step_out(timeout_seconds: float = 5.0) -> dict:
    """Run until the current function returns (step out).

    Sets a breakpoint at the current LR (return address) and resumes.
    Requires probe connected and target halted.
    """
    return _step_out(session, timeout_seconds=timeout_seconds)


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
async def dump_memory(
    address: int,
    size: int = 64,
    format: str = "hex",
    columns: int = 16,
) -> dict:
    """Read and display memory in formatted form.

    format options:
      'hex'  — classic hex dump with address, hex bytes, and ASCII sidebar
      'u8'   — array of unsigned bytes
      'u16'  — array of unsigned 16-bit values (little-endian)
      'u32'  — array of unsigned 32-bit values (little-endian)
      'u64'  — array of unsigned 64-bit values (little-endian)

    columns: bytes per row for hex format (default 16).
    Requires probe connected and target halted.
    Example: dump_memory(0x20000000, 64)
    Example: dump_memory(0x20000100, 32, 'u32')
    """
    return _dump_memory(session, address=address, size=size, format=format, columns=columns)


@mcp.tool()
async def memory_find(address: int, size: int, pattern: list[int], max_results: int = 16) -> dict:
    """Search a memory region for a byte pattern.

    Returns all non-overlapping match addresses. Useful for finding magic numbers,
    string literals, or corrupted canary values in RAM.
    pattern: list of byte values, e.g. [0xDE, 0xAD, 0xBE, 0xEF]
    Example: memory_find(0x20000000, 0x10000, [0xDE, 0xAD, 0xBE, 0xEF])
    Example: memory_find(0x20000000, 0x10000, [0x53, 0x45, 0x47, 0x47, 0x45, 0x52])
    """
    return _memory_find(session, address=address, size=size, pattern=pattern, max_results=max_results)


@mcp.tool()
async def step_n_instructions(count: int = 10) -> dict:
    """Execute count assembly instructions, recording PC and symbol at each step.

    Returns a trace list. Useful for precisely tracking execution through
    small code sequences without source-level stepping.
    Maximum 100 steps per call (truncated=True if count exceeded).
    Requires probe connected and target halted.
    """
    return _step_n_instructions(session, count=count)


@mcp.tool()
async def read_memory_map() -> dict:
    """Return the Cortex-M address space layout and ELF section map.

    Always returns the fixed Cortex-M region boundaries (Code/SRAM/Peripheral etc.).
    If an ELF is loaded, also returns each section's name, VMA, and size.
    No probe connection required.
    """
    return _read_memory_map(session)


@mcp.tool()
async def watch_symbol(
    name: str,
    size: int = 4,
    timeout_seconds: float = 10.0,
    poll_interval_seconds: float = 0.1,
) -> dict:
    """Poll a symbol's value until it changes or timeout expires.

    Reads the symbol at each poll interval and returns as soon as the value differs
    from the initial read. Reports old/new values and elapsed time.
    Requires ELF loaded and probe connected.
    Example: watch_symbol('g_state', 4, timeout_seconds=5.0)
    """
    return _watch_symbol(
        session, name=name, size=size,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )


@mcp.tool()
async def compare_elf_to_flash() -> dict:
    """Compare all loadable ELF sections against actual target memory.

    Reads each PROGBITS+ALLOC section from the ELF, reads the same address range
    from target memory, and reports mismatching bytes. Useful for verifying that
    flash programming completed correctly.
    Requires ELF loaded and probe connected.
    """
    return _compare_elf_to_flash(session)


@mcp.tool()
async def log_trace(max_steps: int = 200, max_lines: int = 50) -> dict:
    """Step through code and record each unique source line visited.

    Executes up to max_steps instructions, collecting distinct (file, line) pairs
    in execution order. Stops early when max_lines unique lines are reached.
    Useful for tracing execution paths through unfamiliar code.
    Requires ELF with debug info (.debug_line) and probe connected.
    """
    return _log_trace(session, max_steps=max_steps, max_lines=max_lines)


@mcp.tool()
async def reset_and_trace(max_steps: int = 200, max_lines: int = 50) -> dict:
    """Reset the target and immediately trace execution from the reset vector.

    Calls reset(halt=True) then steps through code collecting unique source lines.
    Useful for seeing the startup path (clocks, peripherals, RTOS init).
    Requires ELF with debug info and probe connected.
    """
    return _reset_and_trace(session, max_steps=max_steps, max_lines=max_lines)


@mcp.tool()
async def read_stack_usage(canary: int = 0xa5a5a5a5, task_name_len: int = 16) -> dict:
    """Scan FreeRTOS task stacks for the canary high-water mark.

    FreeRTOS fills unused stack with 0xa5 (tskSTACK_FILL_BYTE).
    Scans each task's stack from base upward and counts intact canary words.
    Reports min_free_bytes (never-used stack) and min_used_bytes per task.
    canary: fill byte pattern used at init (default 0xa5a5a5a5).
    Requires ELF loaded and probe connected with target halted.
    """
    return _read_stack_usage(session, canary=canary, task_name_len=task_name_len)


@mcp.tool()
async def elf_list_functions(name_filter: str | None = None) -> dict:
    """List all function symbols from the loaded ELF with address and size.

    name_filter: optional substring to filter function names (case-insensitive).
    Useful for finding candidate breakpoint locations without a map file.
    Example: elf_list_functions('uart')  → all UART-related functions
    Requires ELF loaded (no probe needed).
    """
    return _elf_list_functions(session, name_filter=name_filter)


@mcp.tool()
async def diagnose_memory_corruption(stack_canary: int = 0xCCCCCCCC) -> dict:
    """Scan stack and heap regions for corruption evidence.

    Reads stack bounds from ELF linker symbols (_estack / _Min_Stack_Size or __StackTop / __StackLimit),
    checks whether current SP is in bounds, scans for stack canary high-water mark,
    and samples heap boundaries for known corruption magic values.

    stack_canary: 4-byte fill pattern written to unused stack at startup (default 0xCCCCCCCC).
    Common values: 0xCCCCCCCC (Keil/IAR default), 0xDEADBEEF, 0xA5A5A5A5.
    Requires ELF loaded and probe connected.
    """
    return _diagnose_memory_corruption(session, stack_canary=stack_canary)


@mcp.tool()
async def list_rtos_tasks(max_priorities: int = 32, task_name_len: int = 16) -> dict:
    """List all FreeRTOS tasks with state, priority, and stack usage.

    Walks pxReadyTasksLists, xDelayedTaskList*, and xSuspendedTaskList to enumerate
    all tasks. Reads TCB fields: name, priority, stack base, stack top pointer.

    max_priorities: upper bound for scanning pxReadyTasksLists (default 32).
    task_name_len: configMAX_TASK_NAME_LEN in your FreeRTOS build (default 16).
    Requires ELF loaded and probe connected with target halted.
    """
    return _list_rtos_tasks(session, max_priorities=max_priorities, task_name_len=task_name_len)


@mcp.tool()
async def rtos_task_context(task_name: str, task_name_len: int = 16) -> dict:
    """Read the saved register context of a blocked or suspended FreeRTOS task.

    Parses the Cortex-M4F context switch stack frame stored in the task's TCB.
    Reconstructs R0-R12, SP, LR, PC, xPSR and resolves PC to a symbol/source line.
    Automatically detects whether FPU context was saved (EXC_RETURN bit 4).
    If the named task is currently running, returns live register values instead.

    task_name: exact task name as passed to xTaskCreate (case-sensitive).
    task_name_len: configMAX_TASK_NAME_LEN in your FreeRTOS build (default 16).
    Requires ELF loaded and probe connected with target halted.
    """
    return _rtos_task_context(session, task_name=task_name, task_name_len=task_name_len)


@mcp.tool()
async def read_rtt_log(
    channel: int = 0,
    max_bytes: int = 4096,
    search_start: int = 0x20000000,
    search_size: int = 0x50000,
) -> dict:
    """Read Segger RTT log output directly from target RAM via probe (no UART needed).

    Scans the specified RAM range for the RTT control block ('SEGGER RTT' magic),
    then reads the ring buffer of the requested up-channel.

    channel: RTT up-channel index (default 0).
    search_start: start of RAM scan (default 0x20000000).
    search_size: bytes to scan (default 0x50000 = 320 KB).
    Requires probe connected and target halted (or briefly halted to read).
    """
    return _read_rtt_log(
        session,
        channel=channel,
        max_bytes=max_bytes,
        search_start=search_start,
        search_size=search_size,
    )


@mcp.tool()
async def memory_snapshot(address: int, size: int, label: str = "default") -> dict:
    """Capture a memory region snapshot for later comparison.

    Use before an operation (step, continue, write) then call memory_diff to see what changed.
    Multiple snapshots can be stored simultaneously using different labels.
    Example: memory_snapshot(0x20000000, 256, 'before_init')
    """
    return _memory_snapshot(session, address=address, size=size, label=label)


@mcp.tool()
async def memory_diff(label: str = "default") -> dict:
    """Re-read a snapshotted memory region and return a byte-level diff.

    Returns changed_bytes (individual byte changes) and changed_regions (grouped contiguous runs).
    Call memory_snapshot first to establish a baseline.
    Example: memory_diff('before_init')
    """
    return _memory_diff(session, label=label)


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
async def svd_write_field(peripheral: str, register: str, field: str, value: int) -> dict:
    """Write a value to a single bit-field in a peripheral register (read-modify-write).

    Reads the current register value, updates only the target field bits, writes back.
    Safer than svd_write_register when you only want to change one field.
    Example: svd_write_field('RCC', 'CR', 'PLLON', 1)
    Example: svd_write_field('GPIOA', 'MODER', 'MODER5', 2)
    """
    return _svd_write_field(session, peripheral=peripheral, register=register, field=field, value=value)


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
