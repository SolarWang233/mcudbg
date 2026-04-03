from __future__ import annotations

from pathlib import Path

from ..session import SessionState


def start_gdb_server(
    session: SessionState,
    port: int = 3333,
    telnet_port: int = 4444,
    probe_server_port: int = 5555,
    allow_remote: bool = False,
    persist: bool = False,
    target: str | None = None,
    unique_id: str | None = None,
    elf_path: str | None = None,
) -> dict:
    resolved_target = target or session.config.probe.target
    resolved_unique_id = unique_id if unique_id is not None else session.config.probe.unique_id
    resolved_elf_path = elf_path if elf_path is not None else session.config.elf.path

    if not resolved_target:
        return {
            "status": "error",
            "summary": "Target not configured. Pass target=... or call configure_probe first.",
        }

    cwd = None
    if resolved_elf_path:
        cwd = str(Path(resolved_elf_path).resolve().parent)

    try:
        return session.gdb_server.start(
            target=resolved_target,
            unique_id=resolved_unique_id,
            port=port,
            telnet_port=telnet_port,
            probe_server_port=probe_server_port,
            allow_remote=allow_remote,
            persist=persist,
            elf_path=resolved_elf_path,
            cwd=cwd,
        )
    except Exception as e:
        return {"status": "error", "summary": str(e)}


def stop_gdb_server(session: SessionState, timeout_seconds: float = 5.0) -> dict:
    try:
        return session.gdb_server.stop(timeout_seconds=timeout_seconds)
    except Exception as e:
        return {"status": "error", "summary": str(e)}


def get_gdb_server_status(session: SessionState) -> dict:
    try:
        status = session.gdb_server.status()
        return {
            "status": "ok",
            "summary": (
                f"GDB server is running on {status['host']}:{status['port']}."
                if status["running"]
                else "GDB server is not running."
            ),
            **status,
        }
    except Exception as e:
        return {"status": "error", "summary": str(e)}
