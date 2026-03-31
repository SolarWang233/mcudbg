from __future__ import annotations

from typing import Any

from ...errors import BackendUnavailableError
from .base import ProbeBackend

try:
    from pyocd.core.helpers import ConnectHelper
except ImportError:  # pragma: no cover
    ConnectHelper = None


class PyOcdProbeBackend(ProbeBackend):
    """Minimal pyOCD probe backend for v0.1."""

    def __init__(self) -> None:
        self._session = None
        self._target = None
        self._probe_name = "pyocd"

    def connect(self, target: str, unique_id: str | None = None) -> dict[str, Any]:
        if ConnectHelper is None:
            raise BackendUnavailableError("pyocd is not installed")

        if self._session is not None:
            self.disconnect()

        session = ConnectHelper.session_with_chosen_probe(
            unique_id=unique_id,
            target_override=target,
            frequency=4000000,
            blocking=False,
            connect_mode="attach",
        )
        if session is None:
            raise BackendUnavailableError("no supported pyOCD probe could be opened")

        session.open()
        self._session = session
        self._target = session.target
        return {
            "status": "ok",
            "summary": f"Connected to target {target} via pyOCD probe backend.",
            "backend": self._probe_name,
            "target": target,
        }

    def disconnect(self) -> dict[str, Any]:
        if self._session is not None:
            self._session.close()
        self._session = None
        self._target = None
        return {"status": "ok", "summary": "Disconnected probe session."}

    def halt(self) -> dict[str, Any]:
        self._require_target()
        self._target.halt()
        return {"status": "ok", "summary": "Target halted."}

    def resume(self) -> dict[str, Any]:
        self._require_target()
        self._target.resume()
        return {"status": "ok", "summary": "Target resumed."}

    def reset(self, halt: bool = False) -> dict[str, Any]:
        self._require_target()
        if halt:
            self._target.reset_and_halt()
            return {"status": "ok", "summary": "Target reset and halted."}
        self._target.reset()
        return {"status": "ok", "summary": "Target reset."}

    def read_core_registers(self) -> dict[str, int]:
        self._require_target()
        names = ["pc", "lr", "sp", "xpsr"]
        return {name: int(self._target.read_core_register(name)) for name in names}

    def read_fault_registers(self) -> dict[str, int]:
        self._require_target()
        fault_map = {
            "cfsr": 0xE000ED28,
            "hfsr": 0xE000ED2C,
            "mmfar": 0xE000ED34,
            "bfar": 0xE000ED38,
            "shcsr": 0xE000ED24,
        }
        return {
            name: int(self._target.read32(address))
            for name, address in fault_map.items()
        }

    def read_memory(self, address: int, size: int) -> bytes:
        self._require_target()
        data = self._target.read_memory_block8(address, size)
        return bytes(data)

    def _require_target(self) -> None:
        if self._target is None:
            raise BackendUnavailableError("probe target is not connected")
