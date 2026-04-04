from __future__ import annotations

from typing import Any


_ALIAS_TABLE = {
    "pyocd": {
        "stm32f103c8": "stm32f103c8",
        "stm32f103c8t6": "stm32f103c8",
        "stm32f103ze": "stm32f103ze",
        "stm32f103zet6": "stm32f103ze",
        "stm32l496ve": "stm32l496vetx",
        "stm32l496vetx": "stm32l496vetx",
    },
    "jlink": {
        "stm32f103c8": "STM32F103C8",
        "stm32f103c8t6": "STM32F103C8",
        "stm32f103ze": "STM32F103ZE",
        "stm32f103zet6": "STM32F103ZE",
        "stm32l496ve": "STM32L496VETx",
        "stm32l496vetx": "STM32L496VETx",
    },
}


def _normalize_chip_name(name: str) -> str:
    return "".join(ch for ch in name.strip().lower() if ch.isalnum())


def match_chip_name(name: str, backend: str = "pyocd") -> dict[str, Any]:
    """Resolve common MCU aliases to a backend-specific target name."""
    normalized = _normalize_chip_name(name)
    aliases = _ALIAS_TABLE.get(backend, {})
    matched = aliases.get(normalized)
    if matched is not None:
        return {
            "status": "ok",
            "summary": f"Matched '{name}' to {matched} for {backend}.",
            "input": name,
            "backend": backend,
            "normalized_input": normalized,
            "matched_target": matched,
            "confidence": "high",
        }

    return {
        "status": "ok",
        "summary": f"No alias match for '{name}'; using the original target name.",
        "input": name,
        "backend": backend,
        "normalized_input": normalized,
        "matched_target": name,
        "confidence": "pass_through",
    }
