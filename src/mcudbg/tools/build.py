from __future__ import annotations

from ..session import SessionState


def build_project(session: SessionState, timeout_seconds: int = 120) -> dict:
    return session.build.build(
        build=session.config.build,
        elf=session.config.elf,
        timeout_seconds=timeout_seconds,
    )


def flash_firmware(session: SessionState, timeout_seconds: int = 120) -> dict:
    return session.build.flash(
        build=session.config.build,
        elf=session.config.elf,
        timeout_seconds=timeout_seconds,
    )
