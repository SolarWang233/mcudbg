from __future__ import annotations

from ..session import SessionState


def build_project(session: SessionState, timeout_seconds: int = 120) -> dict:
    return session.build.build(
        build=session.config.build,
        elf=session.config.elf,
        timeout_seconds=timeout_seconds,
    )


def flash_firmware(session: SessionState, timeout_seconds: int = 120) -> dict:
    disconnect_note = None
    try:
        disconnect_note = session.probe.disconnect()
    except Exception:
        disconnect_note = None

    result = session.build.flash(
        build=session.config.build,
        elf=session.config.elf,
        timeout_seconds=timeout_seconds,
    )
    if disconnect_note:
        result["probe_disconnect"] = disconnect_note
    return result
