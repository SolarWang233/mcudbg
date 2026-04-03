"""Phase 3 diagnosis tools -- symptom-driven peripheral diagnosis."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..session import SessionState


def diagnose_peripheral_stuck(
    session: SessionState,
    peripheral: str,
    symptom: str | None = None,
) -> dict[str, Any]:
    """Diagnose why a peripheral is not working.

    Reads peripheral registers (via SVD) and checks whether the RCC clock
    enable bit for the peripheral is set. These two checks together cover the
    most common root causes of a silent/stuck peripheral.
    """
    if not session.svd.is_loaded:
        return {
            "status": "error",
            "summary": "No SVD file loaded. Call svd_load first.",
        }

    if not _probe_is_connected(session):
        return {
            "status": "error",
            "summary": "Probe not connected. Call probe_connect or connect_with_config first.",
        }

    periph_result = session.svd.read_peripheral_state(peripheral, session.probe)
    if periph_result["status"] != "ok":
        return periph_result

    rcc_notes = _check_rcc_clock(session, peripheral)

    diagnosis = periph_result.get("diagnosis", [])
    errors = periph_result.get("errors", [])
    evidence = diagnosis + rcc_notes

    return {
        "status": "ok",
        "peripheral": periph_result["peripheral"],
        "symptom": symptom,
        "summary": (
            f"Diagnosed {periph_result['peripheral']}: "
            f"{len(diagnosis)} register note(s), {len(rcc_notes)} RCC note(s)."
        ),
        "registers": periph_result.get("registers", []),
        "diagnosis": diagnosis,
        "rcc_notes": rcc_notes,
        "evidence": evidence,
        "errors": errors,
    }


def _probe_is_connected(session: SessionState) -> bool:
    """Return True if the probe appears to be connected.

    Reads the Cortex-M SCS ICTR register (0xE000E000), which is always
    accessible on any Cortex-M core regardless of MPU configuration or
    boot-mode memory remapping.  Using 0x0 (vector table) is unreliable
    because MPU policies or BOOT pin remapping can make that region
    inaccessible even with a fully functional probe.
    """
    try:
        session.probe.read_memory(0xE000E000, 4)
        return True
    except Exception:
        return False


def _check_rcc_clock(session: SessionState, peripheral_name: str) -> list[str]:
    """Search SVD RCC registers for the clock-enable bit of *peripheral_name*."""
    notes: list[str] = []

    rcc = session.svd._peripheral_map.get("RCC")
    if rcc is None:
        return ["RCC not found in SVD -- cannot check clock enable."]

    target = peripheral_name.upper() + "EN"
    for reg in (rcc.registers or []):
        for field in (reg.fields or []):
            if field.name.upper() != target:
                continue
            addr = rcc.base_address + reg.address_offset
            try:
                raw = session.probe.read_memory(addr, 4)
                value = int.from_bytes(raw, "little")
                mask = (1 << field.bit_width) - 1
                enabled = (value >> field.bit_offset) & mask
                if enabled:
                    notes.append(
                        f"RCC clock enabled: {reg.name}.{field.name}=1"
                    )
                else:
                    notes.append(
                        f"RCC clock NOT enabled: {reg.name}.{field.name}=0 -- "
                        f"call HAL_RCC_{peripheral_name.upper()}CLK_ENABLE() "
                        f"before initializing the peripheral."
                    )
            except Exception as exc:
                notes.append(f"Failed to read RCC register {reg.name}: {exc}")
            return notes

    notes.append(
        f"No clock-enable bit found for '{peripheral_name}' in RCC registers "
        f"(searched for field '{target}')."
    )
    return notes


def diagnose_stack_overflow(session: SessionState) -> dict[str, Any]:
    """Diagnose potential stack overflow on a Cortex-M target.

    Reads VTOR (0xE000ED08) to locate the vector table, extracts the
    reset-time initial SP from word 0, and compares it with the current SP.
    If an ELF is loaded and _Min_Stack_Size is available, reports remaining
    stack space and flags a likely overflow.
    Requires probe connected and target halted.
    """
    if not _probe_is_connected(session):
        return {
            "status": "error",
            "summary": "Probe not connected. Call probe_connect or connect_with_config first.",
        }

    # Step 1: read VTOR to find vector table base
    try:
        raw = session.probe.read_memory(0xE000ED08, 4)
        vtor_value = int.from_bytes(raw, "little")
    except Exception as exc:
        return {"status": "error", "summary": f"Failed to read VTOR (0xE000ED08): {exc}"}

    vector_table_base = vtor_value & 0xFFFFFF80

    # Step 2: word 0 of the vector table = initial SP at reset
    try:
        raw = session.probe.read_memory(vector_table_base, 4)
        initial_sp = int.from_bytes(raw, "little")
    except Exception as exc:
        return {"status": "error", "summary": f"Failed to read vector table at {hex(vector_table_base)}: {exc}"}

    # Step 3: current SP from core registers
    try:
        regs = session.probe.read_core_registers()
        current_sp = regs["sp"]
    except Exception as exc:
        return {"status": "error", "summary": f"Failed to read core registers: {exc}"}

    stack_used_bytes = initial_sp - current_sp

    # Step 4: optional ELF stack size
    # Try GCC linker symbol first (_Min_Stack_Size: address field holds size in bytes),
    # then fall back to Keil ARM Compiler symbol (Stack_Mem: address is stack bottom, size is allocated bytes).
    stack_allocated_bytes: int | None = None
    overflow_detected: bool | None = None
    stack_bottom: int | None = None
    try:
        result = session.elf.resolve_symbol("_Min_Stack_Size")
        if isinstance(result, dict) and result.get("address") is not None:
            min_stack_size = int(result["address"], 16)
            stack_allocated_bytes = min_stack_size
            stack_bottom = initial_sp - min_stack_size
            overflow_detected = current_sp < stack_bottom
    except Exception:
        pass

    if stack_bottom is None:
        try:
            result = session.elf.resolve_symbol("Stack_Mem")
            if isinstance(result, dict) and result.get("address") is not None and result.get("size"):
                stack_bottom = int(result["address"], 16)
                stack_allocated_bytes = result["size"]
                overflow_detected = current_sp < stack_bottom
        except Exception:
            pass

    # Step 5: build evidence list
    evidence: list[str] = [
        f"Initial SP (from VTOR): {hex(initial_sp)}",
        f"Current SP: {hex(current_sp)}, stack used: {stack_used_bytes} bytes",
    ]
    if stack_used_bytes < 0:
        evidence.append(
            "WARNING: current SP is above initial SP -- "
            "possible VTOR mismatch or stack not yet initialized."
        )
    if overflow_detected is True:
        evidence.append(
            f"STACK OVERFLOW likely: SP {hex(current_sp)} < stack bottom {hex(stack_bottom)}"
        )
    elif overflow_detected is False:
        evidence.append(
            f"Stack OK: {stack_allocated_bytes - stack_used_bytes} bytes remaining "
            f"of {stack_allocated_bytes} allocated."
        )
    else:
        evidence.append(
            "Stack size unknown (no ELF or _Min_Stack_Size symbol not found). "
            "Cannot determine if overflow occurred."
        )

    return {
        "status": "ok",
        "summary": f"Stack analysis: SP={hex(current_sp)}, used={stack_used_bytes} bytes from top.",
        "vtor": hex(vtor_value),
        "vector_table_base": hex(vector_table_base),
        "initial_sp": hex(initial_sp),
        "current_sp": hex(current_sp),
        "stack_used_bytes": stack_used_bytes,
        "stack_allocated_bytes": stack_allocated_bytes,
        "overflow_detected": overflow_detected,
        "evidence": evidence,
    }


def diagnose_interrupt_issue(session: SessionState) -> dict[str, Any]:
    if not _probe_is_connected(session):
        return {
            "status": "error",
            "summary": "Probe not connected. Call probe_connect or connect_with_config first.",
        }

    try:
        raw = session.probe.read_memory(0xE000ED04, 4)
        icsr = int.from_bytes(raw, "little")
    except Exception as exc:
        return {"status": "error", "summary": f"Failed to read SCB_ICSR (0xE000ED04): {exc}"}

    active_exception_number = icsr & 0x1FF
    pending_exception_number = (icsr >> 12) & 0x1FF
    in_interrupt = active_exception_number != 0

    try:
        enabled_irqs = _collect_nvic_irq_numbers(session, 0xE000E100)
        pending_irqs = _collect_nvic_irq_numbers(session, 0xE000E200)
        active_irqs = _collect_nvic_irq_numbers(session, 0xE000E300)
    except Exception as exc:
        return {"status": "error", "summary": f"Failed to read NVIC state: {exc}"}

    evidence = [
        (
            f"SCB_ICSR active_exception={active_exception_number}, "
            f"pending_exception={pending_exception_number}"
        ),
        f"NVIC enabled IRQs: {len(enabled_irqs)}",
        f"NVIC pending IRQs: {len(pending_irqs)}",
        f"NVIC active IRQs: {len(active_irqs)}",
    ]
    if in_interrupt:
        evidence.append(
            f"Core is currently servicing exception {active_exception_number}."
        )
    if pending_exception_number != 0:
        evidence.append(
            f"Exception {pending_exception_number} is pending in SCB_ICSR."
        )
    if pending_irqs and not active_irqs:
        evidence.append("One or more IRQs are pending but none are active.")

    suggested_next_steps = [
        "Compare pending_irqs against your expected peripheral IRQ number and confirm the ISR is enabled in startup code.",
        "If an IRQ is pending but not active, inspect masking/priority state such as PRIMASK, BASEPRI, and NVIC priority configuration.",
        "If no IRQs are enabled, verify that NVIC_EnableIRQ() or the vendor HAL equivalent was called.",
    ]

    return {
        "status": "ok",
        "summary": (
            f"Interrupt state captured: {len(enabled_irqs)} enabled IRQs, "
            f"{len(pending_irqs)} pending IRQs, {len(active_irqs)} active IRQs."
        ),
        "current_exception": {
            "active_exception_number": active_exception_number,
            "pending_exception_number": pending_exception_number,
            "in_interrupt": in_interrupt,
        },
        "enabled_irqs": enabled_irqs,
        "pending_irqs": pending_irqs,
        "active_irqs": active_irqs,
        "enabled_count": len(enabled_irqs),
        "evidence": evidence,
        "suggested_next_steps": suggested_next_steps,
    }


def diagnose_clock_issue(session: SessionState) -> dict[str, Any]:
    if not session.svd.is_loaded:
        return {
            "status": "error",
            "summary": "No SVD file loaded. Call svd_load first.",
        }

    if not _probe_is_connected(session):
        return {
            "status": "error",
            "summary": "Probe not connected. Call probe_connect or connect_with_config first.",
        }

    rcc = session.svd._peripheral_map.get("RCC")
    if rcc is None:
        return {
            "status": "error",
            "summary": "RCC not found in SVD.",
        }

    reg_map = {
        reg.name.upper(): reg
        for reg in (rcc.registers or [])
        if getattr(reg, "name", None)
    }
    required_registers = ("CR", "CFGR", "PLLCFGR")
    register_values: dict[str, int | None] = {}
    for reg_name in required_registers:
        reg = reg_map.get(reg_name)
        if reg is None:
            register_values[reg_name] = None
            continue
        addr = rcc.base_address + reg.address_offset
        try:
            raw = session.probe.read_memory(addr, 4)
            register_values[reg_name] = int.from_bytes(raw, "little")
        except Exception as exc:
            return {
                "status": "error",
                "summary": f"Failed to read RCC.{reg_name} at {hex(addr)}: {exc}",
            }

    cr_fields = _extract_register_fields(reg_map.get("CR"), register_values.get("CR"))
    cfgr_fields = _extract_register_fields(reg_map.get("CFGR"), register_values.get("CFGR"))
    pllcfgr_fields = _extract_register_fields(reg_map.get("PLLCFGR"), register_values.get("PLLCFGR"))

    sw = cfgr_fields.get("SW")
    sws = cfgr_fields.get("SWS")
    hsi_enabled = _field_enabled(cr_fields, "HSION")
    hsi_ready = _field_enabled(cr_fields, "HSIRDY")
    hse_enabled = _field_enabled(cr_fields, "HSEON")
    hse_ready = _field_enabled(cr_fields, "HSERDY")
    pll_enabled = _field_enabled(cr_fields, "PLLON")
    pll_ready = _field_enabled(cr_fields, "PLLRDY")
    pll_source_value = pllcfgr_fields.get("PLLSRC")

    requested_clock = _decode_system_clock_source(sw)
    actual_clock = _decode_system_clock_source(sws)
    pll_source = _decode_pll_source(pll_source_value)
    mismatch = sw is not None and sws is not None and sw != sws

    evidence: list[str] = []
    suggested_next_steps: list[str] = []

    if mismatch:
        evidence.append(
            f"Clock switch not complete: CFGR.SW={sw} ({requested_clock}), CFGR.SWS={sws} ({actual_clock})."
        )
        suggested_next_steps.append(
            "Wait for CFGR.SWS to match CFGR.SW before assuming the system clock source changed."
        )
    if pll_enabled and pll_ready is False:
        evidence.append("PLL is enabled but not locked yet: CR.PLLON=1, CR.PLLRDY=0.")
        suggested_next_steps.append(
            "Check PLL input clock, divisors, and startup delay; the PLL is not reporting ready."
        )
    if hse_enabled and hse_ready is False:
        evidence.append("HSE is enabled but not ready: CR.HSEON=1, CR.HSERDY=0.")
        suggested_next_steps.append(
            "Verify the external crystal/clock source and board load network; HSE is not stabilizing."
        )
    if not evidence:
        evidence.append(
            f"Clock tree appears stable: requested={requested_clock}, actual={actual_clock}, PLL source={pll_source}."
        )
        suggested_next_steps.append(
            "If timing is still wrong, inspect bus prescalers and peripheral-specific clock mux settings."
        )

    raw_registers = {
        name: ("unavailable" if value is None else hex(value))
        for name, value in register_values.items()
    }

    return {
        "status": "ok",
        "summary": (
            f"Clock state captured: requested={requested_clock}, actual={actual_clock}, "
            f"PLL={('on' if pll_enabled else 'off' if pll_enabled is not None else 'unknown')}."
        ),
        "clock_source": {
            "requested": requested_clock,
            "actual": actual_clock,
            "mismatch": mismatch,
        },
        "hsi": {"enabled": hsi_enabled, "ready": hsi_ready},
        "hse": {"enabled": hse_enabled, "ready": hse_ready},
        "pll": {
            "enabled": pll_enabled,
            "ready": pll_ready,
            "source": pll_source,
            "locked": bool(pll_enabled and pll_ready),
        },
        "raw_registers": raw_registers,
        "evidence": evidence,
        "suggested_next_steps": suggested_next_steps,
    }


def _collect_nvic_irq_numbers(session: SessionState, base_address: int) -> list[int]:
    register_values: list[int] = []
    for register_index in range(8):
        addr = base_address + (register_index * 4)
        raw = session.probe.read_memory(addr, 4)
        register_values.append(int.from_bytes(raw, "little"))

    irq_numbers: list[int] = []
    for irq_number in range(240):
        register_index = irq_number // 32
        bit_index = irq_number % 32
        value = register_values[register_index]
        if (value >> bit_index) & 1:
            irq_numbers.append(irq_number)
    return irq_numbers


def _extract_register_fields(register: Any | None, value: int | None) -> dict[str, int]:
    if register is None or value is None:
        return {}

    decoded: dict[str, int] = {}
    for field in (register.fields or []):
        mask = (1 << field.bit_width) - 1
        decoded[field.name.upper()] = (value >> field.bit_offset) & mask
    return decoded


def _field_enabled(fields: dict[str, int], name: str) -> bool | None:
    value = fields.get(name)
    return None if value is None else bool(value)


def _decode_system_clock_source(value: int | None) -> str:
    # STM32L4 CFGR SW/SWS encoding: 0=MSI, 1=HSI16, 2=HSE, 3=PLL
    mapping = {
        0: "MSI",
        1: "HSI16",
        2: "HSE",
        3: "PLL",
    }
    if value is None:
        return "Unknown"
    return mapping.get(value, f"Unknown({value})")


def _decode_pll_source(value: int | None) -> str:
    # STM32L4 PLLCFGR PLLSRC encoding: 0=None, 1=MSI, 2=HSI16, 3=HSE
    mapping = {
        0: "None",
        1: "MSI",
        2: "HSI16",
        3: "HSE",
    }
    if value is None:
        return "Unknown"
    return mapping.get(value, f"Unknown({value})")
