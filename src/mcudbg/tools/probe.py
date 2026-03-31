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


def read_registers(session: SessionState) -> dict:
    values = session.probe.read_core_registers()
    return {
        "status": "ok",
        "summary": "Read core registers.",
        "registers": {name: hex(value) for name, value in values.items()},
    }
