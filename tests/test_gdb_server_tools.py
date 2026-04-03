from __future__ import annotations

from types import SimpleNamespace

from mcudbg.gdb_server import GdbServerRuntime
from mcudbg.tools.gdb_server import get_gdb_server_status, start_gdb_server, stop_gdb_server


class _FakeProcess:
    def __init__(self, poll_result=None) -> None:
        self._poll_result = poll_result
        self.returncode = poll_result
        self.terminated = False
        self.killed = False
        self.wait_timeout = None

    def poll(self):
        return self._poll_result

    def terminate(self) -> None:
        self.terminated = True
        self._poll_result = 0
        self.returncode = 0

    def wait(self, timeout=None):
        self.wait_timeout = timeout
        self._poll_result = 0
        self.returncode = 0
        return 0

    def kill(self) -> None:
        self.killed = True
        self._poll_result = -9
        self.returncode = -9


def test_start_gdb_server_uses_session_defaults() -> None:
    calls: list[dict] = []
    session = SimpleNamespace(
        config=SimpleNamespace(
            probe=SimpleNamespace(target="stm32l496vetx", unique_id="1234"),
            elf=SimpleNamespace(path="D:/demo/firmware.axf"),
        ),
        gdb_server=SimpleNamespace(
            start=lambda **kwargs: calls.append(kwargs) or {"status": "ok", "summary": "started"},
        ),
    )

    result = start_gdb_server(session, port=3335, persist=True)

    assert result["status"] == "ok"
    assert calls == [{
        "target": "stm32l496vetx",
        "unique_id": "1234",
        "port": 3335,
        "telnet_port": 4444,
        "probe_server_port": 5555,
        "allow_remote": False,
        "persist": True,
        "elf_path": "D:/demo/firmware.axf",
        "cwd": "D:\\demo",
    }]


def test_start_gdb_server_requires_target() -> None:
    session = SimpleNamespace(
        config=SimpleNamespace(
            probe=SimpleNamespace(target=None, unique_id=None),
            elf=SimpleNamespace(path=None),
        ),
        gdb_server=SimpleNamespace(),
    )

    result = start_gdb_server(session)

    assert result["status"] == "error"


def test_status_and_stop_wrap_runtime() -> None:
    session = SimpleNamespace(
        gdb_server=SimpleNamespace(
            status=lambda: {"running": True, "host": "127.0.0.1", "port": 3333},
            stop=lambda timeout_seconds=5.0: {"status": "ok", "summary": "stopped", "timeout": timeout_seconds},
        )
    )

    status = get_gdb_server_status(session)
    stopped = stop_gdb_server(session, timeout_seconds=2.5)

    assert status["status"] == "ok"
    assert status["running"] is True
    assert stopped["status"] == "ok"
    assert stopped["timeout"] == 2.5


def test_runtime_status_reflects_running_process() -> None:
    runtime = GdbServerRuntime()
    runtime._process = _FakeProcess()
    runtime._host = "127.0.0.1"
    runtime._port = 3333

    status = runtime.status()

    assert status["running"] is True
    assert status["state"] == "running"


def test_runtime_stop_terminates_process() -> None:
    runtime = GdbServerRuntime()
    runtime._process = _FakeProcess()
    runtime._host = "127.0.0.1"
    runtime._port = 3333

    result = runtime.stop(timeout_seconds=1.5)

    assert result["status"] == "ok"
    assert result["running"] is False
    assert result["exit_code"] == 0
