from mcudbg.demo.mock_session import MockSessionState
from mcudbg.tools.diagnose import diagnose_hardfault, diagnose_startup_failure


def test_mock_startup_failure_contains_sensor_stage() -> None:
    session = MockSessionState()
    session.log.connect("COM-MOCK")
    session.probe.connect("stm32l4")
    session.elf.load("firmware.elf")

    result = diagnose_startup_failure(session, suspected_stage="sensor init")

    assert result["diagnosis_type"] == "startup_failure_with_fault"
    assert result["startup_context"]["suspected_stage"] == "sensor init"
    assert result["log_context"]["last_meaningful_line"] == "sensor init..."


def test_mock_hardfault_resolves_handler_symbol() -> None:
    session = MockSessionState()
    session.log.connect("COM-MOCK")
    session.probe.connect("stm32l4")
    session.elf.load("firmware.elf")

    result = diagnose_hardfault(session, suspected_stage="sensor init")

    assert result["diagnosis_type"] == "hardfault_detected"
    assert result["symbol_context"]["pc_symbol"] == "HardFault_Handler"
