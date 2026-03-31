from __future__ import annotations


class MockProbeBackend:
    """Deterministic probe backend for demo and local development."""

    def __init__(self) -> None:
        self._connected = False
        self._halted = False

    def connect(self, target: str, unique_id: str | None = None) -> dict:
        self._connected = True
        return {
            "status": "ok",
            "summary": f"Connected to mock target {target} via CMSIS-DAP.",
            "backend": "mock-cmsis-dap",
            "target": target,
            "unique_id": unique_id,
        }

    def disconnect(self) -> dict:
        self._connected = False
        self._halted = False
        return {"status": "ok", "summary": "Disconnected mock probe session."}

    def halt(self) -> dict:
        self._require_connected()
        self._halted = True
        return {"status": "ok", "summary": "Mock target halted."}

    def resume(self) -> dict:
        self._require_connected()
        self._halted = False
        return {"status": "ok", "summary": "Mock target resumed."}

    def reset(self, halt: bool = False) -> dict:
        self._require_connected()
        self._halted = halt
        if halt:
            return {"status": "ok", "summary": "Mock target reset and halted."}
        return {"status": "ok", "summary": "Mock target reset."}

    def read_core_registers(self) -> dict[str, int]:
        self._require_connected()
        return {
            "pc": 0x08001234,
            "lr": 0x08004567,
            "sp": 0x20001F80,
            "xpsr": 0x21000000,
        }

    def read_fault_registers(self) -> dict[str, int]:
        self._require_connected()
        return {
            "cfsr": 0x00008200,
            "hfsr": 0x40000000,
            "mmfar": 0x00000000,
            "bfar": 0x20010000,
            "shcsr": 0x00070000,
        }

    def read_memory(self, address: int, size: int) -> bytes:
        self._require_connected()
        pattern = bytes.fromhex("80 1F 00 20 34 12 00 08 67 45 00 08 AA BB CC DD")
        data = (pattern * ((size // len(pattern)) + 1))[:size]
        return data

    def _require_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("mock probe is not connected")
