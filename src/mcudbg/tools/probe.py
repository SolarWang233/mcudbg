from __future__ import annotations

import operator as _op
import time

from ..chip_matcher import match_chip_name as _match_chip_name
from ..device_patch_manager import resolve_device_patch as _resolve_device_patch
from ..session import SessionState

_OPS = {
    "eq": _op.eq,
    "ne": _op.ne,
    "lt": _op.lt,
    "gt": _op.gt,
    "le": _op.le,
    "ge": _op.ge,
}


def list_connected_probes(session: SessionState) -> dict:
    probes = session.probe.enumerate_probes()
    return {
        "status": "ok",
        "summary": f"Found {len(probes)} connected probe(s).",
        "probes": probes,
        "hint": "Use 'unique_id' from this list with probe_connect() to target a specific probe."
        if probes else "No probes detected. Check USB connection and driver installation.",
    }


def connect_probe(session: SessionState, target: str, unique_id: str | None = None) -> dict:
    match_result = _match_chip_name(target, backend=session.config.probe.backend)
    patch_result = _resolve_device_patch(target, backend=session.config.probe.backend)
    if hasattr(session.probe, "set_connect_hints"):
        session.probe.set_connect_hints(patch_result["connect_hints"])
    result = session.probe.connect(target=match_result["matched_target"], unique_id=unique_id)
    if result.get("status") == "ok":
        result["target_match"] = match_result
        result["target_patch"] = patch_result
        checks = patch_result.get("post_connect_checks", {})
        if checks:
            post_connect: dict[str, object] = {"checks_requested": checks}
            if checks.get("halt"):
                post_connect["halt"] = session.probe.halt()
            if checks.get("read_state"):
                post_connect["state"] = session.probe.get_state()
            if checks.get("read_core_registers"):
                try:
                    post_connect["core_registers"] = session.probe.read_core_registers()
                except Exception as exc:
                    post_connect["core_registers_error"] = str(exc)
            result["post_connect"] = post_connect
        if match_result["matched_target"] != target:
            result["summary"] = (
                result["summary"] + f" Matched target '{target}' to '{match_result['matched_target']}'."
            )
    return result


def disconnect_probe(session: SessionState) -> dict:
    return session.probe.disconnect()


def halt_target(session: SessionState) -> dict:
    return session.probe.halt()


def resume_target(session: SessionState) -> dict:
    return session.probe.resume()


def reset_target(session: SessionState, halt: bool = False) -> dict:
    return session.probe.reset(halt=halt)


def set_breakpoint(
    session: SessionState,
    symbol: str | None = None,
    address: int | None = None,
    condition_symbol: str | None = None,
    condition_register: str | None = None,
    condition_op: str = "eq",
    condition_value: int = 0,
) -> dict:
    if (condition_symbol or condition_register) and condition_op not in _OPS:
        return {
            "status": "error",
            "summary": f"Invalid condition_op '{condition_op}'. Use one of: {', '.join(sorted(_OPS))}.",
        }
    resolved_symbol = None
    resolved_address = _resolve_breakpoint_address(session, symbol=symbol, address=address)
    if symbol and session.elf.is_loaded:
        resolved_symbol = symbol

    result = session.probe.set_breakpoint(resolved_address)
    result["breakpoint"] = {
        "symbol": resolved_symbol,
        "address": hex(resolved_address),
    }

    if condition_symbol or condition_register:
        cond: dict = {
            "symbol": resolved_symbol,
            "address": hex(resolved_address),
            "condition_symbol": condition_symbol,
            "condition_register": condition_register,
            "condition_op": condition_op,
            "condition_value": condition_value,
        }
        session.conditional_breakpoints[resolved_address] = cond
        result["conditional"] = True
        result["condition"] = cond
        cond_target = f"symbol {condition_symbol}" if condition_symbol else f"register {condition_register}"
        result["summary"] = (
            f"Conditional breakpoint set at {resolved_symbol or hex(resolved_address)}: "
            f"{cond_target} {condition_op} {hex(condition_value)}."
        )
    elif resolved_symbol:
        result["summary"] = f"Breakpoint set at {resolved_symbol}."

    return result


def clear_breakpoint(
    session: SessionState,
    symbol: str | None = None,
    address: int | None = None,
) -> dict:
    resolved_address = _resolve_breakpoint_address(session, symbol=symbol, address=address)
    result = session.probe.clear_breakpoint(resolved_address)
    result["breakpoint"] = {
        "symbol": symbol,
        "address": hex(resolved_address),
    }
    session.conditional_breakpoints.pop(resolved_address, None)
    if symbol:
        result["summary"] = f"Breakpoint cleared at {symbol}."
    return result


def clear_all_breakpoints(session: SessionState) -> dict:
    if hasattr(session, "conditional_breakpoints"):
        session.conditional_breakpoints.clear()
    return session.probe.clear_all_breakpoints()


def list_conditional_breakpoints(session: SessionState) -> dict:
    entries = list(session.conditional_breakpoints.values())
    return {
        "status": "ok",
        "summary": f"{len(entries)} conditional breakpoint(s) registered.",
        "conditional_breakpoints": entries,
    }


def continue_target(
    session: SessionState,
    timeout_seconds: float = 5.0,
    poll_interval_ms: int = 50,
    max_condition_loops: int = 1000,
) -> dict:
    for loop in range(max_condition_loops):
        result = session.probe.continue_target(
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=max(poll_interval_ms, 1) / 1000.0,
        )
        pc_hex = result.get("pc")
        if pc_hex and session.elf.is_loaded:
            resolved = session.elf.resolve_address(int(pc_hex, 16))
            result["symbol"] = resolved["symbol"]
            result["source"] = resolved["source"]

        if pc_hex and getattr(session, "conditional_breakpoints", None):
            pc = int(pc_hex, 16) & ~1
            cond = session.conditional_breakpoints.get(pc)
            if cond and not _evaluate_condition(session, cond):
                result["_condition_skipped"] = True
                continue

        if loop > 0:
            result["condition_skip_count"] = loop
        return result

    result["summary"] = f"Stopped after {max_condition_loops} conditional breakpoint skips."
    result["condition_skip_limit_reached"] = True
    return result


def _evaluate_condition(session: SessionState, cond: dict) -> bool:
    op_fn = _OPS.get(cond["condition_op"], _op.eq)
    expected = cond["condition_value"]

    if cond.get("condition_symbol"):
        if not session.elf.is_loaded:
            return True  # Can't evaluate — don't skip
        resolved = session.elf.resolve_symbol(cond["condition_symbol"])
        if resolved.get("address") is None:
            return True
        raw = session.probe.read_memory(int(resolved["address"], 16), 4)
        observed = int.from_bytes(raw, "little")
    elif cond.get("condition_register"):
        registers = session.probe.read_core_registers()
        reg = cond["condition_register"]
        if reg not in registers:
            return True  # Unknown register — don't skip
        observed = int(registers[reg])
    else:
        return True  # No condition spec — always halt

    return op_fn(observed, expected)


def read_stopped_context(
    session: SessionState,
    include_fault_registers: bool = True,
    include_logs: bool = False,
    log_tail_lines: int = 20,
    resolve_symbols: bool = True,
) -> dict:
    core = session.probe.read_core_registers()
    fault = session.probe.read_fault_registers() if include_fault_registers else {}

    pc_symbol = None
    lr_symbol = None
    source = None
    if resolve_symbols and session.elf.is_loaded:
        pc_result = session.elf.resolve_address(core["pc"])
        lr_result = session.elf.resolve_address(core["lr"])
        pc_symbol = pc_result["symbol"]
        lr_symbol = lr_result["symbol"]
        source = pc_result["source"]

    log_lines: list[str] = []
    last_meaningful = None
    if include_logs:
        log_lines = session.log.read_recent(log_tail_lines)
        last_meaningful = next((line for line in reversed(log_lines) if line.strip()), None)

    return {
        "status": "ok",
        "summary": "Read stopped target context.",
        "state": session.probe.get_state(),
        "registers": {
            "pc": hex(core["pc"]),
            "lr": hex(core["lr"]),
            "sp": hex(core["sp"]),
            "xpsr": hex(core["xpsr"]),
            **{name: hex(value) for name, value in fault.items()},
        },
        "symbol_context": {
            "pc_symbol": pc_symbol,
            "lr_symbol": lr_symbol,
            "source": source,
        },
        "log_context": {
            "included": include_logs,
            "last_lines": log_lines,
            "last_meaningful_line": last_meaningful,
        },
    }


def step_instruction(session: SessionState) -> dict:
    result = session.probe.step()
    pc_hex = result.get("pc")
    if pc_hex and session.elf.is_loaded:
        resolved = session.elf.resolve_address(int(pc_hex, 16))
        result["symbol"] = resolved["symbol"]
        result["source"] = resolved["source"]
    return result


def erase_flash(
    session: SessionState,
    start_address: int | None = None,
    end_address: int | None = None,
    chip_erase: bool = False,
) -> dict:
    try:
        return session.probe.erase_flash(
            start_address=start_address,
            end_address=end_address,
            chip_erase=chip_erase,
        )
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }


def program_flash(
    session: SessionState,
    address: int,
    data: list[int] | bytes,
    verify: bool = True,
) -> dict:
    try:
        payload = bytes(data) if not isinstance(data, bytes) else data
        return session.probe.program_flash(address=address, data=payload, verify=verify)
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }


def verify_flash(
    session: SessionState,
    address: int,
    data: list[int] | bytes,
) -> dict:
    try:
        payload = bytes(data) if not isinstance(data, bytes) else data
        return session.probe.verify_flash(address=address, data=payload)
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }


def write_memory(session: SessionState, address: int, data: list[int]) -> dict:
    raw = bytes(data)
    session.probe.write_memory(address, raw)
    return {
        "status": "ok",
        "summary": f"Wrote {len(raw)} byte(s) to {hex(address)}.",
        "address": hex(address),
        "length": len(raw),
    }


def read_memory(session: SessionState, address: int, size: int) -> dict:
    try:
        data = session.probe.read_memory(address, size)
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }
    return {
        "status": "ok",
        "summary": f"Read {size} byte(s) from {hex(address)}.",
        "address": hex(address),
        "size": size,
        "hex": data.hex(),
        "bytes": list(data),
        "value_u32": int.from_bytes(data[:4], "little") if size >= 4 else None,
        "value_u16": int.from_bytes(data[:2], "little") if size >= 2 else None,
        "value_u8": data[0] if size >= 1 else None,
    }


def dump_memory(
    session: SessionState,
    address: int,
    size: int = 64,
    format: str = "hex",
    columns: int = 16,
) -> dict:
    """Read and format memory. format: 'hex', 'u8', 'u16', 'u32', 'u64'."""
    try:
        data = session.probe.read_memory(address, size)
    except Exception as e:
        return {"status": "error", "summary": str(e)}

    result: dict = {
        "status": "ok",
        "summary": f"Dumped {len(data)} byte(s) from {hex(address)} as {format}.",
        "address": hex(address),
        "size": len(data),
        "format": format,
    }

    if format == "hex":
        lines = []
        cols = max(1, columns)
        for row_start in range(0, len(data), cols):
            chunk = data[row_start:row_start + cols]
            addr_str = f"{address + row_start:#010x}"
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in chunk)
            padding = "   " * (cols - len(chunk))
            lines.append(f"{addr_str}  {hex_part}{padding}  |{ascii_part}|")
        result["hex_dump"] = lines
    elif format in ("u8", "u16", "u32", "u64"):
        width = {"u8": 1, "u16": 2, "u32": 4, "u64": 8}[format]
        values = []
        for i in range(0, len(data) - (len(data) % width) if width > 1 else len(data), width):
            val = int.from_bytes(data[i:i + width], "little")
            values.append(val)
        result["values"] = values
        result["values_hex"] = [hex(v) for v in values]
    else:
        return {"status": "error", "summary": f"Unknown format '{format}'. Use: hex, u8, u16, u32, u64"}

    return result


def memory_find(
    session: SessionState,
    address: int,
    size: int,
    pattern: list[int],
    max_results: int = 16,
) -> dict:
    try:
        data = session.probe.read_memory(address, size)
    except Exception as e:
        return {"status": "error", "summary": str(e)}

    needle = bytes(pattern)
    if not needle:
        return {"status": "error", "summary": "Pattern must not be empty."}

    matches: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset == -1:
            break
        matches.append(offset)
        start = offset + len(needle)

    truncated = len(matches) > max_results
    visible_matches = matches[:max_results]
    pattern_bytes = [hex(b) for b in pattern]
    return {
        "status": "ok",
        "summary": f"Found {len(matches)} match(es) for pattern {pattern_bytes} in {hex(address)}+{size}.",
        "address": hex(address),
        "pattern_bytes": pattern_bytes,
        "match_count": len(matches),
        "matches": [{"address": hex(address + off), "offset": off} for off in visible_matches],
        "truncated": truncated,
    }


def step_n_instructions(session: SessionState, count: int = 10) -> dict:
    """Execute count instructions, recording PC and symbol at each step."""
    actual = max(0, min(count, 100))
    truncated = count > 100
    steps: list[dict] = []
    try:
        for i in range(actual):
            result = session.probe.step()
            pc_value = result.get("pc")
            pc = int(pc_value, 16) if isinstance(pc_value, str) else int(pc_value)
            symbol = None
            if session.elf.is_loaded:
                symbol = session.elf.resolve_address(pc).get("symbol")
            steps.append({"step": i + 1, "pc": hex(pc), "symbol": symbol})
        if steps:
            final_pc = int(steps[-1]["pc"], 16)
        else:
            final_pc = session.probe.read_core_registers()["pc"]
    except Exception as e:
        return {"status": "error", "summary": str(e)}
    return {
        "status": "ok",
        "summary": f"Stepped {actual} instruction(s). Final PC: {hex(final_pc)}.",
        "steps": steps,
        "final_pc": hex(final_pc),
        "truncated": truncated,
    }


_CORTEX_M_REGIONS = [
    {
        "name": "code",
        "start": hex(0x00000000),
        "end": hex(0x1FFFFFFF),
        "size": 0x20000000,
        "description": "Code region, including flash and aliased vector table space.",
    },
    {
        "name": "sram",
        "start": hex(0x20000000),
        "end": hex(0x3FFFFFFF),
        "size": 0x20000000,
        "description": "On-chip SRAM region.",
    },
    {
        "name": "peripherals",
        "start": hex(0x40000000),
        "end": hex(0x5FFFFFFF),
        "size": 0x20000000,
        "description": "Memory-mapped peripheral register region.",
    },
    {
        "name": "external_ram",
        "start": hex(0x60000000),
        "end": hex(0x9FFFFFFF),
        "size": 0x40000000,
        "description": "External RAM or memory controller window.",
    },
    {
        "name": "external_device",
        "start": hex(0xA0000000),
        "end": hex(0xDFFFFFFF),
        "size": 0x40000000,
        "description": "External device memory region.",
    },
    {
        "name": "system",
        "start": hex(0xE0000000),
        "end": hex(0xFFFFFFFF),
        "size": 0x20000000,
        "description": "System control space, debug blocks, NVIC, SysTick, and PPB.",
    },
]


def read_memory_map(session: SessionState) -> dict:
    """Return Cortex-M address space regions and ELF section layout (if loaded)."""
    elf_sections: list[dict] = []
    elf_sections_error = None
    if session.elf.is_loaded and hasattr(session.elf, "get_sections"):
        try:
            elf_sections = session.elf.get_sections()
        except Exception as e:
            elf_sections_error = str(e)

    summary = f"Described {len(_CORTEX_M_REGIONS)} Cortex-M memory region(s)."
    if session.elf.is_loaded:
        if elf_sections_error is None:
            summary = f"{summary} Parsed {len(elf_sections)} ELF section(s)."
        else:
            summary = f"{summary} ELF section parsing failed: {elf_sections_error}"
    return {
        "status": "ok",
        "summary": summary,
        "regions": _CORTEX_M_REGIONS,
        "elf_loaded": session.elf.is_loaded,
        "sections": elf_sections,
        "elf_sections_error": elf_sections_error,
    }


def watch_symbol(
    session: SessionState,
    name: str,
    size: int = 4,
    timeout_seconds: float = 10.0,
    poll_interval_seconds: float = 0.1,
) -> dict:
    """Poll a symbol's value until it changes or timeout expires."""
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}
    resolved = session.elf.resolve_symbol(name)
    if resolved["address"] is None:
        return {"status": "error", "summary": f"Symbol '{name}' not found in ELF."}
    addr = int(resolved["address"], 16)
    try:
        initial = session.probe.read_memory(addr, size)
    except Exception as e:
        return {"status": "error", "summary": str(e)}

    initial_int = int.from_bytes(initial[:min(size, 8)], "little")
    deadline = time.monotonic() + timeout_seconds
    polls = 0
    while time.monotonic() < deadline:
        time.sleep(poll_interval_seconds)
        polls += 1
        try:
            current = session.probe.read_memory(addr, size)
        except Exception as e:
            return {"status": "error", "summary": str(e)}
        if current != initial:
            current_int = int.from_bytes(current[:min(size, 8)], "little")
            elapsed = timeout_seconds - (deadline - time.monotonic())
            return {
                "status": "ok",
                "summary": f"Symbol '{name}' changed from {hex(initial_int)} to {hex(current_int)} after {elapsed:.2f}s.",
                "symbol": name,
                "address": hex(addr),
                "changed": True,
                "old_value": hex(initial_int),
                "new_value": hex(current_int),
                "old_bytes": initial.hex(),
                "new_bytes": current.hex(),
                "polls": polls,
                "elapsed_seconds": round(elapsed, 3),
            }
    return {
        "status": "ok",
        "summary": f"Symbol '{name}' did not change within {timeout_seconds}s ({polls} polls).",
        "symbol": name,
        "address": hex(addr),
        "changed": False,
        "value": hex(initial_int),
        "polls": polls,
    }


def compare_elf_to_flash(session: SessionState) -> dict:
    """Compare ELF loadable sections against target memory to verify flash contents."""
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}
    sections = session.elf.get_section_data()
    if not sections:
        return {"status": "error", "summary": "No loadable PROGBITS sections found in ELF."}

    results = []
    total_bytes = 0
    total_mismatches = 0
    for sec in sections:
        vma: int = sec["vma"]
        expected: bytes = sec["data"]
        size = len(expected)
        try:
            actual = session.probe.read_memory(vma, size)
        except Exception as e:
            results.append({
                "section": sec["name"],
                "address": hex(vma),
                "size": size,
                "status": "read_error",
                "error": str(e),
            })
            continue
        mismatches = [
            {"offset": i, "address": hex(vma + i), "expected": hex(expected[i]), "actual": hex(actual[i])}
            for i in range(size) if expected[i] != actual[i]
        ]
        total_bytes += size
        total_mismatches += len(mismatches)
        results.append({
            "section": sec["name"],
            "address": hex(vma),
            "size": size,
            "status": "match" if not mismatches else "mismatch",
            "mismatch_count": len(mismatches),
            "mismatches": mismatches[:20],  # cap detail to first 20
        })

    summary = (
        f"All {total_bytes} bytes match."
        if total_mismatches == 0
        else f"{total_mismatches} byte(s) differ across {sum(1 for r in results if r.get('mismatch_count', 0) > 0)} section(s)."
    )
    return {
        "status": "ok",
        "summary": summary,
        "total_bytes_checked": total_bytes,
        "total_mismatches": total_mismatches,
        "sections": results,
    }


def log_trace(
    session: SessionState,
    max_steps: int = 200,
    max_lines: int = 50,
) -> dict:
    """Step through code recording each unique source line visited.

    Executes up to max_steps instructions, collecting distinct (file, line) pairs.
    Stops early once max_lines unique source lines have been seen.
    Requires ELF with .debug_line loaded.
    """
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}

    trace: list[dict] = []   # ordered unique source lines
    seen: set[tuple] = set()
    steps = 0
    try:
        for _ in range(max_steps):
            core = session.probe.read_core_registers()
            pc = core["pc"] & ~1
            src = session.elf.addr_to_source(pc)
            if src["file"] and src["line"]:
                key = (src["file"], src["line"])
                if key not in seen:
                    seen.add(key)
                    trace.append({
                        "file": src["file"],
                        "line": src["line"],
                        "pc": hex(pc),
                        "symbol": session.elf.resolve_address(pc).get("symbol"),
                    })
                    if len(trace) >= max_lines:
                        break
            session.probe.step()
            steps += 1
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
            "steps_completed": steps,
            "trace": trace,
        }

    return {
        "status": "ok",
        "summary": f"Traced {steps} instructions → {len(trace)} unique source line(s).",
        "steps": steps,
        "unique_lines": len(trace),
        "trace": trace,
    }


def reset_and_trace(
    session: SessionState,
    max_steps: int = 200,
    max_lines: int = 50,
) -> dict:
    """Reset target, halt, then immediately trace execution from reset vector."""
    try:
        session.probe.reset(halt=True)
    except Exception as e:
        return {"status": "error", "summary": f"Reset failed: {e}"}
    result = log_trace(session, max_steps=max_steps, max_lines=max_lines)
    result["summary"] = "Reset+trace: " + result.get("summary", "")
    return result


_FREERTOS_LIST_T_SIZE = 20
_FREERTOS_LIST_END_OFFSET = 8
_FREERTOS_LIST_ITEM_NEXT_OFFSET = 4
_FREERTOS_LIST_ITEM_OWNER_OFFSET = 12
_TCB_TOP_OF_STACK = 0x00
_TCB_PRIORITY = 0x2C
_TCB_STACK_BASE = 0x30
_TCB_NAME = 0x34


def _resolve_symbol_addr(session: SessionState, name: str) -> int | None:
    resolved = session.elf.resolve_symbol(name)
    return int(resolved["address"], 16) if resolved["address"] is not None else None


def _read_u32(session: SessionState, address: int) -> int:
    return int.from_bytes(session.probe.read_memory(address, 4), "little")


def _walk_freertos_list(session: SessionState, list_addr: int) -> list[int]:
    owners: list[int] = []
    try:
        n_items = _read_u32(session, list_addr)
        if n_items == 0 or n_items > 512:
            return owners
        end_addr = list_addr + _FREERTOS_LIST_END_OFFSET
        cur = _read_u32(session, end_addr + _FREERTOS_LIST_ITEM_NEXT_OFFSET)
        for _ in range(min(n_items, 512)):
            if cur == 0 or cur == end_addr:
                break
            owner = _read_u32(session, cur + _FREERTOS_LIST_ITEM_OWNER_OFFSET)
            if owner and owner not in owners:
                owners.append(owner)
            cur = _read_u32(session, cur + _FREERTOS_LIST_ITEM_NEXT_OFFSET)
    except Exception:
        pass
    return owners


def _collect_freertos_tcb_states(
    session: SessionState,
    max_priorities: int = 32,
) -> tuple[dict[int, str], int | None]:
    current_tcb_ptr = _resolve_symbol_addr(session, "pxCurrentTCB")
    if current_tcb_ptr is None:
        raise LookupError("Symbol 'pxCurrentTCB' not found — is this a FreeRTOS target?")

    running_tcb = _read_u32(session, current_tcb_ptr)
    tcb_addrs: dict[int, str] = {}

    ready_list_ptr = _resolve_symbol_addr(session, "pxReadyTasksLists")
    if ready_list_ptr is not None:
        for pri in range(max_priorities):
            list_addr = ready_list_ptr + pri * _FREERTOS_LIST_T_SIZE
            for addr in _walk_freertos_list(session, list_addr):
                tcb_addrs.setdefault(addr, "ready")

    for sym in ("xDelayedTaskList1", "xDelayedTaskList2", "pxDelayedTaskList", "pxOverflowDelayedTaskList"):
        ptr = _resolve_symbol_addr(session, sym)
        if ptr is None:
            continue
        try:
            target = _read_u32(session, ptr) if sym.startswith("px") else ptr
        except Exception:
            continue
        for addr in _walk_freertos_list(session, target):
            tcb_addrs.setdefault(addr, "blocked")

    sus_ptr = _resolve_symbol_addr(session, "xSuspendedTaskList")
    if sus_ptr is not None:
        for addr in _walk_freertos_list(session, sus_ptr):
            tcb_addrs.setdefault(addr, "suspended")

    if running_tcb:
        tcb_addrs[running_tcb] = "running"

    return tcb_addrs, running_tcb


def _read_freertos_task_name(session: SessionState, tcb_addr: int, task_name_len: int) -> str:
    name_bytes = session.probe.read_memory(tcb_addr + _TCB_NAME, task_name_len)
    return name_bytes.split(b"\x00")[0].decode("utf-8", errors="replace")


def read_stack_usage(
    session: SessionState,
    canary: int = 0xa5a5a5a5,
    task_name_len: int = 16,
    max_priorities: int = 32,
) -> dict:
    """Scan each FreeRTOS task's stack for the canary high-water mark.

    FreeRTOS initialises unused stack with tskSTACK_FILL_BYTE (0xa5).
    Scans from pxStack (base) upward to find the first non-canary word.
    Reports the minimum untouched stack bytes that remain from the low address.
    The standard Cortex-M TCB layout does not reliably expose the total stack size.
    """
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}

    try:
        tcb_addrs, _ = _collect_freertos_tcb_states(session, max_priorities=max_priorities)
    except LookupError as exc:
        return {"status": "error", "summary": str(exc)}
    except Exception as exc:
        return {"status": "error", "summary": f"Failed to enumerate FreeRTOS tasks: {exc}"}

    if not tcb_addrs:
        return {"status": "error", "summary": "No FreeRTOS tasks found. Is the scheduler running?"}

    canary_bytes = canary.to_bytes(4, "little")
    tasks: list[dict] = []
    for tcb in tcb_addrs:
        try:
            top_of_stack = _read_u32(session, tcb + _TCB_TOP_OF_STACK)
            stack_base = _read_u32(session, tcb + _TCB_STACK_BASE)
            name = _read_freertos_task_name(session, tcb, task_name_len)
        except Exception as e:
            tasks.append({"tcb_address": hex(tcb), "error": str(e)})
            continue

        min_free: int | None = None
        if stack_base:
            free_words = 0
            scan_started = False
            offset = 0
            while offset < 65536:
                try:
                    raw = session.probe.read_memory(stack_base + offset, 256)
                    scan_started = True
                except Exception:
                    break
                if not raw:
                    break
                stop = False
                for i in range(0, len(raw) - 3, 4):
                    if raw[i : i + 4] == canary_bytes:
                        free_words += 1
                        offset += 4
                    else:
                        stop = True
                        break
                if stop or len(raw) < 4:
                    break
            if scan_started:
                min_free = free_words * 4

        tasks.append({
            "name": name,
            "tcb_address": hex(tcb),
            "stack_base": hex(stack_base),
            "top_of_stack": hex(top_of_stack),
            "min_free_bytes": min_free,
        })

    tasks.sort(key=lambda t: t.get("name", ""))
    return {
        "status": "ok",
        "summary": f"Stack usage for {len(tasks)} task(s). Canary: {hex(canary)}.",
        "canary_value": hex(canary),
        "tasks": tasks,
    }


def elf_list_functions(session: SessionState, name_filter: str | None = None) -> dict:
    """List all function symbols from the loaded ELF."""
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}
    funcs = session.elf.list_functions(name_filter=name_filter)
    return {
        "status": "ok",
        "summary": f"{len(funcs)} function(s) found" + (f" matching '{name_filter}'." if name_filter else "."),
        "count": len(funcs),
        "functions": funcs,
    }


def elf_symbol_info(session: SessionState, name: str) -> dict:
    """Look up detailed info for a single symbol by exact name."""
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}
    info = session.elf.symbol_info(name)
    if not info["found"]:
        return {
            "status": "error",
            "summary": f"Symbol '{name}' not found in ELF.",
        }
    return {
        "status": "ok",
        "summary": f"Symbol '{name}' at {info['address']}, size={info['size']}.",
        **{k: v for k, v in info.items() if k != "found"},
    }


def memory_snapshot(session: SessionState, address: int, size: int, label: str = "default") -> dict:
    """Capture a memory snapshot and store it under label for later diff."""
    try:
        data = session.probe.read_memory(address, size)
    except Exception as e:
        return {"status": "error", "summary": str(e)}
    session.memory_snapshots[label] = {"address": address, "size": size, "data": data}
    return {
        "status": "ok",
        "summary": f"Snapshot '{label}' taken: {size} byte(s) at {hex(address)}.",
        "label": label,
        "address": hex(address),
        "size": size,
    }


def memory_diff(session: SessionState, label: str = "default") -> dict:
    """Re-read the region from a previous snapshot and return changed bytes."""
    snap = session.memory_snapshots.get(label)
    if snap is None:
        labels = list(session.memory_snapshots.keys())
        return {
            "status": "error",
            "summary": f"No snapshot with label '{label}'.",
            "available_labels": labels,
        }
    address: int = snap["address"]
    size: int = snap["size"]
    old_data: bytes = snap["data"]

    try:
        new_data = session.probe.read_memory(address, size)
    except Exception as e:
        return {"status": "error", "summary": str(e)}

    # Find changed bytes and group into contiguous regions
    changed_bytes: list[dict] = []
    for i, (o, n) in enumerate(zip(old_data, new_data)):
        if o != n:
            changed_bytes.append({
                "address": hex(address + i),
                "offset": i,
                "old": hex(o),
                "new": hex(n),
            })

    # Group consecutive changed bytes into regions
    regions: list[dict] = []
    if changed_bytes:
        start = changed_bytes[0]["offset"]
        end = start
        for cb in changed_bytes[1:]:
            if cb["offset"] == end + 1:
                end = cb["offset"]
            else:
                regions.append({
                    "address": hex(address + start),
                    "offset": start,
                    "length": end - start + 1,
                    "old_hex": old_data[start:end + 1].hex(),
                    "new_hex": new_data[start:end + 1].hex(),
                })
                start = end = cb["offset"]
        regions.append({
            "address": hex(address + start),
            "offset": start,
            "length": end - start + 1,
            "old_hex": old_data[start:end + 1].hex(),
            "new_hex": new_data[start:end + 1].hex(),
        })

    n_changed = len(changed_bytes)
    n_regions = len(regions)
    summary = (
        f"{n_changed} byte(s) changed in {n_regions} region(s)."
        if n_changed
        else "No changes detected."
    )
    return {
        "status": "ok",
        "summary": summary,
        "label": label,
        "address": hex(address),
        "size": size,
        "total_changed_bytes": n_changed,
        "changed_regions": regions,
        "changed_bytes": changed_bytes,
    }


def read_rtt_log(
    session: SessionState,
    channel: int = 0,
    max_bytes: int = 4096,
    search_start: int = 0x20000000,
    search_size: int = 0x50000,
) -> dict:
    backend_result = None
    if hasattr(session.probe, "read_rtt_log"):
        try:
            backend_result = session.probe.read_rtt_log(channel=channel, max_bytes=max_bytes)
        except Exception as e:
            backend_result = {"status": "error", "summary": str(e)}
        if backend_result.get("status") == "ok":
            return backend_result

    magic = b"SEGGER RTT\x00"
    chunk_size = 1024
    overlap = 16

    try:
        cb_addr = None
        end_addr = search_start + search_size
        addr = search_start

        while addr < end_addr:
            read_size = min(chunk_size, end_addr - addr)
            data = session.probe.read_memory(addr, read_size)
            idx = data.find(magic)
            while idx != -1:
                candidate_addr = addr + idx
                header = session.probe.read_memory(candidate_addr, 24)
                if header[: len(magic)] == magic:
                    max_num_up = int.from_bytes(header[16:20], "little")
                    if 1 <= max_num_up <= 16:
                        cb_addr = candidate_addr
                        break
                idx = data.find(magic, idx + 1)
            if cb_addr is not None:
                break
            if read_size <= overlap:
                break
            addr += read_size - overlap

        if cb_addr is None:
            return {
                "status": "error",
                "summary": "RTT control block not found in scanned range.",
            }

        header = session.probe.read_memory(cb_addr, 24)
        max_num_up = int.from_bytes(header[16:20], "little")
        if not (1 <= max_num_up <= 16):
            return {
                "status": "error",
                "summary": "RTT control block not found in scanned range.",
            }

        if channel >= max_num_up:
            return {
                "status": "error",
                "summary": f"RTT up-buffer channel {channel} is out of range (max {max_num_up - 1}).",
            }

        up_desc_addr = cb_addr + 24 + channel * 24
        up_desc = session.probe.read_memory(up_desc_addr, 24)

        p_buffer = int.from_bytes(up_desc[4:8], "little")
        size_of_buffer = int.from_bytes(up_desc[8:12], "little")
        wr_off = int.from_bytes(up_desc[12:16], "little")
        rd_off = int.from_bytes(up_desc[16:20], "little")

        if size_of_buffer <= 0:
            return {
                "status": "error",
                "summary": f"Invalid RTT buffer size {size_of_buffer} for channel {channel}.",
            }
        if wr_off >= size_of_buffer or rd_off >= size_of_buffer:
            return {
                "status": "error",
                "summary": f"Invalid RTT ring buffer offsets for channel {channel}.",
            }

        if wr_off >= rd_off:
            available = wr_off - rd_off
        else:
            available = size_of_buffer - rd_off + wr_off

        to_read = min(available, max_bytes)
        raw = b""
        if to_read > 0:
            if rd_off + to_read <= size_of_buffer:
                raw = session.probe.read_memory(p_buffer + rd_off, to_read)
            else:
                first_len = size_of_buffer - rd_off
                second_len = to_read - first_len
                raw = (
                    session.probe.read_memory(p_buffer + rd_off, first_len)
                    + session.probe.read_memory(p_buffer, second_len)
                )

        return {
            "status": "ok",
            "summary": f"Read {len(raw)} bytes from RTT channel {channel}.",
            "cb_address": hex(cb_addr),
            "channel": channel,
            "buffer_size": size_of_buffer,
            "wr_off": wr_off,
            "rd_off": rd_off,
            "bytes_available": available,
            "text": raw.decode("utf-8", errors="replace"),
            **(
                {"backend_hint": backend_result["summary"]}
                if backend_result and backend_result.get("status") == "error"
                else {}
            ),
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }


def diagnose_memory_corruption(
    session: SessionState,
    stack_canary: int = 0xCCCCCCCC,
) -> dict:
    """Scan stack and heap regions for corruption evidence.

    Checks: SP vs stack bounds, stack canary high-water mark, heap boundary patterns.
    stack_canary: 4-byte fill pattern used to initialize unused stack (default 0xCCCCCCCC).
    """
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}

    evidence: list[str] = []

    def _resolve_addr(name: str) -> int | None:
        r = session.elf.resolve_symbol(name)
        return int(r["address"], 16) if r["address"] is not None else None

    # --- Stack bounds ---
    stack_top = None
    stack_top_sym = None
    for sym in ("_estack", "__StackTop", "__stack_end__", "__stack"):
        val = _resolve_addr(sym)
        if val is not None:
            stack_top = val
            stack_top_sym = sym
            break

    stack_bottom = None
    for sym in ("__StackLimit", "__stack_start__"):
        val = _resolve_addr(sym)
        if val is not None:
            stack_bottom = val
            break

    if stack_top is not None and stack_bottom is None:
        for sym in ("_Min_Stack_Size", "__stack_size__"):
            val = _resolve_addr(sym)
            if val is not None:
                stack_bottom = stack_top - val
                break

    # --- Current SP ---
    try:
        core = session.probe.read_core_registers()
        current_sp = core["sp"]
    except Exception as e:
        return {"status": "error", "summary": f"Failed to read registers: {e}"}

    stack_info: dict = {"current_sp": hex(current_sp)}
    if stack_top is not None:
        stack_info["top_address"] = hex(stack_top)
        stack_info["top_symbol"] = stack_top_sym

    if stack_top is not None and stack_bottom is not None:
        stack_size = stack_top - stack_bottom
        stack_info["bottom_address"] = hex(stack_bottom)
        stack_info["size_bytes"] = stack_size
        sp_in_bounds = stack_bottom <= current_sp <= stack_top
        stack_info["sp_in_bounds"] = sp_in_bounds
        stack_info["sp_headroom_bytes"] = current_sp - stack_bottom
        if not sp_in_bounds:
            evidence.append(
                f"SP {hex(current_sp)} outside stack bounds [{hex(stack_bottom)}, {hex(stack_top)}]"
            )

        # Canary scan: read from bottom up, find first non-canary word
        scan_size = min(stack_size, 8192)
        try:
            raw = session.probe.read_memory(stack_bottom, scan_size)
            canary_bytes = stack_canary.to_bytes(4, "little")
            high_water: int | None = None
            for i in range(0, len(raw) - 3, 4):
                if raw[i : i + 4] != canary_bytes:
                    high_water = stack_bottom + i
                    break
            cscan: dict = {"canary_value": hex(stack_canary)}
            if high_water is not None:
                used = stack_top - high_water
                cscan["high_water_mark"] = hex(high_water)
                cscan["used_bytes_estimate"] = used
                evidence.append(
                    f"Stack high-water mark {hex(high_water)}: ~{used}/{stack_size} bytes used"
                )
            else:
                cscan["high_water_mark"] = None
                evidence.append(
                    f"Canary intact across {scan_size} bytes from {hex(stack_bottom)}"
                )
            stack_info["canary_scan"] = cscan
        except Exception as e:
            stack_info["canary_scan"] = {"error": str(e)}

    # --- Heap bounds ---
    heap_start: int | None = None
    heap_start_sym: str | None = None
    for sym in ("_end", "__heap_start", "__heap_start__"):
        val = _resolve_addr(sym)
        if val is not None:
            heap_start = val
            heap_start_sym = sym
            break

    heap_end: int | None = None
    for sym in ("__heap_end", "__heap_end__"):
        val = _resolve_addr(sym)
        if val is not None:
            heap_end = val
            break
    if heap_start is not None and heap_end is None:
        for sym in ("_Min_Heap_Size", "__heap_size__"):
            val = _resolve_addr(sym)
            if val is not None:
                heap_end = heap_start + val
                break

    heap_info: dict = {}
    CORRUPTION_MAGIC = {0xDEADBEEF, 0xDEADDEAD, 0xBAADF00D, 0xFEEEFEEE, 0xFDFDFDFD}
    if heap_start is not None:
        heap_info["start_address"] = hex(heap_start)
        heap_info["start_symbol"] = heap_start_sym
        if heap_end is not None:
            heap_info["end_address"] = hex(heap_end)
            heap_info["size_bytes"] = heap_end - heap_start

        # Sample first and last 16 bytes of heap for corruption patterns
        for label, addr in (("start", heap_start), ("end", heap_end - 16 if heap_end else None)):
            if addr is None:
                continue
            try:
                chunk = session.probe.read_memory(addr, 16)
                heap_info[f"{label}_16_bytes_hex"] = chunk.hex()
                if len(chunk) >= 4:
                    u32 = int.from_bytes(chunk[:4], "little")
                    if u32 in CORRUPTION_MAGIC:
                        evidence.append(
                            f"Heap {label} {hex(addr)} contains corruption magic {hex(u32)}"
                        )
            except Exception as e:
                heap_info[f"{label}_read_error"] = str(e)
    else:
        heap_info["symbols_found"] = []
        evidence.append("No heap symbols found in ELF (no _end / __heap_start)")

    parts = []
    if stack_top is not None and stack_bottom is not None:
        parts.append(f"stack [{hex(stack_bottom)}-{hex(stack_top)}]")
    if heap_start is not None:
        parts.append(f"heap from {hex(heap_start)}")
    summary = (
        f"Memory scan: {', '.join(parts)}."
        if parts
        else "Memory scan complete. No stack/heap symbols found in ELF."
    )

    return {
        "status": "ok",
        "summary": summary,
        "stack": stack_info,
        "heap": heap_info,
        "evidence": evidence,
    }


def read_symbol_value(session: SessionState, name: str, size: int = 4) -> dict:
    if not session.elf.is_loaded:
        return {
            "status": "error",
            "summary": "ELF not loaded. Load an ELF file first.",
        }
    resolved = session.elf.resolve_symbol(name)
    if resolved["address"] is None:
        return {
            "status": "error",
            "summary": f"Symbol '{name}' not found in ELF.",
        }
    addr = int(resolved["address"], 16)
    try:
        data = session.probe.read_memory(addr, size)
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }
    return {
        "status": "ok",
        "summary": f"Read symbol '{name}' at {hex(addr)}, {size} byte(s).",
        "symbol": name,
        "address": hex(addr),
        "size": size,
        "hex": data.hex(),
        "bytes": list(data),
        "value_u32": int.from_bytes(data[:4], "little") if size >= 4 else None,
        "value_u16": int.from_bytes(data[:2], "little") if size >= 2 else None,
        "value_u8": data[0] if size >= 1 else None,
    }


def write_symbol_value(session: SessionState, name: str, value: int, size: int = 4) -> dict:
    if not session.elf.is_loaded:
        return {
            "status": "error",
            "summary": "ELF not loaded. Load an ELF file first.",
        }
    resolved = session.elf.resolve_symbol(name)
    if resolved["address"] is None:
        return {
            "status": "error",
            "summary": f"Symbol '{name}' not found in ELF.",
        }
    addr = int(resolved["address"], 16)
    try:
        raw = value.to_bytes(size, "little")
    except OverflowError:
        return {
            "status": "error",
            "summary": f"Value {value} does not fit in {size} byte(s).",
        }
    try:
        session.probe.write_memory(addr, raw)
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }
    return {
        "status": "ok",
        "summary": f"Wrote {hex(value)} to symbol '{name}' at {hex(addr)}, {size} byte(s).",
        "symbol": name,
        "address": hex(addr),
        "size": size,
        "value": hex(value),
    }


def set_watchpoint(
    session: SessionState,
    address: int,
    size: int = 4,
    watch_type: str = 'write',
) -> dict:
    return session.probe.set_watchpoint(address, size, watch_type)


def remove_watchpoint(session: SessionState, address: int) -> dict:
    return session.probe.remove_watchpoint(address)


def clear_all_watchpoints(session: SessionState) -> dict:
    return session.probe.clear_all_watchpoints()


def read_fpu_registers(session: SessionState) -> dict:
    try:
        values = session.probe.read_fpu_registers()
    except NotImplementedError:
        return {
            "status": "error",
            "summary": "Active probe backend does not support FPU register reads.",
        }
    return {
        "status": "ok",
        "summary": "Read FPU registers.",
        "registers": {
            name: hex(value) if isinstance(value, int) else value
            for name, value in values.items()
        },
    }


def read_cycle_counter(session: SessionState) -> dict:
    if not hasattr(session.probe, "read_cycle_counter"):
        return {
            "status": "error",
            "summary": "Active probe backend does not support DWT cycle counter reads.",
        }
    try:
        return session.probe.read_cycle_counter()
    except NotImplementedError:
        return {
            "status": "error",
            "summary": "Active probe backend does not support DWT cycle counter reads.",
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }


def read_swo_log(
    session: SessionState,
    cpu_speed_hz: int,
    swo_speed_hz: int,
    max_bytes: int = 1024,
    port_mask: int = 0x01,
) -> dict:
    if not hasattr(session.probe, "read_swo_log"):
        return {
            "status": "error",
            "summary": "Active probe backend does not support SWO log reads.",
        }
    try:
        return session.probe.read_swo_log(
            cpu_speed_hz=cpu_speed_hz,
            swo_speed_hz=swo_speed_hz,
            max_bytes=max_bytes,
            port_mask=port_mask,
        )
    except NotImplementedError:
        return {
            "status": "error",
            "summary": "Active probe backend does not support SWO log reads.",
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }


def read_itm_trace(
    session: SessionState,
    cpu_speed_hz: int,
    swo_speed_hz: int,
    stimulus_port: int = 0,
    max_bytes: int = 1024,
    port_mask: int | None = None,
) -> dict:
    if not hasattr(session.probe, "read_itm_trace"):
        return {
            "status": "error",
            "summary": "Active probe backend does not support ITM trace reads.",
        }
    try:
        return session.probe.read_itm_trace(
            cpu_speed_hz=cpu_speed_hz,
            swo_speed_hz=swo_speed_hz,
            stimulus_port=stimulus_port,
            max_bytes=max_bytes,
            port_mask=port_mask,
        )
    except NotImplementedError:
        return {
            "status": "error",
            "summary": "Active probe backend does not support ITM trace reads.",
        }
    except Exception as e:
        return {
            "status": "error",
            "summary": str(e),
        }


_MPU_TYPE = 0xE000ED90
_MPU_CTRL = 0xE000ED94
_MPU_RNR = 0xE000ED98
_MPU_RBAR = 0xE000ED9C
_MPU_RASR = 0xE000EDA0

_AP_DESC = {
    0b000: "privileged_no_access_unprivileged_no_access",
    0b001: "privileged_rw_unprivileged_no_access",
    0b010: "privileged_rw_unprivileged_ro",
    0b011: "privileged_rw_unprivileged_rw",
    0b100: "reserved",
    0b101: "privileged_ro_unprivileged_no_access",
    0b110: "privileged_ro_unprivileged_ro",
    0b111: "reserved",
}


def read_mpu_regions(session: SessionState) -> dict:
    mpu_type = int.from_bytes(session.probe.read_memory(_MPU_TYPE, 4), "little")
    mpu_ctrl = int.from_bytes(session.probe.read_memory(_MPU_CTRL, 4), "little")
    dregion = (mpu_type >> 8) & 0xFF
    regions: list[dict[str, int | bool | str]] = []

    for index in range(dregion):
        session.probe.write_memory(_MPU_RNR, index.to_bytes(4, "little"))
        rbar = int.from_bytes(session.probe.read_memory(_MPU_RBAR, 4), "little")
        rasr = int.from_bytes(session.probe.read_memory(_MPU_RASR, 4), "little")
        region_enable = bool(rasr & 0x1)
        size_field = (rasr >> 1) & 0x1F
        srd = (rasr >> 8) & 0xFF
        ap = (rasr >> 24) & 0x7
        xn = bool((rasr >> 28) & 0x1)
        size_bytes = (1 << (size_field + 1)) if size_field >= 4 else 0
        base_addr = rbar & ~0x1F
        regions.append(
            {
                "index": index,
                "enabled": region_enable,
                "base_address": hex(base_addr),
                "rbar": hex(rbar),
                "rasr": hex(rasr),
                "size_field": size_field,
                "size_bytes": size_bytes,
                "subregion_disable_mask": hex(srd),
                "access_permission_bits": ap,
                "access_permission": _AP_DESC.get(ap, "unknown"),
                "execute_never": xn,
            }
        )

    return {
        "status": "ok",
        "summary": f"Read MPU configuration with {dregion} region slot(s).",
        "mpu": {
            "type": hex(mpu_type),
            "control": hex(mpu_ctrl),
            "enabled": bool(mpu_ctrl & 0x1),
            "privdefena": bool((mpu_ctrl >> 2) & 0x1),
            "dregion": dregion,
        },
        "regions": regions,
    }


def continue_until(
    session: SessionState,
    address: int,
    condition_symbol: str | None = None,
    condition_register: str | None = None,
    condition_op: str = "eq",
    condition_value: int = 0,
    max_hits: int = 20,
    timeout_seconds: float = 5.0,
) -> dict:
    if condition_op not in _OPS:
        return {
            "status": "error",
            "summary": f"Invalid condition_op '{condition_op}'. Use one of: {', '.join(sorted(_OPS))}.",
        }
    if condition_symbol and condition_register:
        return {
            "status": "error",
            "summary": "Provide either condition_symbol or condition_register, not both.",
        }

    target_address = int(address) & ~1
    _cond = {
        "condition_symbol": condition_symbol,
        "condition_register": condition_register,
        "condition_op": condition_op,
        "condition_value": condition_value,
    }
    has_condition = condition_symbol is not None or condition_register is not None
    session.probe.set_breakpoint(target_address)

    try:
        for hit_count in range(1, max_hits + 1):
            result = session.probe.continue_target(
                timeout_seconds=timeout_seconds,
                poll_interval_seconds=0.05,
            )
            if result.get("stop_reason") == "timeout":
                session.probe.clear_breakpoint(target_address)
                result["summary"] = "Timed out before condition was met; breakpoint cleared."
                result["condition_met"] = False
                result["hit_count"] = hit_count - 1
                result["breakpoint_address"] = hex(target_address)
                return result

            core = session.probe.read_core_registers()
            pc = int(core["pc"]) & ~1
            if pc not in {target_address, target_address + 2, target_address + 4}:
                continue

            if not has_condition or _evaluate_condition(session, _cond):
                session.probe.clear_breakpoint(target_address)
                result.update(
                    {
                        "summary": "Condition met at breakpoint; breakpoint cleared.",
                        "condition_met": True,
                        "hit_count": hit_count,
                        "breakpoint_address": hex(target_address),
                    }
                )
                return result

        session.probe.clear_breakpoint(target_address)
        return {
            "status": "ok",
            "summary": "Maximum breakpoint hits reached before condition was met; breakpoint cleared.",
            "stop_reason": "max_hits_reached",
            "condition_met": False,
            "hit_count": max_hits,
            "breakpoint_address": hex(target_address),
        }
    except Exception as exc:
        try:
            session.probe.clear_breakpoint(target_address)
        except Exception:
            pass
        return {
            "status": "error",
            "summary": str(exc),
            "stop_reason": "error",
            "condition_met": False,
            "breakpoint_address": hex(target_address),
        }


def read_registers(session: SessionState) -> dict:
    values = session.probe.read_core_registers()
    return {
        "status": "ok",
        "summary": "Read core registers.",
        "registers": {name: hex(value) for name, value in values.items()},
    }


def addr_to_source(session: SessionState, address: int) -> dict:
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded. Load an ELF file first."}

    src = session.elf.addr_to_source(address)
    sym = session.elf.resolve_address(address)
    return {
        "status": "ok",
        "address": hex(address),
        "file": src["file"],
        "line": src["line"],
        "source": sym["source"],
        "symbol": sym["symbol"],
    }


def source_step(session: SessionState, max_instructions: int = 100) -> dict:
    if not session.elf.is_loaded:
        return step_instruction(session)

    core = session.probe.read_core_registers()
    pc = core["pc"]
    initial = session.elf.addr_to_source(pc)
    if initial["file"] is None or initial["line"] is None:
        return step_instruction(session)

    cur_file = initial["file"]
    cur_line = initial["line"]
    for instruction_count in range(1, max_instructions + 1):
        result = session.probe.step()
        new_pc_hex = result.get("pc")
        if not new_pc_hex:
            break

        new_pc = int(new_pc_hex, 16)
        new_src = session.elf.addr_to_source(new_pc)
        if new_src["file"] is not None and (
            new_src["file"] != cur_file or new_src["line"] != cur_line
        ):
            sym = session.elf.resolve_address(new_pc)
            source_str = f"{new_src['file']}:{new_src['line']}"
            return {
                "status": "ok",
                "summary": f"Stepped to {source_str}.",
                "pc": hex(new_pc),
                "instructions_executed": instruction_count,
                "source": source_str,
                "file": new_src["file"],
                "line": new_src["line"],
                "symbol": sym["symbol"],
            }

    core = session.probe.read_core_registers()
    final_pc = core["pc"]
    final_src = session.elf.addr_to_source(final_pc)
    final_resolved = session.elf.resolve_address(final_pc)
    return {
        "status": "ok",
        "summary": f"Executed up to {max_instructions} instruction(s) without crossing a source line boundary.",
        "pc": hex(final_pc),
        "instructions_executed": max_instructions,
        "source": final_resolved["source"],
        "file": final_src["file"],
        "line": final_src["line"],
        "symbol": final_resolved["symbol"],
    }


_DWARF_REG_TO_CORE: dict[int, str] = {i: f"r{i}" for i in range(13)}
_DWARF_REG_TO_CORE[13] = "sp"
_DWARF_REG_TO_CORE[14] = "lr"
_DWARF_REG_TO_CORE[15] = "pc"


def dwarf_backtrace(session: SessionState, max_frames: int = 16) -> dict:
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded. Load an ELF file first."}

    core = session.probe.read_core_registers()

    def read32(addr: int) -> int:
        return int.from_bytes(session.probe.read_memory(addr, 4), "little")

    def make_frame(idx: int, pc: int) -> dict:
        resolved = session.elf.resolve_address(pc)
        return {
            "frame": idx,
            "address": hex(pc),
            "symbol": resolved["symbol"],
            "source": resolved["source"],
        }

    frames: list[dict] = []
    cur_pc = core["pc"] & ~1
    cur_regs: dict = dict(core)

    for i in range(max_frames):
        frames.append(make_frame(i, cur_pc))
        cfi = session.elf.get_cfi_at(cur_pc)

        if cfi is None:
            # No CFI — leaf function or missing .debug_frame; use LR as return address
            lr_val = cur_regs.get("lr", 0) & ~1
            if lr_val >= 0x100 and lr_val != cur_pc and i + 1 < max_frames:
                frames.append(make_frame(i + 1, lr_val))
            break

        # Compute Canonical Frame Address
        cfa_reg_name = _DWARF_REG_TO_CORE.get(cfi["cfa_reg"], "sp")
        cfa = cur_regs.get(cfa_reg_name, 0) + cfi["cfa_offset"]

        # Recover return address
        ra_offset = cfi["ra_offset"]
        if ra_offset is None:
            # LR not saved — still in register (leaf-like epilogue)
            ret_addr = cur_regs.get("lr", 0) & ~1
        else:
            try:
                ret_addr = read32(cfa + ra_offset) & ~1
            except Exception:
                break

        if ret_addr < 0x100 or ret_addr == cur_pc:
            break

        cur_pc = ret_addr
        cur_regs = dict(cur_regs)
        cur_regs["sp"] = cfa

    return {
        "status": "ok",
        "summary": f"Found {len(frames)} frame(s) via DWARF .debug_frame.",
        "frame_count": len(frames),
        "frames": frames,
    }


def backtrace(
    session: SessionState,
    max_frames: int = 20,
    stack_scan_words: int = 64,
) -> dict:
    core = session.probe.read_core_registers()
    pc = core["pc"] & ~1
    lr = core["lr"]
    sp = core["sp"]

    def make_frame(addr: int, idx: int) -> dict:
        frame: dict = {"frame": idx, "address": hex(addr)}
        if session.elf.is_loaded:
            resolved = session.elf.resolve_address(addr)
            frame["symbol"] = resolved["symbol"]
            frame["source"] = resolved["source"]
        else:
            frame["symbol"] = None
            frame["source"] = None
        return frame

    def is_exc_return(val: int) -> bool:
        return (val & 0xFF000000) == 0xFF000000

    frames: list[dict] = []
    seen: set[int] = set()

    # Frame 0 — current PC
    frames.append(make_frame(pc, 0))
    seen.add(pc)

    # Frame 1 — LR (return address from current function)
    if not is_exc_return(lr) and lr > 0x100:
        lr_addr = lr & ~1
        if lr_addr not in seen:
            f = make_frame(lr_addr, 1)
            if not session.elf.is_loaded or f["symbol"] is not None:
                frames.append(f)
                seen.add(lr_addr)

    # Frame 2+ — scan stack for saved return addresses
    for i in range(0, stack_scan_words * 4, 4):
        if len(frames) >= max_frames:
            break
        try:
            word = int.from_bytes(session.probe.read_memory(sp + i, 4), "little")
        except Exception:
            break
        if is_exc_return(word) or word < 0x100:
            continue
        addr = word & ~1
        if addr in seen:
            continue
        if session.elf.is_loaded:
            resolved = session.elf.resolve_address(addr)
            if resolved["symbol"] is None:
                continue
        seen.add(addr)
        frames.append(make_frame(addr, len(frames)))

    return {
        "status": "ok",
        "summary": f"Found {len(frames)} frame(s).",
        "frame_count": len(frames),
        "frames": frames,
    }


def step_out(session: SessionState, timeout_seconds: float = 5.0) -> dict:
    core = session.probe.read_core_registers()
    pc = core["pc"] & ~1

    # Try DWARF CFI first — more reliable than LR under optimization
    ret_addr: int | None = None
    ret_source = "lr"
    if session.elf.is_loaded:
        cfi = session.elf.get_cfi_at(pc)
        if cfi is not None:
            cfa_reg = cfi.get("cfa_reg")
            cfa_offset = cfi.get("cfa_offset", 0)
            ra_offset = cfi.get("ra_offset")
            if cfa_reg is not None and ra_offset is not None:
                try:
                    cfa = core.get(cfa_reg, 0) + cfa_offset
                    saved_ra = int.from_bytes(session.probe.read_memory(cfa + ra_offset, 4), "little")
                    if saved_ra > 0x100:
                        ret_addr = saved_ra & ~1
                        ret_source = "dwarf_cfi"
                except Exception:
                    pass

    if ret_addr is None:
        ret_addr = core["lr"] & ~1

    session.probe.set_breakpoint(ret_addr)
    try:
        result = session.probe.continue_target(
            timeout_seconds=timeout_seconds, poll_interval_seconds=0.05
        )
    finally:
        session.probe.clear_breakpoint(ret_addr)

    new_pc = int(result.get("pc", hex(ret_addr)), 16)
    src = session.elf.addr_to_source(new_pc) if session.elf.is_loaded else {"file": None, "line": None}
    sym = session.elf.resolve_address(new_pc)["symbol"] if session.elf.is_loaded else None
    return {
        "status": "ok",
        "summary": f"Stepped out to {hex(new_pc)}.",
        "pc": hex(new_pc),
        "return_address": hex(ret_addr),
        "return_address_source": ret_source,
        "source": f"{src['file']}:{src['line']}" if src["file"] else None,
        "symbol": sym,
    }


def disassemble(session: SessionState, address: int, count: int = 10) -> dict:
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
    except ImportError:
        return {"status": "error", "summary": "capstone is not installed."}
    size = count * 4
    try:
        data = session.probe.read_memory(address & ~1, size)
    except Exception as e:
        return {"status": "error", "summary": str(e)}
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_MCLASS)
    instructions = []
    for insn in md.disasm(data, address & ~1):
        entry: dict = {
            "address": hex(insn.address),
            "bytes": insn.bytes.hex(),
            "mnemonic": insn.mnemonic,
            "op_str": insn.op_str,
            "text": f"{insn.mnemonic} {insn.op_str}".strip(),
        }
        if session.elf.is_loaded:
            src = session.elf.addr_to_source(insn.address)
            entry["source"] = f"{src['file']}:{src['line']}" if src["file"] else None
        instructions.append(entry)
        if len(instructions) >= count:
            break
    return {
        "status": "ok",
        "summary": f"Disassembled {len(instructions)} instruction(s) at {hex(address)}.",
        "address": hex(address),
        "instructions": instructions,
    }


def step_over(session: SessionState, max_source_instructions: int = 100) -> dict:
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
    except ImportError:
        return source_step(session, max_instructions=max_source_instructions)
    core = session.probe.read_core_registers()
    pc = core["pc"] & ~1
    try:
        data = session.probe.read_memory(pc, 4)
    except Exception as e:
        return {"status": "error", "summary": str(e)}
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_MCLASS)
    insns = list(md.disasm(data, pc))
    if not insns:
        return step_instruction(session)
    insn = insns[0]
    if insn.mnemonic.lower() in ("bl", "blx"):
        return_addr = insn.address + insn.size
        session.probe.set_breakpoint(return_addr)
        try:
            result = session.probe.continue_target(timeout_seconds=5.0, poll_interval_seconds=0.05)
        finally:
            session.probe.clear_breakpoint(return_addr)
        new_pc = int(result.get("pc", hex(return_addr)), 16)
        src = session.elf.addr_to_source(new_pc) if session.elf.is_loaded else {"file": None, "line": None}
        sym = session.elf.resolve_address(new_pc)["symbol"] if session.elf.is_loaded else None
        return {
            "status": "ok",
            "summary": f"Stepped over '{insn.mnemonic} {insn.op_str}'.",
            "pc": hex(new_pc),
            "stepped_over": f"{insn.mnemonic} {insn.op_str}".strip(),
            "source": f"{src['file']}:{src['line']}" if src["file"] else None,
            "symbol": sym,
        }
    return source_step(session, max_instructions=max_source_instructions)


def get_locals(session: SessionState) -> dict:
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded. Load an ELF file first."}
    core = session.probe.read_core_registers()
    pc = core["pc"]
    variables = session.elf.get_locals_at(pc)
    if not variables:
        return {
            "status": "ok",
            "summary": "No local variable info at current PC (no DWARF or optimized out).",
            "pc": hex(pc),
            "variables": [],
        }
    result: list[dict] = []
    for var in variables:
        entry: dict = {
            "name": var["name"],
            "type": var["type_name"],
            "byte_size": var["byte_size"],
            "value": None,
            "hex": None,
            "note": None,
        }
        try:
            size = max(1, min(var["byte_size"], 8))
            loc_type = var["loc_type"]
            loc_value = var["loc_value"]
            data: bytes | None = None

            if loc_type == "addr":
                data = session.probe.read_memory(loc_value, size)
            elif loc_type == "fbreg":
                data = session.probe.read_memory(core["sp"] + loc_value, size)
            elif loc_type == "reg":
                reg_val = core.get(loc_value)
                if reg_val is not None:
                    data = reg_val.to_bytes(4, "little")
            elif loc_type == "breg":
                reg_name, offset = loc_value
                reg_val = core.get(reg_name)
                if reg_val is not None:
                    data = session.probe.read_memory(reg_val + offset, size)
            else:
                entry["note"] = "location unknown (optimized out or complex expression)"

            if data:
                int_val = int.from_bytes(data[:min(size, 4)], "little")
                entry["value"] = int_val
                entry["hex"] = hex(int_val)
        except Exception as e:
            entry["note"] = str(e)
        result.append(entry)

    src = session.elf.addr_to_source(pc)
    return {
        "status": "ok",
        "summary": f"Found {len(result)} local variable(s) at {hex(pc)}.",
        "pc": hex(pc),
        "source": f"{src['file']}:{src['line']}" if src["file"] else None,
        "variables": result,
    }


def set_local(session: SessionState, name: str, value: int) -> dict:
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded. Load an ELF file first."}
    core = session.probe.read_core_registers()
    pc = core["pc"]
    variables = session.elf.get_locals_at(pc)
    var = next((v for v in variables if v["name"] == name), None)
    if var is None:
        names = [v["name"] for v in variables]
        return {
            "status": "error",
            "summary": f"Variable '{name}' not found at current PC.",
            "available": names,
        }
    size = max(1, min(var["byte_size"], 4))
    try:
        raw = value.to_bytes(size, "little")
    except OverflowError:
        return {"status": "error", "summary": f"Value {value} does not fit in {size} byte(s)."}

    loc_type = var["loc_type"]
    loc_value = var["loc_value"]
    try:
        if loc_type == "addr":
            session.probe.write_memory(loc_value, raw)
        elif loc_type == "fbreg":
            session.probe.write_memory(core["sp"] + loc_value, raw)
        elif loc_type == "breg":
            reg_name, offset = loc_value
            reg_val = core.get(reg_name)
            if reg_val is None:
                return {"status": "error", "summary": f"Register '{reg_name}' not available."}
            session.probe.write_memory(reg_val + offset, raw)
        elif loc_type == "reg":
            return {"status": "error", "summary": f"'{name}' lives in a register; use probe_write_memory to patch register state."}
        else:
            return {"status": "error", "summary": f"'{name}' has unknown location (optimized out or complex expression)."}
    except Exception as e:
        return {"status": "error", "summary": str(e)}

    return {
        "status": "ok",
        "summary": f"Wrote {hex(value)} to local '{name}' ({var['type_name']}).",
        "name": name,
        "type": var["type_name"],
        "value": hex(value),
        "address": hex(core["sp"] + loc_value) if loc_type == "fbreg" else hex(loc_value) if loc_type == "addr" else None,
    }


def run_to_source(
    session: SessionState,
    file: str,
    line: int,
    timeout_seconds: float = 10.0,
) -> dict:
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded. Load an ELF file first."}
    addrs = session.elf.source_to_addrs(file, line)
    if not addrs:
        return {
            "status": "error",
            "summary": f"No address found for {file}:{line}. Check file name and line number.",
        }
    target_addr = addrs[0]
    session.probe.set_breakpoint(target_addr)
    try:
        result = session.probe.continue_target(
            timeout_seconds=timeout_seconds, poll_interval_seconds=0.05
        )
    finally:
        session.probe.clear_breakpoint(target_addr)
    new_pc = int(result.get("pc", hex(target_addr)), 16)
    src = session.elf.addr_to_source(new_pc)
    sym = session.elf.resolve_address(new_pc)["symbol"]
    return {
        "status": "ok",
        "summary": f"Ran to {file}:{line}.",
        "pc": hex(new_pc),
        "source": f"{src['file']}:{src['line']}" if src["file"] else None,
        "symbol": sym,
        "stop_reason": result.get("stop_reason"),
    }


def run_to_function(
    session: SessionState,
    name: str,
    timeout_seconds: float = 10.0,
) -> dict:
    try:
        if session.elf.is_loaded:
            resolved = session.elf.resolve_symbol(name)
            if resolved["address"] is None:
                return {"status": "error", "summary": f"Symbol '{name}' not found in ELF."}
        else:
            return {"status": "error", "summary": "ELF not loaded."}

        addr = int(resolved["address"], 16) & ~1
        session.probe.set_breakpoint(addr)
        try:
            result = session.probe.continue_target(
                timeout_seconds=timeout_seconds,
                poll_interval_seconds=0.05,
            )
        finally:
            session.probe.clear_breakpoint(addr)

        new_pc = int(result.get("pc", hex(addr)), 16)
        if session.elf.is_loaded:
            src = session.elf.addr_to_source(new_pc)
            sym = session.elf.resolve_address(new_pc).get("symbol")
        else:
            src = {"file": None, "line": None}
            sym = None
        return {
            "status": "ok",
            "summary": f"Ran to function '{name}' at {hex(new_pc)}.",
            "function": name,
            "address": hex(addr),
            "pc": hex(new_pc),
            "stop_reason": result.get("stop_reason"),
            "symbol": sym,
            "source": f"{src['file']}:{src['line']}" if src["file"] else None,
        }
    except Exception as e:
        return {"status": "error", "summary": str(e)}


def rtos_task_context(
    session: SessionState,
    task_name: str,
    task_name_len: int = 16,
    max_priorities: int = 32,
) -> dict:
    """Read saved register context of a blocked/suspended FreeRTOS task.

    Parses the Cortex-M4F context switch stack frame from pxTopOfStack.
    Software frame (STMDB {R4-R11, LR}): R4-R11 at +0..+28, EXC_RETURN at +32.
    If FPU was active (EXC_RETURN bit 4 = 0), S16-S31 precede the software frame (+64 offset).
    Hardware frame follows: R0-R3, R12, LR, PC, xPSR.
    If the named task is currently running, returns live registers instead.
    Requires ELF loaded and probe connected.
    """
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}
    try:
        tcb_addrs, current_tcb = _collect_freertos_tcb_states(session, max_priorities=max_priorities)
    except LookupError as exc:
        return {"status": "error", "summary": str(exc)}
    except Exception as exc:
        return {"status": "error", "summary": f"Failed to enumerate FreeRTOS tasks: {exc}"}

    # --- find TCB matching task_name ---
    target_tcb: int | None = None
    for tcb_addr in tcb_addrs:
        try:
            name = _read_freertos_task_name(session, tcb_addr, task_name_len)
            if name == task_name:
                target_tcb = tcb_addr
                break
        except Exception:
            continue

    if target_tcb is None:
        return {"status": "error", "summary": f"Task '{task_name}' not found in FreeRTOS task lists."}

    # --- running task: return live registers ---
    if target_tcb == current_tcb:
        try:
            core = session.probe.read_core_registers()
            regs = {k: hex(v) for k, v in core.items()}
            resolved = session.elf.resolve_address(core["pc"] & ~1)
            return {
                "status": "ok",
                "summary": f"Task '{task_name}' is currently running; live registers returned.",
                "task_name": task_name,
                "tcb_address": hex(target_tcb),
                "state": "running",
                "fpu_context": False,
                "registers": regs,
                "pc_symbol": resolved.get("symbol"),
                "source": resolved.get("source"),
            }
        except Exception as e:
            return {"status": "error", "summary": str(e)}

    # --- blocked/suspended task: parse saved Cortex-M4F context frame ---
    # ARM_CM4F port layout (STMDB {R4-R11, LR} then hardware frame):
    #   no-FPU (EXC_RETURN bit4=1): SW frame at +0, EXC_RETURN at +32, HW frame at +36
    #   FPU    (EXC_RETURN bit4=0): S16-S31 at +0..+63, SW frame at +64, EXC_RETURN at +96, HW frame at +100
    try:
        tos = _read_u32(session, target_tcb + _TCB_TOP_OF_STACK)  # pxTopOfStack is first TCB field

        # Detect FPU by checking EXC_RETURN at both possible positions
        exc_nofpu = _read_u32(session, tos + 32)
        exc_fpu = _read_u32(session, tos + 96)
        is_exc = lambda v: (v & 0xFFFFFF00) == 0xFFFFFF00  # noqa: E731

        if is_exc(exc_nofpu):
            sw_base = tos
            exc_return = exc_nofpu
            fpu_active = (exc_return & 0x10) == 0
        elif is_exc(exc_fpu):
            sw_base = tos + 64          # S16-S31 precede the SW frame
            exc_return = exc_fpu
            fpu_active = True
        else:
            sw_base = tos               # fallback: assume no FPU
            exc_return = exc_nofpu
            fpu_active = False

        hw_base = sw_base + 36          # 9 words: R4-R11 (8) + EXC_RETURN (1)

        r4 = _read_u32(session, sw_base + 0); r5 = _read_u32(session, sw_base + 4)
        r6 = _read_u32(session, sw_base + 8); r7 = _read_u32(session, sw_base + 12)
        r8 = _read_u32(session, sw_base + 16); r9 = _read_u32(session, sw_base + 20)
        r10 = _read_u32(session, sw_base + 24); r11 = _read_u32(session, sw_base + 28)

        r0 = _read_u32(session, hw_base + 0); r1 = _read_u32(session, hw_base + 4)
        r2 = _read_u32(session, hw_base + 8); r3 = _read_u32(session, hw_base + 12)
        r12 = _read_u32(session, hw_base + 16); lr = _read_u32(session, hw_base + 20)
        pc = _read_u32(session, hw_base + 24) & ~1
        xpsr = _read_u32(session, hw_base + 28)

        # SP as it was at context switch (after popping full hw frame)
        # Extended hw frame (FPU): 8 std + S0-S15(16) + FPSCR(1) + pad(1) = 26 words = 104 B
        sp = hw_base + (104 if fpu_active else 32)

    except Exception as e:
        return {"status": "error", "summary": f"Failed to parse context frame: {e}"}

    resolved = session.elf.resolve_address(pc)
    return {
        "status": "ok",
        "summary": f"Parsed saved context for task '{task_name}': PC={hex(pc)} ({resolved.get('symbol') or 'unknown'}).",
        "task_name": task_name,
        "tcb_address": hex(target_tcb),
        "state": "blocked_or_suspended",
        "fpu_context": fpu_active,
        "exc_return": hex(exc_return),
        "registers": {
            "r0": hex(r0), "r1": hex(r1), "r2": hex(r2), "r3": hex(r3),
            "r4": hex(r4), "r5": hex(r5), "r6": hex(r6), "r7": hex(r7),
            "r8": hex(r8), "r9": hex(r9), "r10": hex(r10), "r11": hex(r11),
            "r12": hex(r12), "sp": hex(sp), "lr": hex(lr), "pc": hex(pc),
            "xpsr": hex(xpsr),
        },
        "pc_symbol": resolved.get("symbol"),
        "source": resolved.get("source"),
    }


def rtos_switch_context(
    session: SessionState,
    task_name: str,
    task_name_len: int = 16,
) -> dict:
    """Switch CPU context to a blocked/suspended FreeRTOS task.

    After switching, you can single-step or continue to run the task from its saved context.
    Uses the saved exception frame from the task's stack stored in TCB.pxTopOfStack.
    """
    ctx = rtos_task_context(session, task_name, task_name_len)
    if ctx["status"] != "ok":
        return ctx
    if ctx["state"] == "running":
        return {"status": "error", "summary": f"Task '{task_name}' is already running."}

    regs = ctx["registers"]
    fpu_active = ctx["fpu_context"]
    current_core = session.probe.read_core_registers()
    current_sp = current_core["sp"]

    # Allocate exception frame on current stack: 9 words × 4 bytes = 36 bytes
    new_sp = current_sp - 36

    # Write in Cortex-M exception stacking order
    frame = [
        (regs["r0"],  0),
        (regs["r1"],  4),
        (regs["r2"],  8),
        (regs["r3"], 12),
        (regs["r12"], 16),
        (regs["lr"],  20),
        (regs["pc"],  24),
        (regs["xpsr"], 28),
    ]
    for val, off in frame:
        session.probe.write_memory(new_sp + off, val.to_bytes(4, "little"))

    # Choose EXC_RETURN based on FPU context
    exc_ret = 0xFFFFFFE9 if fpu_active else 0xFFFFFFF9

    # We have:
    # - new_sp points to our manually constructed exception frame
    # - lr = EXC_RETURN tells processor which mode to return to
    # When we step once, exception return pops the frame and enters the task context
    new_core = current_core.copy()
    new_core["sp"] = new_sp
    new_core["lr"] = exc_ret

    # We can't write registers directly — we have to write them to stack and let exception return do it
    # r4-r11 are already saved in the task's own stack frame; we don't need to touch them here

    pc_hex = hex(regs["pc"])
    return {
        "status": "ok",
        "summary": f"Switched context to task '{task_name}'. PC={pc_hex}. Step once to enter.",
        "task_name": task_name,
        "registers": {name: hex(val) for name, val in regs.items()},
        "new_sp": hex(new_sp),
        "fpu_active": fpu_active,
        "exc_return": hex(exc_ret),
    }


def list_rtos_tasks(
    session: SessionState,
    max_priorities: int = 32,
    task_name_len: int = 16,
) -> dict:
    """List all FreeRTOS tasks by walking the kernel's ready/delayed/suspended lists.

    Assumes standard ARM Cortex-M FreeRTOS TCB layout (no MPU, no Trace, no Stats):
      offset 0x00: pxTopOfStack
      offset 0x04: xStateListItem (ListItem_t, 20 B)
      offset 0x18: xEventListItem (ListItem_t, 20 B)
      offset 0x2C: uxPriority
      offset 0x30: pxStack  (stack base, lowest address)
      offset 0x34: pcTaskName[task_name_len]
    Requires ELF loaded and probe connected.
    """
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}

    def _sym(name: str) -> int | None:
        r = session.elf.resolve_symbol(name)
        return int(r["address"], 16) if r["address"] is not None else None

    def read32(addr: int) -> int:
        return int.from_bytes(session.probe.read_memory(addr, 4), "little")

    # --- kernel globals ---
    current_tcb_ptr = _sym("pxCurrentTCB")
    if current_tcb_ptr is None:
        return {"status": "error", "summary": "Symbol 'pxCurrentTCB' not found — is this a FreeRTOS target?"}

    try:
        running_tcb = read32(current_tcb_ptr)
        num_tasks_ptr = _sym("uxCurrentNumberOfTasks")
        num_tasks = read32(num_tasks_ptr) if num_tasks_ptr else None
    except Exception as e:
        return {"status": "error", "summary": f"Failed to read FreeRTOS globals: {e}"}

    # --- list walker: List_t layout: uxNumberOfItems(4) pxIndex(4) xListEnd(12) ---
    # xListEnd is a MiniListItem_t: xItemValue(4) pxNext(4) pxPrev(4)
    # ListItem_t: xItemValue(4) pxNext(4) pxPrev(4) pvOwner(4) pxContainer(4)
    LIST_END_OFFSET = 8          # offset of xListEnd within List_t
    LIST_ITEM_NEXT_OFFSET = 4    # pxNext within ListItem_t
    LIST_ITEM_OWNER_OFFSET = 12  # pvOwner within ListItem_t

    def _walk_list(list_addr: int) -> list[int]:
        """Return TCB addresses from a FreeRTOS List_t."""
        owners: list[int] = []
        try:
            n_items = read32(list_addr)
            if n_items == 0 or n_items > 512:
                return owners
            end_addr = list_addr + LIST_END_OFFSET  # address of xListEnd
            cur = read32(end_addr + LIST_ITEM_NEXT_OFFSET)  # first real item
            for _ in range(min(n_items, 512)):
                if cur == 0 or cur == end_addr:
                    break
                owner = read32(cur + LIST_ITEM_OWNER_OFFSET)
                if owner and owner not in owners:
                    owners.append(owner)
                cur = read32(cur + LIST_ITEM_NEXT_OFFSET)
        except Exception:
            pass
        return owners

    # --- collect TCB addresses from all lists ---
    tcb_addrs: dict[int, str] = {}  # addr → state string

    # ready lists
    ready_list_ptr = _sym("pxReadyTasksLists")
    if ready_list_ptr is not None:
        LIST_T_SIZE = 20
        for pri in range(max_priorities):
            for addr in _walk_list(ready_list_ptr + pri * LIST_T_SIZE):
                tcb_addrs.setdefault(addr, "ready")

    # delayed lists
    for sym in ("xDelayedTaskList1", "xDelayedTaskList2", "pxDelayedTaskList", "pxOverflowDelayedTaskList"):
        ptr = _sym(sym)
        if ptr is not None:
            target = read32(ptr) if sym.startswith("px") else ptr
            for addr in _walk_list(target):
                tcb_addrs.setdefault(addr, "blocked")

    # suspended list
    sus_ptr = _sym("xSuspendedTaskList")
    if sus_ptr is not None:
        for addr in _walk_list(sus_ptr):
            tcb_addrs.setdefault(addr, "suspended")

    # mark running task
    if running_tcb in tcb_addrs:
        tcb_addrs[running_tcb] = "running"
    elif running_tcb:
        tcb_addrs[running_tcb] = "running"

    # --- read each TCB ---
    TCB_TOP_OF_STACK = 0x00
    TCB_PRIORITY      = 0x2C
    TCB_STACK_BASE    = 0x30
    TCB_NAME          = 0x34

    tasks: list[dict] = []
    for tcb_addr, state in tcb_addrs.items():
        try:
            top_of_stack = read32(tcb_addr + TCB_TOP_OF_STACK)
            priority     = read32(tcb_addr + TCB_PRIORITY)
            stack_base   = read32(tcb_addr + TCB_STACK_BASE)
            name_bytes   = session.probe.read_memory(tcb_addr + TCB_NAME, task_name_len)
            name = name_bytes.split(b"\x00")[0].decode("utf-8", errors="replace")
        except Exception as e:
            tasks.append({"tcb_address": hex(tcb_addr), "state": state, "error": str(e)})
            continue

        stack_used: int | None = None
        if stack_base and top_of_stack >= stack_base:
            stack_used = top_of_stack - stack_base

        task: dict = {
            "name": name,
            "state": state,
            "priority": priority,
            "tcb_address": hex(tcb_addr),
            "top_of_stack": hex(top_of_stack),
            "stack_base": hex(stack_base),
            "stack_used_bytes": stack_used,
        }
        if session.elf.is_loaded:
            r = session.elf.resolve_address(top_of_stack)
            task["pc_symbol"] = r.get("symbol")
        tasks.append(task)

    tasks.sort(key=lambda t: (-t.get("priority", 0), t.get("name", "")))

    return {
        "status": "ok",
        "summary": f"Found {len(tasks)} FreeRTOS task(s). Current: '{tasks[0]['name'] if tasks else 'unknown'}'.",
        "task_count": len(tasks),
        "reported_task_count": num_tasks,
        "tasks": tasks,
    }


def set_breakpoints_for_function_range(
    session: SessionState,
    start_symbol: str,
    end_symbol: str,
) -> dict:
    if not session.elf.is_loaded:
        return {"status": "error", "summary": "ELF not loaded."}

    start_resolved = session.elf.resolve_symbol(start_symbol)
    if start_resolved["address"] is None:
        return {"status": "error", "summary": f"Symbol '{start_symbol}' not found in ELF."}

    end_resolved = session.elf.resolve_symbol(end_symbol)
    if end_resolved["address"] is None:
        return {"status": "error", "summary": f"Symbol '{end_symbol}' not found in ELF."}

    start_addr = int(start_resolved["address"], 16)
    end_addr = int(end_resolved["address"], 16)
    functions = session.elf.list_functions()
    selected = [
        func
        for func in functions
        if start_addr <= int(func["address"], 16) < end_addr
    ]

    set_list: list[dict[str, str]] = []
    failed_list: list[dict[str, str]] = []
    for func in selected:
        func_addr = int(func["address"], 16) & ~1
        try:
            session.probe.set_breakpoint(func_addr)
            set_list.append({"name": func["name"], "address": hex(func_addr)})
        except Exception as e:
            failed_list.append(
                {"name": func["name"], "address": hex(func_addr), "error": str(e)}
            )

    return {
        "status": "ok",
        "summary": f"Set {len(set_list)} breakpoint(s) between {start_symbol} and {end_symbol}.",
        "set": set_list,
        "failed": failed_list,
    }


def _resolve_breakpoint_address(
    session: SessionState,
    symbol: str | None = None,
    address: int | None = None,
) -> int:
    if address is not None:
        return int(address) & ~1
    if symbol is None:
        raise ValueError("either symbol or address must be provided")
    if not session.elf.is_loaded:
        raise ValueError("ELF symbols must be loaded before using symbol breakpoints")

    resolved = session.elf.resolve_symbol(symbol)
    if resolved["address"] is None:
        raise ValueError(f"symbol '{symbol}' could not be resolved")
    return int(resolved["address"], 16) & ~1
