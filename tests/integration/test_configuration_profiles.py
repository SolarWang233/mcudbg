from mcudbg.config import get_builtin_profiles
from mcudbg.session import SessionState
from mcudbg.tools.configuration import (
    configure_build,
    configure_elf,
    configure_log,
    configure_probe,
    get_target_info,
    load_demo_profile,
    match_chip_name,
)


def test_builtin_profile_exists() -> None:
    profiles = get_builtin_profiles()
    assert "stm32l4_atk_led_demo" in profiles


def test_load_demo_profile_updates_runtime_config() -> None:
    session = SessionState()
    result = load_demo_profile(session, "stm32l4_atk_led_demo")

    assert result["status"] == "ok"
    assert session.config.active_profile == "stm32l4_atk_led_demo"
    assert session.config.probe.target == "stm32l496vetx"
    assert session.config.log.baudrate == 115200
    assert session.config.build.target_name is None


def test_configure_probe_overrides_target() -> None:
    session = SessionState()
    result = configure_probe(session, target="stm32l4x", unique_id="abc123")
    assert result["status"] == "ok"
    assert session.config.probe.target == "stm32l4x"
    assert session.config.probe.unique_id == "abc123"


def test_configure_log_overrides_port() -> None:
    session = SessionState()
    result = configure_log(session, uart_port="COM7", uart_baudrate=9600)
    assert result["status"] == "ok"
    assert session.config.log.port == "COM7"
    assert session.config.log.baudrate == 9600


def test_configure_elf_sets_path() -> None:
    session = SessionState()
    result = configure_elf(session, elf_path=r"d:\demo\firmware.axf")
    assert result["status"] == "ok"
    assert session.config.elf.path == r"d:\demo\firmware.axf"


def test_configure_build_sets_keil_params() -> None:
    session = SessionState()
    load_demo_profile(session, "stm32l4_atk_led_demo")
    result = configure_build(
        session,
        uv4_path=r"E:\software\MDK\UV4\UV4.exe",
        project_path=r"d:\demo\firmware.uvprojx",
        target_name="demo_target",
    )
    assert result["status"] == "ok"
    assert session.config.build.uv4_path == r"E:\software\MDK\UV4\UV4.exe"
    assert session.config.build.project_path == r"d:\demo\firmware.uvprojx"
    assert session.config.build.target_name == "demo_target"


def test_match_chip_name_resolves_known_jlink_alias() -> None:
    result = match_chip_name("STM32F103C8T6", backend="jlink")

    assert result["status"] == "ok"
    assert result["matched_target"] == "STM32F103C8"
    assert result["confidence"] == "high"


def test_configure_probe_normalizes_known_pyocd_alias() -> None:
    session = SessionState()

    result = configure_probe(session, target="STM32L496VE", backend="pyocd")

    assert result["status"] == "ok"
    assert session.config.probe.target == "stm32l496vetx"
    assert result["target_match"]["matched_target"] == "stm32l496vetx"
    assert result["target_patch"]["patch_applied"] is True


def test_get_target_info_reports_patch_metadata() -> None:
    result = get_target_info("STM32F103C8T6", backend="jlink")

    assert result["status"] == "ok"
    assert result["matched_target"] == "STM32F103C8"
    assert result["patch_applied"] is True
