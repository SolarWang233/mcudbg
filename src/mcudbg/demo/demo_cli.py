from __future__ import annotations

import json

from ..tools.diagnose import diagnose_hardfault, diagnose_startup_failure
from .mock_session import MockSessionState


def run_demo() -> None:
    session = MockSessionState()

    print("== mcudbg mock demo ==")
    print()
    print("User: This STM32L4 board doesn't boot after power-on. Help me inspect it.")
    print()

    print("[1/4] Connect UART log")
    print(json.dumps(session.log.connect(port="COM-MOCK", baudrate=115200), indent=2))
    print()

    print("[2/4] Connect CMSIS-DAP probe")
    print(json.dumps(session.probe.connect(target="stm32l4"), indent=2))
    print()

    print("[3/4] Load ELF")
    print(json.dumps(session.elf.load("firmware.elf"), indent=2))
    print()

    print("[4/4] Diagnose startup failure")
    startup = diagnose_startup_failure(session, suspected_stage="sensor init")
    print(json.dumps(startup, indent=2))
    print()

    print("HardFault-focused result")
    hardfault = diagnose_hardfault(session, suspected_stage="sensor init")
    print(json.dumps(hardfault, indent=2))


if __name__ == "__main__":
    run_demo()
