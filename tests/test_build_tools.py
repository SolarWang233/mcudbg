from pathlib import Path

from mcudbg.config import BuildConfig, ElfConfig
from mcudbg.session import SessionState
from mcudbg.tools.build import build_project, flash_firmware


class _FakeBuildRuntime:
    def __init__(self) -> None:
        self.calls = []

    def build(self, build: BuildConfig, elf: ElfConfig, timeout_seconds: int = 120) -> dict:
        self.calls.append(("build", build, elf, timeout_seconds))
        return {
            "status": "ok",
            "summary": "fake build ok",
            "firmware": {"path": elf.path},
        }

    def flash(self, build: BuildConfig, elf: ElfConfig, timeout_seconds: int = 120) -> dict:
        self.calls.append(("flash", build, elf, timeout_seconds))
        return {
            "status": "ok",
            "summary": "fake flash ok",
            "firmware": {"path": elf.path},
        }


def test_build_project_uses_runtime_config() -> None:
    session = SessionState()
    session.config.build.uv4_path = r"E:\software\MDK\UV4\UV4.exe"
    session.config.build.project_path = r"d:\demo\app.uvprojx"
    session.config.build.target_name = "demo_target"
    session.config.elf.path = r"d:\demo\app.axf"
    session.build = _FakeBuildRuntime()

    result = build_project(session, timeout_seconds=33)

    assert result["status"] == "ok"
    assert session.build.calls[0][0] == "build"
    assert session.build.calls[0][1].target_name == "demo_target"
    assert session.build.calls[0][2].path == r"d:\demo\app.axf"
    assert session.build.calls[0][3] == 33


def test_flash_firmware_uses_runtime_config() -> None:
    session = SessionState()
    session.config.build.uv4_path = r"E:\software\MDK\UV4\UV4.exe"
    session.config.build.project_path = r"d:\demo\app.uvprojx"
    session.config.build.target_name = "demo_target"
    session.config.elf.path = r"d:\demo\app.axf"
    session.build = _FakeBuildRuntime()

    result = flash_firmware(session, timeout_seconds=44)

    assert result["status"] == "ok"
    assert session.build.calls[0][0] == "flash"
    assert session.build.calls[0][1].project_path == r"d:\demo\app.uvprojx"
    assert session.build.calls[0][2].path == r"d:\demo\app.axf"
    assert session.build.calls[0][3] == 44


def test_keil_build_runtime_collects_firmware_info(tmp_path: Path) -> None:
    from mcudbg.build_runtime import KeilBuildRuntime

    axf = tmp_path / "demo.axf"
    axf.write_bytes(b"demo")
    hex_path = tmp_path / "demo.hex"
    hex_path.write_text(":00000001FF", encoding="utf-8")

    info = KeilBuildRuntime._collect_firmware_info(str(axf))

    assert info is not None
    assert info["exists"] is True
    assert info["hex_exists"] is True
    assert info["path"].endswith("demo.axf")
