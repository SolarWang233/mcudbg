from __future__ import annotations

from ..models.diagnostics import HardFaultDiagnosis, LogContext, StackSnapshot, SymbolContext
from ..session import SessionState


def diagnose_hardfault(
    session: SessionState,
    auto_halt: bool = True,
    include_logs: bool = True,
    log_tail_lines: int = 50,
    resolve_symbols: bool = True,
    include_fault_registers: bool = True,
    include_stack_snapshot: bool = True,
    stack_snapshot_bytes: int = 64,
    suspected_stage: str | None = None,
) -> dict:
    if auto_halt:
        session.probe.halt()

    core = session.probe.read_core_registers()
    fault_registers = session.probe.read_fault_registers() if include_fault_registers else {}

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

    stack_snapshot = StackSnapshot()
    if include_stack_snapshot:
        raw = session.probe.read_memory(core["sp"], stack_snapshot_bytes)
        stack_snapshot = StackSnapshot(
            included=True,
            start_address=hex(core["sp"]),
            size_bytes=stack_snapshot_bytes,
            data_hex=raw.hex(" "),
        )

    fault_class = _classify_fault(fault_registers)
    summary_stage = suspected_stage or "startup"
    summary = f"Target entered HardFault shortly after {summary_stage}."

    cfsr = fault_registers.get("cfsr", 0)
    hfsr = fault_registers.get("hfsr", 0)
    mmfar = fault_registers.get("mmfar", 0)
    bfar = fault_registers.get("bfar", 0)
    shcsr = fault_registers.get("shcsr", 0)

    evidence: list[str] = []
    if last_meaningful:
        evidence.append(f"Last meaningful UART line = '{last_meaningful}'.")
    evidence.append(f"PC = {hex(core['pc'])}" + (f" ({pc_symbol})" if pc_symbol else "") + ".")
    evidence.append(f"LR = {hex(core['lr'])}" + (f" ({lr_symbol})" if lr_symbol else "") + ".")
    evidence.append(f"SP = {hex(core['sp'])}.")
    evidence.append(f"xPSR = {hex(core['xpsr'])}.")
    if source:
        evidence.append(f"Source = {source}.")
    evidence.append(f"CFSR = {hex(cfsr)}.")
    evidence.append(f"HFSR = {hex(hfsr)}.")
    evidence.append(f"MMFAR = {hex(mmfar)}.")
    evidence.append(f"BFAR = {hex(bfar)}.")
    evidence.append(f"SHCSR = {hex(shcsr)}.")
    if pc_symbol:
        evidence.append(f"PC symbol = {pc_symbol}.")
    if lr_symbol:
        evidence.append(f"LR symbol = {lr_symbol}.")
    if cfsr & 0x00000001:
        evidence.append("CFSR IACCVIOL bit set.")
    if cfsr & 0x00000002:
        evidence.append("CFSR DACCVIOL bit set.")
    if cfsr & 0x00000008:
        evidence.append("CFSR MUNSTKERR bit set.")
    if cfsr & 0x00000010:
        evidence.append("CFSR MSTKERR bit set.")
    if cfsr & 0x00000020:
        evidence.append("CFSR MLSPERR bit set.")
    if cfsr & 0x00000080:
        evidence.append(f"CFSR MMARVALID bit set, MMFAR = {hex(mmfar)}.")
    if cfsr & 0x00000100:
        evidence.append("CFSR IBUSERR bit set.")
    if cfsr & 0x00000200:
        evidence.append("CFSR PRECISERR bit set.")
    if cfsr & 0x00000400:
        evidence.append("CFSR IMPRECISERR bit set.")
    if cfsr & 0x00000800:
        evidence.append("CFSR UNSTKERR bit set.")
    if cfsr & 0x00001000:
        evidence.append("CFSR STKERR bit set.")
    if cfsr & 0x00002000:
        evidence.append("CFSR LSPERR bit set.")
    if cfsr & 0x00008000:
        evidence.append(f"CFSR BFARVALID bit set, BFAR = {hex(bfar)}.")
    if cfsr & 0x00010000:
        evidence.append("CFSR UNDEFINSTR bit set.")
    if cfsr & 0x00020000:
        evidence.append("CFSR INVSTATE bit set.")
    if cfsr & 0x00040000:
        evidence.append("CFSR INVPC bit set.")
    if cfsr & 0x00080000:
        evidence.append("CFSR NOCP bit set.")
    if cfsr & 0x01000000:
        evidence.append("CFSR UNALIGNED bit set.")
    if cfsr & 0x02000000:
        evidence.append("CFSR DIVBYZERO bit set.")
    if hfsr & 0x00000002:
        evidence.append("HFSR VECTTBL bit set.")
    if hfsr & 0x40000000:
        evidence.append("HFSR FORCED bit set.")
    if pc_symbol == "HardFault_Handler":
        evidence.append("PC resolves to HardFault_Handler.")
    if core.get("pc") == 0xFFFFFFFF:
        evidence.append("PC = 0xffffffff.")

    diagnosis = HardFaultDiagnosis(
        status="ok",
        diagnosis_type="hardfault_detected",
        summary=summary,
        confidence="high" if fault_registers.get("cfsr", 0) else "medium",
        target_state={"halted": True, "reason": "halted_for_analysis"},
        fault={
            "fault_detected": True,
            "fault_handler_active": pc_symbol == "HardFault_Handler",
            "fault_class": fault_class,
            "fault_description": _describe_fault(fault_class),
            "escalated_to_hardfault": bool(hfsr & 0x40000000),
            "registers": {
                "pc": hex(core["pc"]),
                "lr": hex(core["lr"]),
                "sp": hex(core["sp"]),
                "xpsr": hex(core["xpsr"]),
                **{name: hex(value) for name, value in fault_registers.items()},
            },
        },
        symbol_context=SymbolContext(
            pc_symbol=pc_symbol,
            lr_symbol=lr_symbol,
            source=source,
        ),
        log_context=LogContext(
            included=include_logs,
            last_lines=log_lines,
            last_meaningful_line=last_meaningful,
            log_stopped_abruptly=bool(last_meaningful),
        ),
        stack_snapshot=stack_snapshot,
        evidence=evidence,
        raw_refs={"elf_loaded": session.elf.is_loaded, "probe_backend": "pyocd", "log_backend": "uart"},
    )
    return diagnosis.model_dump()


def diagnose_startup_failure(
    session: SessionState,
    auto_halt: bool = True,
    include_logs: bool = True,
    log_tail_lines: int = 50,
    resolve_symbols: bool = True,
    suspected_stage: str | None = None,
) -> dict:
    if auto_halt:
        session.probe.halt()

    core = session.probe.read_core_registers()
    pc_samples = [core["pc"]]
    for _ in range(2):
        try:
            pc_samples.append(session.probe.read_core_registers()["pc"])
        except Exception:
            break
    fault_registers = session.probe.read_fault_registers()

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

    fault_class = _classify_fault(fault_registers)
    fault_detected = bool(fault_registers.get("cfsr", 0) or fault_registers.get("hfsr", 0))
    stage = suspected_stage or _infer_stage_from_logs(last_meaningful)
    startup_completed = _logs_indicate_startup_success(log_lines)

    if startup_completed and not fault_detected:
        diagnosis_type = "startup_completed_normally"
        summary = f"Startup completed normally past {stage}."
        confidence = "high"
    elif fault_detected:
        diagnosis_type = "startup_failure_with_fault"
        summary = f"Startup stopped around {stage} with fault registers set."
        confidence = "high"
    else:
        diagnosis_type = "startup_failure_no_fault_confirmed"
        summary = f"Startup appears to stop around {stage} without a confirmed fault."
        confidence = "medium"

    cfsr = fault_registers.get("cfsr", 0)
    hfsr = fault_registers.get("hfsr", 0)
    mmfar = fault_registers.get("mmfar", 0)
    bfar = fault_registers.get("bfar", 0)
    ipsr = core["xpsr"] & 0x1FF

    evidence: list[str] = []
    if last_meaningful:
        evidence.append(f"Last meaningful UART line = '{last_meaningful}'.")
    if pc_symbol:
        evidence.append(f"PC symbol = {pc_symbol}.")
    if lr_symbol:
        evidence.append(f"LR symbol = {lr_symbol}.")
    if len(pc_samples) >= 2 and all(pc == pc_samples[0] for pc in pc_samples):
        evidence.append(f"PC stuck at {hex(pc_samples[0])} for {len(pc_samples)} polls.")
    else:
        evidence.append("PC samples = " + ", ".join(hex(pc) for pc in pc_samples) + ".")
    evidence.append(f"LR = {hex(core['lr'])}.")
    evidence.append(f"SP = {hex(core['sp'])}.")
    evidence.append(f"xPSR = {hex(core['xpsr'])}.")
    evidence.append(f"xPSR IPSR field = {ipsr}.")
    if source:
        evidence.append(f"Source = {source}.")
    evidence.append(f"CFSR = {hex(cfsr)}, HFSR = {hex(hfsr)}.")
    evidence.append(f"MMFAR = {hex(mmfar)}, BFAR = {hex(bfar)}.")
    if startup_completed and not fault_detected:
        evidence.append("Startup success markers present in UART logs.")
    if cfsr & 0x00000001:
        evidence.append("CFSR IACCVIOL bit set.")
    if cfsr & 0x00000002:
        evidence.append("CFSR DACCVIOL bit set.")
    if cfsr & 0x00000080:
        evidence.append(f"CFSR MMARVALID bit set, MMFAR = {hex(mmfar)}.")
    if cfsr & 0x00000100:
        evidence.append("CFSR IBUSERR bit set.")
    if cfsr & 0x00000200:
        evidence.append("CFSR PRECISERR bit set.")
    if cfsr & 0x00000400:
        evidence.append("CFSR IMPRECISERR bit set.")
    if cfsr & 0x00008000:
        evidence.append(f"CFSR BFARVALID bit set, BFAR = {hex(bfar)}.")
    if cfsr & 0x00010000:
        evidence.append("CFSR UNDEFINSTR bit set.")
    if cfsr & 0x00020000:
        evidence.append("CFSR INVSTATE bit set.")
    if cfsr & 0x00040000:
        evidence.append("CFSR INVPC bit set.")
    if cfsr & 0x00080000:
        evidence.append("CFSR NOCP bit set.")
    if cfsr & 0x01000000:
        evidence.append("CFSR UNALIGNED bit set.")
    if cfsr & 0x02000000:
        evidence.append("CFSR DIVBYZERO bit set.")
    if hfsr & 0x00000002:
        evidence.append("HFSR VECTTBL bit set.")
    if hfsr & 0x40000000:
        evidence.append("HFSR FORCED bit set.")

    return {
        "status": "ok",
        "diagnosis_type": diagnosis_type,
        "summary": summary,
        "confidence": confidence,
        "target_state": {"halted": True, "reason": "halted_for_analysis"},
        "startup_context": {
            "suspected_stage": stage,
            "last_meaningful_log": last_meaningful,
            "progress_interrupted": bool(last_meaningful) and not startup_completed,
        },
        "fault": {
            "fault_detected": fault_detected,
            "fault_class": fault_class if fault_detected else None,
            "registers": {
                "pc": hex(core["pc"]),
                "lr": hex(core["lr"]),
                "sp": hex(core["sp"]),
                "xpsr": hex(core["xpsr"]),
                **{name: hex(value) for name, value in fault_registers.items()},
            },
        },
        "symbol_context": SymbolContext(
            pc_symbol=pc_symbol,
            lr_symbol=lr_symbol,
            source=source,
        ).model_dump(),
        "log_context": LogContext(
            included=include_logs,
            last_lines=log_lines,
            last_meaningful_line=last_meaningful,
            log_stopped_abruptly=bool(last_meaningful) and not startup_completed,
        ).model_dump(),
        "evidence": evidence,
        "raw_refs": {
            "elf_loaded": session.elf.is_loaded,
            "probe_backend": "pyocd",
            "log_backend": "uart",
        },
    }


def _classify_fault(fault_registers: dict[str, int]) -> str:
    cfsr = fault_registers.get("cfsr", 0)
    if cfsr & 0x00008200:
        return "precise_data_bus_error"
    if cfsr & 0x00000400:
        return "imprecise_data_bus_error"
    if cfsr & 0x00000001:
        return "instruction_access_violation"
    if cfsr & 0x00000002:
        return "data_access_violation"
    if cfsr & 0x00010000:
        return "usage_fault"
    if fault_registers.get("hfsr", 0) & 0x40000000:
        return "forced_hardfault"
    return "hardfault_handler_entered"


def _describe_fault(fault_class: str) -> str:
    descriptions = {
        "precise_data_bus_error": "A precise data bus fault was reported by CFSR.",
        "imprecise_data_bus_error": "An imprecise data bus fault was reported by CFSR.",
        "instruction_access_violation": "An instruction access violation was reported by CFSR.",
        "data_access_violation": "A data access violation was reported by CFSR.",
        "usage_fault": "A usage fault was reported by CFSR.",
        "forced_hardfault": "A configurable fault escalated into HardFault.",
        "hardfault_handler_entered": "The CPU is currently in HardFault handler.",
    }
    return descriptions[fault_class]


def _infer_stage_from_logs(last_meaningful: str | None) -> str:
    if not last_meaningful:
        return "early boot"

    normalized = last_meaningful.lower()
    if "clock" in normalized:
        return "clock initialization"
    if "uart" in normalized:
        return "uart initialization"
    if "sensor" in normalized:
        return "sensor initialization"
    if "init" in normalized:
        return "initialization"
    return "startup"


def _logs_indicate_startup_success(log_lines: list[str]) -> bool:
    success_markers = (
        "sensor init ok",
        "app loop running",
        "startup complete",
        "boot complete",
    )
    normalized_lines = [line.lower() for line in log_lines]
    return any(marker in line for line in normalized_lines for marker in success_markers)


def _build_fault_notes(
    fault_registers: dict[str, int],
    core: dict[str, int],
    pc_symbol: str | None,
    lr_symbol: str | None,
) -> dict:
    cfsr = fault_registers.get("cfsr", 0)
    notes = {
        "evidence": [],
        "root_causes": [],
        "next_steps": [],
    }

    if cfsr & 0x00000001:
        notes["evidence"].append(
            "CFSR bit 0 indicates an instruction access violation."
        )
        notes["root_causes"].append(
            {
                "label": "invalid execution target or illegal function entry",
                "confidence": "high",
            }
        )
        notes["root_causes"].append(
            {
                "label": "control flow jumped to an unmapped address during startup",
                "confidence": "medium",
            }
        )
        notes["next_steps"].extend(
            [
                "Resolve the stacked PC/LR values against the ELF symbols.",
                "Verify whether the failing path uses an invalid function pointer or forced bad entry address.",
                "Confirm the startup control flow immediately before the fault site.",
            ]
        )
    elif cfsr & 0x00008200:
        notes["root_causes"].append(
            {
                "label": "invalid pointer dereference during initialization",
                "confidence": "high",
            }
        )
        notes["root_causes"].append(
            {
                "label": "incorrect peripheral register access",
                "confidence": "medium",
            }
        )
        notes["next_steps"].extend(
            [
                "Inspect the last memory access in the failing init path.",
                "Verify all startup handles are initialized before use.",
                "Check register base addresses used around the fault site.",
            ]
        )
    else:
        notes["root_causes"].append(
            {
                "label": "startup-stage fault with incomplete classification",
                "confidence": "medium",
            }
        )
        notes["next_steps"].extend(
            [
                "Inspect the stacked register frame and resolve PC/LR against the ELF.",
                "Compare the fault register values with the Cortex-M fault status definitions.",
            ]
        )

    if pc_symbol == "HardFault_Handler":
        notes["evidence"].append("PC currently resolves to HardFault_Handler.")
    if lr_symbol:
        notes["evidence"].append(f"LR resolves to {lr_symbol}.")
    if core.get("pc") == 0xFFFFFFFF:
        notes["evidence"].append("PC contains 0xFFFFFFFF, which strongly suggests an invalid execution target.")

    return notes
