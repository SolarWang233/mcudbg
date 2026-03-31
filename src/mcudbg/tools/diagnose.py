from __future__ import annotations

from ..models.diagnostics import HardFaultDiagnosis, LogContext, RootCauseHint, StackSnapshot, SymbolContext
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

    evidence = []
    if last_meaningful:
        evidence.append(f"UART output stopped after '{last_meaningful}'.")
    evidence.append(f"PC={hex(core['pc'])}, LR={hex(core['lr'])}, SP={hex(core['sp'])}.")
    if pc_symbol:
        evidence.append(f"PC resolved to {pc_symbol}.")
    if fault_registers.get("cfsr", 0):
        evidence.append(f"CFSR={hex(fault_registers['cfsr'])} indicates {fault_class}.")

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
        suspected_root_causes=[
            RootCauseHint(
                label="invalid pointer dereference during initialization",
                confidence="high",
            ),
            RootCauseHint(
                label="incorrect peripheral register access",
                confidence="medium",
            ),
        ],
        suggested_next_steps=[
            "Inspect the last memory access in the failing init path.",
            "Verify all startup handles are initialized before use.",
            "Check register base addresses used around the fault site.",
        ],
        raw_refs={"elf_loaded": session.elf.is_loaded, "probe_backend": "cmsis-dap", "log_backend": "uart"},
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

    if fault_detected:
        diagnosis_type = "startup_failure_with_fault"
        summary = f"Startup likely failed around {stage}, and the target shows a fault condition."
        confidence = "high"
    else:
        diagnosis_type = "startup_failure_no_fault_confirmed"
        summary = f"Startup appears to stop around {stage}, but no definitive fault was confirmed."
        confidence = "medium"

    evidence = []
    if last_meaningful:
        evidence.append(f"UART output stops after '{last_meaningful}'.")
    if pc_symbol:
        evidence.append(f"Current PC resolves to {pc_symbol}.")
    evidence.append(f"PC={hex(core['pc'])}, LR={hex(core['lr'])}, SP={hex(core['sp'])}.")
    if fault_detected:
        evidence.append(f"Fault registers suggest {fault_class}.")

    suspected_root_causes = []
    suggested_next_steps = []
    if fault_detected:
        suspected_root_causes.extend(
            [
                RootCauseHint(
                    label=f"startup code fault near {stage}",
                    confidence="high",
                ),
                RootCauseHint(
                    label="invalid pointer or register access during initialization",
                    confidence="medium",
                ),
            ]
        )
        suggested_next_steps.extend(
            [
                f"Inspect the initialization path around {stage}.",
                "Check the last memory or register access before the fault.",
                "Verify all init-time handles, buffers, and register addresses.",
            ]
        )
    else:
        suspected_root_causes.extend(
            [
                RootCauseHint(
                    label=f"startup flow is blocked near {stage}",
                    confidence="medium",
                ),
                RootCauseHint(
                    label="firmware is stuck in a wait loop or peripheral bring-up path",
                    confidence="medium",
                ),
            ]
        )
        suggested_next_steps.extend(
            [
                f"Check whether startup progress should continue after {stage}.",
                "Inspect wait loops, timeout logic, and peripheral ready conditions.",
                "Add one more log point immediately after the current last successful step.",
            ]
        )

    return {
        "status": "ok",
        "diagnosis_type": diagnosis_type,
        "summary": summary,
        "confidence": confidence,
        "target_state": {"halted": True, "reason": "halted_for_analysis"},
        "startup_context": {
            "suspected_stage": stage,
            "last_meaningful_log": last_meaningful,
            "progress_interrupted": bool(last_meaningful),
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
            log_stopped_abruptly=bool(last_meaningful),
        ).model_dump(),
        "evidence": evidence,
        "suspected_root_causes": [item.model_dump() for item in suspected_root_causes],
        "suggested_next_steps": suggested_next_steps,
        "raw_refs": {
            "elf_loaded": session.elf.is_loaded,
            "probe_backend": "cmsis-dap",
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
        return "memory_management_fault"
    if cfsr & 0x00010000:
        return "usage_fault"
    if fault_registers.get("hfsr", 0) & 0x40000000:
        return "forced_hardfault"
    return "hardfault_handler_entered"


def _describe_fault(fault_class: str) -> str:
    descriptions = {
        "precise_data_bus_error": "A precise data bus fault was reported by CFSR.",
        "imprecise_data_bus_error": "An imprecise data bus fault was reported by CFSR.",
        "memory_management_fault": "A memory management fault was reported by CFSR.",
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
