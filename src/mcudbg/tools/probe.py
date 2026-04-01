from __future__ import annotations

from ..session import SessionState


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


def read_registers(session: SessionState) -> dict:
    values = session.probe.read_core_registers()
    return {
        "status": "ok",
        "summary": "Read core registers.",
        "registers": {name: hex(value) for name, value in values.items()},
    }


def _resolve_breakpoint_address(
    session: SessionState,
    symbol: str | None = None,
    address: int | None = None,
) -> int:
    if address is not None:
        return int(address)
    if symbol is None:
        raise ValueError("either symbol or address must be provided")
    if not session.elf.is_loaded:
        raise ValueError("ELF symbols must be loaded before using symbol breakpoints")

    resolved = session.elf.resolve_symbol(symbol)
    if resolved["address"] is None:
        raise ValueError(f"symbol '{symbol}' could not be resolved")
    return int(resolved["address"], 16)
