from __future__ import annotations

from ..config import RuntimeConfig, get_builtin_profiles
from ..session import SessionState


def get_runtime_config(session: SessionState) -> dict:
    return {
        "status": "ok",
        "summary": "Loaded current mcudbg runtime configuration.",
        "config": session.config.model_dump(),
    }


def list_demo_profiles() -> dict:
    profiles = get_builtin_profiles()
    return {
        "status": "ok",
        "summary": f"Found {len(profiles)} built-in demo profile(s).",
        "profiles": {
            name: profile.model_dump() for name, profile in profiles.items()
        },
    }


def load_demo_profile(session: SessionState, profile_name: str) -> dict:
    profiles = get_builtin_profiles()
    if profile_name not in profiles:
        return {
            "status": "error",
            "summary": f"Unknown demo profile: {profile_name}.",
            "available_profiles": sorted(profiles.keys()),
        }

    profile = profiles[profile_name]
    session.config.apply_profile(profile)
    return {
        "status": "ok",
        "summary": f"Loaded demo profile {profile_name}.",
        "config": session.config.model_dump(),
    }


def configure_probe(
    session: SessionState,
    target: str | None = None,
    unique_id: str | None = None,
) -> dict:
    """Set probe connection parameters (target chip name and optional probe serial)."""
    if target is not None:
        session.config.probe.target = target
    if unique_id is not None:
        session.config.probe.unique_id = unique_id
    return {
        "status": "ok",
        "summary": "Updated probe configuration.",
        "probe": session.config.probe.model_dump(),
    }


def configure_log(
    session: SessionState,
    uart_port: str | None = None,
    uart_baudrate: int | None = None,
) -> dict:
    """Set UART log channel parameters."""
    if uart_port is not None:
        session.config.log.port = uart_port
    if uart_baudrate is not None:
        session.config.log.baudrate = uart_baudrate
    return {
        "status": "ok",
        "summary": "Updated log configuration.",
        "log": session.config.log.model_dump(),
    }


def configure_elf(
    session: SessionState,
    elf_path: str,
) -> dict:
    """Set the path to the ELF/AXF file for symbol resolution."""
    session.config.elf.path = elf_path
    return {
        "status": "ok",
        "summary": f"ELF path set to {elf_path}.",
        "elf": session.config.elf.model_dump(),
    }


def configure_build(
    session: SessionState,
    uv4_path: str | None = None,
    project_path: str | None = None,
    target_name: str | None = None,
    build_log_path: str | None = None,
    flash_log_path: str | None = None,
) -> dict:
    """Set Keil UV4 build/flash parameters.

    Note: build_project and flash_firmware currently require Keil UV4.
    This tool is only needed if you use those features.
    """
    if uv4_path is not None:
        session.config.build.uv4_path = uv4_path
    if project_path is not None:
        session.config.build.project_path = project_path
    if target_name is not None:
        session.config.build.target_name = target_name
    if build_log_path is not None:
        session.config.build.build_log_path = build_log_path
    if flash_log_path is not None:
        session.config.build.flash_log_path = flash_log_path
    return {
        "status": "ok",
        "summary": "Updated Keil UV4 build configuration.",
        "build": session.config.build.model_dump(),
    }


def connect_with_config(session: SessionState) -> dict:
    target = session.config.probe.target
    uart_port = session.config.log.port
    elf_path = session.config.elf.path

    results: dict[str, dict] = {}
    missing = []
    errors: dict[str, str] = {}

    if not target:
        missing.append("probe.target")
    else:
        try:
            results["probe"] = session.probe.connect(
                target=target,
                unique_id=session.config.probe.unique_id,
            )
        except Exception as exc:
            errors["probe"] = str(exc)

    if not uart_port:
        missing.append("log.port")
    else:
        try:
            results["log"] = session.log.connect(
                port=uart_port,
                baudrate=session.config.log.baudrate,
            )
        except Exception as exc:
            errors["log"] = str(exc)

    if not elf_path:
        missing.append("elf.path")
    else:
        try:
            results["elf"] = session.elf.load(elf_path)
        except Exception as exc:
            errors["elf"] = str(exc)

    if missing or errors:
        status = "partial"
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if errors:
            details.append(
                "errors: " + ", ".join(f"{name}={message}" for name, message in errors.items())
            )
        summary = "Connected available configured resources; " + "; ".join(details) + "."
    else:
        status = "ok"
        summary = "Connected configured resources."
    return {
        "status": status,
        "summary": summary,
        "results": results,
        "missing": missing,
        "errors": errors,
        "config": session.config.model_dump(),
    }
