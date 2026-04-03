from __future__ import annotations

from types import SimpleNamespace

import mcudbg.backends.probe.jlink_backend as jlink_backend
from mcudbg.session import SessionState, create_probe_backend
from mcudbg.tools.configuration import configure_probe


class _FakeLibrary:
    def __init__(self, path: str) -> None:
        self._path = path


class _FakeJLink:
    def __init__(self, lib=None) -> None:
        self.lib = lib
        self.open_calls: list[int | None] = []
        self.connected_target = None
        self.closed = False
        self.breakpoints: list[int] = []

    def open(self, serial_no=None) -> None:
        self.open_calls.append(serial_no)

    def set_tif(self, interface) -> None:
        self.interface = interface

    def connect(self, target: str) -> None:
        self.connected_target = target

    def close(self) -> None:
        self.closed = True

    def halt(self) -> None:
        pass

    def restart(self) -> None:
        pass

    def reset(self, halt: bool = False) -> None:
        self.reset_halt = halt

    def breakpoint_set(self, address: int) -> None:
        self.breakpoints.append(address)

    def breakpoint_clear(self, address: int) -> None:
        self.breakpoints = [bp for bp in self.breakpoints if bp != address]

    def breakpoint_clear_all(self) -> None:
        self.breakpoints.clear()

    def halted(self) -> bool:
        return True

    def register_read(self, name: str) -> int:
        return {
            "R15 (PC)": 0x08001234,
            "R13 (SP)": 0x20001000,
            "R14": 0x08000101,
            "XPSR": 0x21000000,
        }.get(name, 0)

    def memory_read32(self, address: int, count: int) -> list[int]:
        return [address]

    def memory_read8(self, address: int, size: int) -> list[int]:
        return [(address + i) & 0xFF for i in range(size)]

    def memory_write8(self, address: int, data: list[int]) -> None:
        self.last_write = (address, data)

    def step(self) -> None:
        pass

    # -- Watchpoint stubs --
    def watchpoint_set(self, addr, addr_mask=0, data=0, data_mask=0, access_size=None, read=False, write=False, privileged=False) -> int:
        handle = id(addr)
        if not hasattr(self, "_watchpoints"):
            self._watchpoints = {}
        self._watchpoints[handle] = (addr, access_size, read, write)
        return handle

    def watchpoint_clear(self, handle: int) -> None:
        if hasattr(self, "_watchpoints"):
            self._watchpoints.pop(handle, None)

    def watchpoint_clear_all(self) -> None:
        if hasattr(self, "_watchpoints"):
            self._watchpoints.clear()

    # -- Flash stubs --
    def erase(self, start_address=None, size=None) -> None:
        self.last_erase = (start_address, size)

    def flash_write(self, address: int, data: list[int]) -> None:
        self.last_flash_write = (address, data)

    def connected_emulators(self, host=1):
        return [SimpleNamespace(SerialNumber=12345678, acProduct="J-Link EDU")]


def _fake_library_module():
    return SimpleNamespace(Library=lambda path: _FakeLibrary(path))


def _fake_pylink_module(fake):
    def _make_jlink(lib=None):
        fake.lib = lib
        return fake

    return SimpleNamespace(
        JLink=_make_jlink,
        enums=SimpleNamespace(JLinkInterfaces=SimpleNamespace(SWD="SWD")),
    )


def test_configure_probe_switches_to_jlink_backend() -> None:
    session = SessionState()

    result = configure_probe(
        session,
        backend="jlink",
        target="stm32l4",
        unique_id="123456",
        jlink_dll_path="E:/software/jlink/JLink_x64.dll",
    )

    assert result["status"] == "ok"
    assert session.config.probe.backend == "jlink"
    assert session.config.probe.target == "stm32l4"
    assert session.config.probe.unique_id == "123456"
    assert session.config.probe.jlink_dll_path == "E:/software/jlink/JLink_x64.dll"
    assert session.probe.__class__.__name__ == "JLinkProbeBackend"


def test_configure_probe_rejects_unknown_backend() -> None:
    session = SessionState()

    result = configure_probe(session, backend="unknown")

    assert result["status"] == "error"
    assert "Unknown probe backend" in result["summary"]


def test_create_probe_backend_supports_jlink() -> None:
    probe = create_probe_backend("jlink", jlink_dll_path="E:/software/jlink/JLink_x64.dll")

    assert probe.__class__.__name__ == "JLinkProbeBackend"


def test_jlink_backend_connects_and_reads_memory(monkeypatch) -> None:
    fake = _FakeJLink()
    fake_module = _fake_pylink_module(fake)
    monkeypatch.setattr(jlink_backend, "pylink", fake_module)
    monkeypatch.setattr(jlink_backend, "pylink_library", _fake_library_module())
    monkeypatch.setattr(jlink_backend.JLinkProbeBackend, "_resolve_dll_path", classmethod(lambda cls, dll_path=None: dll_path or "E:/software/jlink/JLink_x64.dll"))

    backend = jlink_backend.JLinkProbeBackend(dll_path="E:/software/jlink/JLink_x64.dll")
    result = backend.connect(target="stm32l496vetx", unique_id="123456")

    assert result["status"] == "ok"
    assert fake.open_calls == [123456]
    assert fake.connected_target == "stm32l496vetx"
    assert backend.read_memory(0x20000000, 4) == b"\x00\x01\x02\x03"
    assert result["dll_path"] == "E:/software/jlink/JLink_x64.dll"


def test_jlink_backend_enumerates_connected_emulators(monkeypatch) -> None:
    fake_module = _fake_pylink_module(_FakeJLink())
    monkeypatch.setattr(jlink_backend, "pylink", fake_module)
    monkeypatch.setattr(jlink_backend, "pylink_library", _fake_library_module())
    monkeypatch.setattr(jlink_backend.JLinkProbeBackend, "_resolve_dll_path", classmethod(lambda cls, dll_path=None: dll_path or "E:/software/jlink/JLink_x64.dll"))

    probes = jlink_backend.JLinkProbeBackend.enumerate_probes()

    assert probes == [
        {
            "unique_id": "12345678",
            "description": "J-Link 12345678",
            "product": "J-Link EDU",
        }
    ]


def _make_connected_backend(monkeypatch):
    """Helper: return a connected JLinkProbeBackend with fake pylink."""
    fake = _FakeJLink()
    fake_module = _fake_pylink_module(fake)
    monkeypatch.setattr(jlink_backend, "pylink", fake_module)
    monkeypatch.setattr(jlink_backend, "pylink_library", _fake_library_module())
    monkeypatch.setattr(jlink_backend.JLinkProbeBackend, "_resolve_dll_path", classmethod(lambda cls, dll_path=None: dll_path or "E:/software/jlink/JLink_x64.dll"))
    backend = jlink_backend.JLinkProbeBackend(dll_path="E:/software/jlink/JLink_x64.dll")
    backend.connect(target="stm32l496vetx")
    return backend, fake


# -- Watchpoint tests --

def test_jlink_watchpoint_set_and_remove(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    result = backend.set_watchpoint(0x20000000, size=4, watch_type="write")
    assert result["status"] == "ok"
    assert result["watch_type"] == "write"
    assert 0x20000000 in backend._watchpoints

    result = backend.remove_watchpoint(0x20000000)
    assert result["status"] == "ok"
    assert 0x20000000 not in backend._watchpoints


def test_jlink_watchpoint_clear_all(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    backend.set_watchpoint(0x20000000, size=4, watch_type="read")
    backend.set_watchpoint(0x20000100, size=2, watch_type="write")

    result = backend.clear_all_watchpoints()
    assert result["status"] == "ok"
    assert result["cleared_count"] == 2
    assert len(backend._watchpoints) == 0


def test_jlink_watchpoint_invalid_type(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    try:
        backend.set_watchpoint(0x20000000, size=4, watch_type="invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "invalid" in str(e).lower()


# -- FPU register tests --

def test_jlink_read_fpu_registers(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    result = backend.read_fpu_registers()
    assert "s0" in result
    assert "s31" in result
    assert "fpscr" in result
    assert len([k for k in result if k.startswith("s")]) == 32


# -- Flash tests --

def test_jlink_erase_flash_chip(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    result = backend.erase_flash(chip_erase=True)
    assert result["status"] == "ok"
    assert result["chip_erase"] is True


def test_jlink_erase_flash_range(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    result = backend.erase_flash(start_address=0x08000000, end_address=0x08010000)
    assert result["status"] == "ok"
    assert result["chip_erase"] is False


def test_jlink_program_flash(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    data = bytes([0xAA, 0xBB, 0xCC, 0xDD])
    # Make memory_read8 return the same data so verify passes
    fake.memory_read8 = lambda addr, size: list(data)

    result = backend.program_flash(0x08000000, data, verify=True)
    assert result["status"] == "ok"
    assert result["size"] == 4


def test_jlink_verify_flash_match(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    data = bytes([0x01, 0x02, 0x03])
    fake.memory_read8 = lambda addr, size: list(data)

    result = backend.verify_flash(0x08000000, data)
    assert result["status"] == "ok"
    assert result["match"] is True


def test_jlink_verify_flash_mismatch(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    data = bytes([0x01, 0x02, 0x03])
    fake.memory_read8 = lambda addr, size: [0x01, 0xFF, 0x03]

    result = backend.verify_flash(0x08000000, data)
    assert result["status"] == "error"
    assert result["match"] is False
    assert result["mismatch_count"] == 1
    assert result["first_mismatch_address"] == hex(0x08000001)


def test_jlink_disconnect_clears_watchpoints(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    backend.set_watchpoint(0x20000000, size=4, watch_type="write")
    assert len(backend._watchpoints) == 1

    backend.disconnect()
    assert len(backend._watchpoints) == 0


def test_jlink_read_core_registers_uses_aliases(monkeypatch) -> None:
    backend, fake = _make_connected_backend(monkeypatch)

    result = backend.read_core_registers()

    assert result["pc"] == 0x08001234
    assert result["sp"] == 0x20001000
    assert result["lr"] == 0x08000101
