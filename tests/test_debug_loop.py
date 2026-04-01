from mcudbg.config import RuntimeConfig
from mcudbg.demo.mock_session import MockSessionState
from mcudbg.tools.debug_loop import run_debug_loop


class _HealthyLogBackend:
    def __init__(self) -> None:
        self._connected = False

    def connect(self, port: str, baudrate: int = 115200) -> dict:
        self._connected = True
        return {
            "status": "ok",
            "summary": f"Connected healthy mock UART on {port} at {baudrate} baud.",
        }

    def disconnect(self) -> dict:
        self._connected = False
        return {"status": "ok", "summary": "Disconnected healthy mock UART."}

    def read_recent(self, line_count: int = 50) -> list[str]:
        return [
            "boot start",
            "clock init ok",
            "uart init ok",
            "sensor init...",
            "sensor init ok",
            "app loop running",
        ][-line_count:]


class _HealthyProbeBackend:
    def __init__(self) -> None:
        self._connected = False

    def connect(self, target: str, unique_id: str | None = None) -> dict:
        self._connected = True
        return {"status": "ok", "summary": f"Connected healthy mock target {target}."}

    def disconnect(self) -> dict:
        self._connected = False
        return {"status": "ok", "summary": "Disconnected healthy mock probe."}

    def halt(self) -> dict:
        return {"status": "ok", "summary": "Healthy mock target halted."}

    def reset(self, halt: bool = False) -> dict:
        return {"status": "ok", "summary": "Healthy mock target reset."}

    def read_core_registers(self) -> dict[str, int]:
        return {
            "pc": 0x0800237E,
            "lr": 0x08002351,
            "sp": 0x2000079C,
            "xpsr": 0x81000000,
        }

    def read_fault_registers(self) -> dict[str, int]:
        return {
            "cfsr": 0x0,
            "hfsr": 0x0,
            "mmfar": 0xE000EDF8,
            "bfar": 0xE000EDF8,
            "shcsr": 0x0,
        }


class _HealthyElfManager:
    is_loaded = True

    def load(self, path: str) -> dict:
        return {"status": "ok", "summary": f"Loaded healthy mock ELF from {path}."}

    def resolve_address(self, address: int) -> dict:
        mapping = {
            0x0800237E: {"symbol": "delay_us", "source": None},
            0x08002351: {"symbol": "delay_ms", "source": None},
        }
        return mapping.get(address, {"symbol": None, "source": None})


class _HealthyBuildRuntime:
    def build(self, build, elf, timeout_seconds: int = 120) -> dict:
        return {"status": "ok", "summary": "healthy mock build ok"}

    def flash(self, build, elf, timeout_seconds: int = 120) -> dict:
        return {"status": "ok", "summary": "healthy mock flash ok"}


class _HealthySession:
    def __init__(self) -> None:
        self.probe = _HealthyProbeBackend()
        self.log = _HealthyLogBackend()
        self.elf = _HealthyElfManager()
        self.build = _HealthyBuildRuntime()
        self.config = RuntimeConfig()
        self.config.probe.target = "cortex_m"
        self.config.log.port = "COM3"
        self.config.elf.path = "firmware.axf"


def test_run_debug_loop_returns_hardfault_path_for_led_not_blinking() -> None:
    session = MockSessionState()
    session.config = RuntimeConfig()
    session.config.probe.target = "stm32l4"
    session.config.log.port = "COM-MOCK"
    session.config.elf.path = "firmware.elf"

    result = run_debug_loop(
        session,
        issue_description="板子灯不闪",
        log_tail_lines=20,
        suspected_stage="sensor init",
    )

    assert result["status"] == "ok"
    assert result["symptom_class"] == "led_not_blinking"
    assert result["final_diagnosis"]["diagnosis_type"] == "hardfault_detected"


def test_run_debug_loop_returns_successful_startup_when_logs_are_healthy() -> None:
    session = _HealthySession()

    result = run_debug_loop(
        session,
        issue_description="板子灯不闪",
        log_tail_lines=20,
        suspected_stage="sensor init",
    )

    assert result["status"] == "ok"
    assert result["final_diagnosis"]["diagnosis_type"] == "startup_completed_normally"
