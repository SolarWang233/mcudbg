from __future__ import annotations

from .diagnose import diagnose_hardfault, diagnose_startup_failure
from .phase3 import (
    diagnose_clock_issue,
    diagnose_interrupt_issue,
    diagnose_peripheral_stuck,
    diagnose_stack_overflow,
)
from .probe import diagnose_memory_corruption
from ..session import SessionState


def diagnose(
    session: SessionState,
    symptom: str,
    peripheral: str | None = None,
    suspected_stage: str | None = None,
    include_logs: bool = True,
    auto_halt: bool = True,
    stack_canary: int = 0xCCCCCCCC,
) -> dict:
    normalized = (symptom or "").strip().lower()
    if not normalized:
        return {
            "status": "error",
            "summary": "symptom must not be empty.",
        }

    route = _select_route(normalized=normalized, peripheral=peripheral)
    handler = route["handler"]

    if route["name"] == "diagnose_hardfault":
        result = diagnose_hardfault(
            session,
            auto_halt=auto_halt,
            include_logs=include_logs,
            suspected_stage=suspected_stage,
        )
    elif route["name"] == "diagnose_startup_failure":
        result = diagnose_startup_failure(
            session,
            auto_halt=auto_halt,
            include_logs=include_logs,
            suspected_stage=suspected_stage,
        )
    elif route["name"] == "diagnose_peripheral_stuck":
        result = diagnose_peripheral_stuck(
            session,
            peripheral=peripheral or route["inferred_peripheral"] or "unknown",
            symptom=symptom,
        )
    elif route["name"] == "diagnose_stack_overflow":
        result = diagnose_stack_overflow(session)
    elif route["name"] == "diagnose_interrupt_issue":
        result = diagnose_interrupt_issue(session)
    elif route["name"] == "diagnose_clock_issue":
        result = diagnose_clock_issue(session)
    elif route["name"] == "diagnose_memory_corruption":
        result = diagnose_memory_corruption(session, stack_canary=stack_canary)
    else:
        return {
            "status": "error",
            "summary": f"Unsupported diagnose route '{route['name']}'.",
        }

    if not isinstance(result, dict):
        return {
            "status": "error",
            "summary": f"Diagnose route '{route['name']}' returned a non-dict result.",
        }

    result = dict(result)
    result["symptom"] = symptom
    result["diagnose_route"] = route["name"]
    if route["inferred_peripheral"] is not None and "peripheral" not in result:
        result["peripheral"] = route["inferred_peripheral"]
    if result.get("status") == "ok":
        result["summary"] = f"{route['label']}: {result['summary']}"
    return result


def _select_route(normalized: str, peripheral: str | None) -> dict[str, str | None]:
    inferred_peripheral = peripheral or _infer_peripheral_name(normalized)

    if _has_any(normalized, ("hardfault", "hard fault", "fault handler", "crash", "crashed")):
        return {
            "name": "diagnose_hardfault",
            "label": "Routed to hardfault diagnosis",
            "handler": "diagnose_hardfault",
            "inferred_peripheral": inferred_peripheral,
        }
    if _has_any(normalized, ("stack overflow", "stack smashed", "stack crash", "overflowed stack")):
        return {
            "name": "diagnose_stack_overflow",
            "label": "Routed to stack-overflow diagnosis",
            "handler": "diagnose_stack_overflow",
            "inferred_peripheral": inferred_peripheral,
        }
    if _has_any(normalized, ("memory corruption", "heap corruption", "corruption", "heap overwrite", "stack canary")):
        return {
            "name": "diagnose_memory_corruption",
            "label": "Routed to memory-corruption diagnosis",
            "handler": "diagnose_memory_corruption",
            "inferred_peripheral": inferred_peripheral,
        }
    if _has_any(normalized, ("interrupt", "irq", "nvic", "isr", "pending irq")):
        return {
            "name": "diagnose_interrupt_issue",
            "label": "Routed to interrupt diagnosis",
            "handler": "diagnose_interrupt_issue",
            "inferred_peripheral": inferred_peripheral,
        }
    if _has_any(normalized, ("clock", "pll", "hse", "hsi", "msi", "sws", "system clock")):
        return {
            "name": "diagnose_clock_issue",
            "label": "Routed to clock diagnosis",
            "handler": "diagnose_clock_issue",
            "inferred_peripheral": inferred_peripheral,
        }
    if inferred_peripheral is not None or _has_any(
        normalized,
        ("uart", "spi", "i2c", "gpio", "peripheral", "tx pin", "rx pin", "no output"),
    ):
        return {
            "name": "diagnose_peripheral_stuck",
            "label": "Routed to peripheral diagnosis",
            "handler": "diagnose_peripheral_stuck",
            "inferred_peripheral": inferred_peripheral,
        }
    return {
        "name": "diagnose_startup_failure",
        "label": "Routed to startup diagnosis",
        "handler": "diagnose_startup_failure",
        "inferred_peripheral": inferred_peripheral,
    }


def _has_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def _infer_peripheral_name(text: str) -> str | None:
    tokens = text.replace(",", " ").replace(":", " ").replace("(", " ").replace(")", " ").split()
    for token in tokens:
        upper = token.upper()
        if upper.startswith(("USART", "UART", "SPI", "I2C", "GPIO", "TIM", "ADC", "DAC", "RCC")):
            return upper
    return None
