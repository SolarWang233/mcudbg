from mcudbg.config import get_builtin_profiles
from mcudbg.session import SessionState
from mcudbg.tools.configuration import configure_target, load_demo_profile


def test_builtin_profile_exists() -> None:
    profiles = get_builtin_profiles()
    assert "stm32l4_atk_led_demo" in profiles


def test_load_demo_profile_updates_runtime_config() -> None:
    session = SessionState()
    result = load_demo_profile(session, "stm32l4_atk_led_demo")

    assert result["status"] == "ok"
    assert session.config.active_profile == "stm32l4_atk_led_demo"
    assert session.config.probe.target == "stm32l496ve"
    assert session.config.log.baudrate == 115200


def test_configure_target_overrides_runtime_values() -> None:
    session = SessionState()
    load_demo_profile(session, "stm32l4_atk_led_demo")

    result = configure_target(
        session,
        uart_port="COM7",
        elf_path=r"d:\demo\firmware.axf",
    )

    assert result["status"] == "ok"
    assert session.config.log.port == "COM7"
    assert session.config.elf.path == r"d:\demo\firmware.axf"
