from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProbeBackend(ABC):
    @classmethod
    def enumerate_probes(cls) -> list[dict[str, Any]]:
        """Return a list of connected probes visible to this backend.

        Each entry should contain at minimum 'unique_id' and 'description'.
        Backends that do not support enumeration may return an empty list.
        """
        return []

    @abstractmethod
    def connect(self, target: str, unique_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def halt(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def resume(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def reset(self, halt: bool = False) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def set_breakpoint(self, address: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def clear_breakpoint(self, address: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def clear_all_breakpoints(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def continue_target(
        self,
        timeout_seconds: float = 5.0,
        poll_interval_seconds: float = 0.05,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_core_registers(self) -> dict[str, int]:
        raise NotImplementedError

    @abstractmethod
    def read_fault_registers(self) -> dict[str, int]:
        raise NotImplementedError

    @abstractmethod
    def read_memory(self, address: int, size: int) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def write_memory(self, address: int, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def step(self) -> dict[str, Any]:
        raise NotImplementedError

    def set_watchpoint(self, address: int, size: int, watch_type: str) -> dict[str, Any]:
        raise NotImplementedError

    def remove_watchpoint(self, address: int) -> dict[str, Any]:
        raise NotImplementedError

    def clear_all_watchpoints(self) -> dict[str, Any]:
        raise NotImplementedError

    def read_fpu_registers(self) -> dict[str, Any]:
        raise NotImplementedError
