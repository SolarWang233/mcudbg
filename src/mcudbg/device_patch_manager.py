from __future__ import annotations

from typing import Any

from .chip_matcher import match_chip_name


_PATCH_TABLE = {
    "jlink": {
        "STM32F103C8": {
            "support_tier": "validated",
            "recommended_probe": "J-Link",
            "validated_hardware": [
                {
                    "board": "Custom",
                    "mcu": "STM32F103C8",
                    "probe": "J-Link",
                    "notes": "Validated with native RTT, flash, source-level debugging, and J-Link GDB server.",
                }
            ],
            "validated_capabilities": [
                "connect",
                "halt",
                "reset",
                "memory",
                "registers",
                "flash",
                "watchpoints",
                "gdb_server",
                "rtt",
                "source_debug",
            ],
            "connect_hints": {
                "speeds": [4000, 1000, 400, "auto"],
            },
            "post_connect_checks": {
                "read_state": True,
            },
            "notes": [
                "Prefer SWD-only bring-up on STM32F103C8 boards when trace pins are shared.",
            ],
            "warnings": [
                "PB3 may be shared with TRACESWO, GPIO, or SPI functions on small F103 boards.",
            ],
            "recovery_guidance": [
                "If attach fails, retry with lower SWD speed before changing firmware.",
                "If the target still fails to respond, try under-reset attach from a pyOCD backend or external tool.",
            ],
        },
        "STM32L496VETx": {
            "support_tier": "validated",
            "recommended_probe": "J-Link",
            "validated_hardware": [
                {
                    "board": "ATK_PICTURE",
                    "mcu": "STM32L496VETx",
                    "probe": "J-Link",
                    "notes": "Alias/patch path validated; primary hardware validation remains on ST-Link/pyOCD.",
                }
            ],
            "validated_capabilities": [
                "connect",
                "halt",
                "reset",
                "memory",
                "registers",
            ],
            "connect_hints": {
                "speeds": [4000, 1000, "auto"],
            },
            "post_connect_checks": {
                "read_state": True,
            },
            "notes": [
                "L4 boards usually tolerate 4 MHz SWD; fall back to 1 MHz before auto.",
            ],
            "warnings": [],
            "recovery_guidance": [
                "If attach is unstable, retry at 1 MHz before switching probes.",
            ],
        },
    },
    "pyocd": {
        "stm32f103c8": {
            "support_tier": "known",
            "recommended_probe": "CMSIS-DAP or ST-Link",
            "validated_hardware": [
                {
                    "board": "Custom",
                    "mcu": "STM32F103C8",
                    "probe": "J-Link",
                    "notes": "pyOCD attach strategy validated in unit coverage; real hardware validation focused on J-Link for this board.",
                }
            ],
            "validated_capabilities": [
                "connect_fallback",
                "target_alias",
            ],
            "connect_hints": {
                "attempts": [
                    {"frequency": 4000000, "connect_mode": "attach"},
                    {"frequency": 1000000, "connect_mode": "attach"},
                    {"frequency": 1000000, "connect_mode": "under-reset"},
                ],
            },
            "post_connect_checks": {
                "read_state": True,
            },
            "notes": [
                "Use under-reset fallback for STM32F103C8 boards that fail normal attach.",
            ],
            "warnings": [
                "Small F103 boards may expose fewer recovery options when SWD pins are repurposed by the application.",
            ],
            "recovery_guidance": [
                "Prefer attach first, then under-reset at 1 MHz if the core is not responsive.",
            ],
        },
        "stm32l496vetx": {
            "support_tier": "validated",
            "recommended_probe": "ST-Link",
            "validated_hardware": [
                {
                    "board": "ATK_PICTURE",
                    "mcu": "STM32L496VETx",
                    "probe": "ST-Link",
                    "notes": "Primary full-stack validation board for mcudbg.",
                }
            ],
            "validated_capabilities": [
                "connect",
                "halt",
                "reset",
                "memory",
                "registers",
                "flash",
                "rtt",
                "rtos",
                "diagnose",
                "gdb_server",
                "source_debug",
            ],
            "connect_hints": {
                "attempts": [
                    {"frequency": 4000000, "connect_mode": "attach"},
                    {"frequency": 1000000, "connect_mode": "attach"},
                ],
            },
            "post_connect_checks": {
                "read_state": True,
            },
            "notes": [
                "STM32L496 boards normally attach cleanly; keep under-reset as a manual fallback.",
            ],
            "warnings": [],
            "recovery_guidance": [
                "Use under-reset manually only if normal attach fails after lowering frequency.",
            ],
        },
    },
}


def resolve_device_patch(target: str, backend: str = "pyocd") -> dict[str, Any]:
    match_result = match_chip_name(target, backend=backend)
    matched_target = match_result["matched_target"]
    patch = _PATCH_TABLE.get(backend, {}).get(matched_target)
    if patch is None:
        return {
            "status": "ok",
            "summary": f"No device patch registered for {matched_target} on {backend}.",
            "backend": backend,
            "input": target,
            "matched_target": matched_target,
            "match_result": match_result,
            "patch_applied": False,
            "support_tier": "unknown",
            "recommended_probe": None,
            "validated_hardware": [],
            "validated_capabilities": [],
            "connect_hints": {},
            "post_connect_checks": {},
            "notes": [],
            "warnings": [],
            "recovery_guidance": [],
        }

    return {
        "status": "ok",
        "summary": f"Resolved device patch for {matched_target} on {backend}.",
        "backend": backend,
        "input": target,
        "matched_target": matched_target,
        "match_result": match_result,
        "patch_applied": True,
        "support_tier": patch.get("support_tier", "known"),
        "recommended_probe": patch.get("recommended_probe"),
        "validated_hardware": patch.get("validated_hardware", []),
        "validated_capabilities": patch.get("validated_capabilities", []),
        "connect_hints": patch.get("connect_hints", {}),
        "post_connect_checks": patch.get("post_connect_checks", {}),
        "notes": patch.get("notes", []),
        "warnings": patch.get("warnings", []),
        "recovery_guidance": patch.get("recovery_guidance", []),
    }


def list_supported_targets(backend: str | None = None) -> dict[str, Any]:
    backends = [backend] if backend is not None else sorted(_PATCH_TABLE.keys())
    targets: list[dict[str, Any]] = []

    for backend_name in backends:
        for target_name, patch in sorted(_PATCH_TABLE.get(backend_name, {}).items()):
            targets.append(
                {
                    "backend": backend_name,
                    "target": target_name,
                    "support_tier": patch.get("support_tier", "known"),
                    "recommended_probe": patch.get("recommended_probe"),
                    "validated_capabilities": patch.get("validated_capabilities", []),
                    "validated_hardware": patch.get("validated_hardware", []),
                }
            )

    return {
        "status": "ok",
        "summary": f"Found {len(targets)} supported target profile(s).",
        "backend": backend,
        "targets": targets,
    }
