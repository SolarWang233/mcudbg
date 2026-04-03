from __future__ import annotations

import operator as _op

from ..session import SessionState


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
    return session.probe.connect(target=target, unique_id=unique_id)


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
) -> dict:
    resolved_symbol = None
    resolved_address = _resolve_breakpoint_address(session, symbol=symbol, address=address)
    if symbol and session.elf.is_loaded:
        resolved_symbol = symbol

    result = session.probe.set_breakpoint(resolved_address)
    result["breakpoint"] = {
        "symbol": resolved_symbol,
        "address": hex(resolved_address),
    }
    if resolved_symbol:
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
    if symbol:
        result["summary"] = f"Breakpoint cleared at {symbol}."
    return result


def clear_all_breakpoints(session: SessionState) -> dict:
    return session.probe.clear_all_breakpoints()


def continue_target(
    session: SessionState,
    timeout_seconds: float = 5.0,
    poll_interval_ms: int = 50,
) -> dict:
    result = session.probe.continue_target(
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=max(poll_interval_ms, 1) / 1000.0,
    )
    pc_hex = result.get("pc")
    if pc_hex and session.elf.is_loaded:
        resolved = session.elf.resolve_address(int(pc_hex, 16))
        result["symbol"] = resolved["symbol"]
        result["source"] = resolved["source"]
    return result


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
            name: hex(value) if value is not None else None
            for name, value in values.items()
        },
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


_OPS = {
    "eq": _op.eq,
    "ne": _op.ne,
    "lt": _op.lt,
    "gt": _op.gt,
    "le": _op.le,
    "ge": _op.ge,
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
    condition_fn = _OPS[condition_op]
    set_breakpoint(session, address=target_address)

    try:
        for hit_count in range(1, max_hits + 1):
            result = continue_target(
                session,
                timeout_seconds=timeout_seconds,
                poll_interval_ms=50,
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

            observed_value = condition_value
            observed_from = None
            if condition_symbol is not None:
                if not session.elf.is_loaded:
                    raise ValueError("ELF must be loaded before using condition_symbol")
                resolved = session.elf.resolve_symbol(condition_symbol)
                if resolved["address"] is None:
                    raise ValueError(f"symbol '{condition_symbol}' could not be resolved")
                symbol_address = int(resolved["address"], 16)
                raw = session.probe.read_memory(symbol_address, 4)
                observed_value = int.from_bytes(raw, "little")
                observed_from = {"symbol": condition_symbol, "address": hex(symbol_address)}
            elif condition_register is not None:
                registers = session.probe.read_core_registers()
                if condition_register not in registers:
                    raise ValueError(f"register '{condition_register}' is not available")
                observed_value = int(registers[condition_register])
                observed_from = {"register": condition_register}

            if condition_fn(observed_value, condition_value):
                session.probe.clear_breakpoint(target_address)
                result.update(
                    {
                        "summary": "Condition met at breakpoint; breakpoint cleared.",
                        "condition_met": True,
                        "hit_count": hit_count,
                        "breakpoint_address": hex(target_address),
                        "condition": {
                            "op": condition_op,
                            "expected": hex(condition_value),
                            "actual": hex(observed_value),
                            **(observed_from or {}),
                        },
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
    lr = core["lr"] & ~1
    session.probe.set_breakpoint(lr)
    try:
        result = session.probe.continue_target(
            timeout_seconds=timeout_seconds, poll_interval_seconds=0.05
        )
    finally:
        session.probe.clear_breakpoint(lr)
    new_pc = int(result.get("pc", hex(lr)), 16)
    src = session.elf.addr_to_source(new_pc) if session.elf.is_loaded else {"file": None, "line": None}
    sym = session.elf.resolve_address(new_pc)["symbol"] if session.elf.is_loaded else None
    return {
        "status": "ok",
        "summary": f"Stepped out to {hex(new_pc)}.",
        "pc": hex(new_pc),
        "return_address": hex(lr),
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
