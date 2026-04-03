from __future__ import annotations

import time
from typing import Any

from ...errors import BackendUnavailableError
from .base import ProbeBackend

try:
    from pyocd.core.helpers import ConnectHelper
    from pyocd.core.target import Target
except ImportError:  # pragma: no cover
    ConnectHelper = None
    Target = None


class PyOcdProbeBackend(ProbeBackend):
    """Minimal pyOCD probe backend for v0.1."""

    @classmethod
    def enumerate_probes(cls) -> list[dict]:
        if ConnectHelper is None:
            return []
        try:
            probes = ConnectHelper.get_all_connected_probes(blocking=False)
            return [
                {
                    "unique_id": probe.unique_id,
                    "description": probe.description,
                    "vendor_name": getattr(probe, "vendor_name", None),
                    "product_name": getattr(probe, "product_name", None),
                }
                for probe in probes
            ]
        except Exception:
            return []

    def __init__(self) -> None:
        self._session = None
        self._target = None
        self._probe_name = "pyocd"
        self._breakpoints: set[int] = set()
        self._watchpoints: set[int] = set()

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
        self._breakpoints.clear()
        self._watchpoints.clear()
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

    def set_breakpoint(self, address: int) -> dict[str, Any]:
        self._require_target()
        success = bool(self._target.set_breakpoint(address))
        if not success:
            raise BackendUnavailableError(f"failed to set breakpoint at {hex(address)}")
        self._breakpoints.add(address)
        return {
            "status": "ok",
            "summary": f"Breakpoint set at {hex(address)}.",
            "address": hex(address),
        }

    def clear_breakpoint(self, address: int) -> dict[str, Any]:
        self._require_target()
        self._target.remove_breakpoint(address)
        self._breakpoints.discard(address)
        return {
            "status": "ok",
            "summary": f"Breakpoint cleared at {hex(address)}.",
            "address": hex(address),
        }

    def clear_all_breakpoints(self) -> dict[str, Any]:
        self._require_target()
        for address in list(self._breakpoints):
            self._target.remove_breakpoint(address)
        cleared = len(self._breakpoints)
        self._breakpoints.clear()
        return {
            "status": "ok",
            "summary": f"Cleared {cleared} breakpoint(s).",
            "cleared_count": cleared,
        }

    def continue_target(
        self,
        timeout_seconds: float = 5.0,
        poll_interval_seconds: float = 0.05,
    ) -> dict[str, Any]:
        self._require_target()
        self._target.resume()

        deadline = time.monotonic() + timeout_seconds
        last_state = self._target.get_state()
        while time.monotonic() < deadline:
            state = self._target.get_state()
            last_state = state
            if Target is not None and state != Target.State.RUNNING:
                break
            time.sleep(poll_interval_seconds)
        else:
            self._target.halt()
            core = self.read_core_registers()
            return {
                "status": "ok",
                "summary": "Target did not stop before timeout and was halted for analysis.",
                "stop_reason": "timeout",
                "state": self.get_state(),
                "pc": hex(core["pc"]),
            }

        core = self.read_core_registers()
        stop_reason = self._infer_stop_reason(core["pc"], last_state)
        return {
            "status": "ok",
            "summary": "Target stopped after continue.",
            "stop_reason": stop_reason,
            "state": self.get_state(),
            "pc": hex(core["pc"]),
        }

    def get_state(self) -> str:
        self._require_target()
        state = self._target.get_state()
        return getattr(state, "name", str(state)).lower()

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

    def write_memory(self, address: int, data: bytes) -> None:
        self._require_target()
        self._target.write_memory_block8(address, list(data))

    def step(self) -> dict[str, Any]:
        self._require_target()
        self._target.step()
        core = self.read_core_registers()
        result: dict[str, Any] = {
            "status": "ok",
            "summary": "Executed one instruction.",
            "pc": hex(core["pc"]),
        }
        return result

    def _require_target(self) -> None:
        if self._target is None:
            raise BackendUnavailableError("probe target is not connected")

    def _infer_stop_reason(self, pc: int, state: Any) -> str:
        if Target is not None and state == Target.State.LOCKUP:
            return "fault"
        if self._matches_breakpoint(pc):
            return "breakpoint_hit"
        return "manual_halt"

    def _matches_breakpoint(self, pc: int) -> bool:
        if pc in self._breakpoints:
            return True
        if (pc - 2) in self._breakpoints:
            return True
        if (pc - 4) in self._breakpoints:
            return True
        return False

    def set_watchpoint(self, address: int, size: int, watch_type: str) -> dict[str, Any]:
        self._require_target()
        if Target is None:
            raise BackendUnavailableError('pyocd is not installed')
        type_map = {
            'read': Target.WatchpointType.READ,
            'write': Target.WatchpointType.WRITE,
            'read_write': Target.WatchpointType.READ_WRITE,
        }
        wp_type = type_map.get(watch_type)
        if wp_type is None:
            raise ValueError(f"Invalid watch_type '{watch_type}'. Use: read, write, read_write")
        self._target.set_watchpoint(address, size, wp_type)
        self._watchpoints.add(address)
        return {
            'status': 'ok',
            'summary': f'Watchpoint set at {hex(address)}, size={size}, type={watch_type}.',
            'address': hex(address),
            'size': size,
            'watch_type': watch_type,
        }

    def remove_watchpoint(self, address: int) -> dict[str, Any]:
        self._require_target()
        self._target.remove_watchpoint(address)
        self._watchpoints.discard(address)
        return {
            'status': 'ok',
            'summary': f'Watchpoint removed at {hex(address)}.',
            'address': hex(address),
        }

    def clear_all_watchpoints(self) -> dict[str, Any]:
        self._require_target()
        for address in list(self._watchpoints):
            self._target.remove_watchpoint(address)
        cleared = len(self._watchpoints)
        self._watchpoints.clear()
        return {
            'status': 'ok',
            'summary': f'Cleared {cleared} watchpoint(s).',
            'cleared_count': cleared,
        }

    def read_fpu_registers(self) -> dict[str, Any]:
        self._require_target()
        result: dict[str, Any] = {}
        for index in range(32):
            name = f"s{index}"
            try:
                result[name] = self._target.read_core_register(name)
            except Exception:
                result[name] = None
        try:
            result["fpscr"] = self._target.read_core_register("fpscr")
        except Exception:
            result["fpscr"] = None
        return result
