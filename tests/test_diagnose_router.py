from __future__ import annotations

from types import SimpleNamespace

import mcudbg.tools.diagnose_router as diagnose_router


def test_diagnose_routes_hardfault(monkeypatch) -> None:
    session = SimpleNamespace()
    monkeypatch.setattr(
        diagnose_router,
        "diagnose_hardfault",
        lambda session, **kwargs: {"status": "ok", "summary": "hardfault details"},
    )

    result = diagnose_router.diagnose(session, symptom="Board crashed into HardFault")

    assert result["status"] == "ok"
    assert result["diagnose_route"] == "diagnose_hardfault"
    assert result["summary"].startswith("Routed to hardfault diagnosis:")


def test_diagnose_routes_peripheral_and_infers_name(monkeypatch) -> None:
    session = SimpleNamespace()
    calls: list[tuple[str, str | None]] = []

    def _fake_peripheral(session, peripheral, symptom=None):
        calls.append((peripheral, symptom))
        return {"status": "ok", "summary": "peripheral details"}

    monkeypatch.setattr(diagnose_router, "diagnose_peripheral_stuck", _fake_peripheral)

    result = diagnose_router.diagnose(session, symptom="USART2 no output from TX pin")

    assert result["status"] == "ok"
    assert result["diagnose_route"] == "diagnose_peripheral_stuck"
    assert result["peripheral"] == "USART2"
    assert calls == [("USART2", "USART2 no output from TX pin")]


def test_diagnose_routes_clock_issue(monkeypatch) -> None:
    session = SimpleNamespace()
    monkeypatch.setattr(
        diagnose_router,
        "diagnose_clock_issue",
        lambda session: {"status": "ok", "summary": "clock details"},
    )

    result = diagnose_router.diagnose(session, symptom="PLL clock switch is stuck")

    assert result["status"] == "ok"
    assert result["diagnose_route"] == "diagnose_clock_issue"


def test_diagnose_falls_back_to_startup(monkeypatch) -> None:
    session = SimpleNamespace()
    monkeypatch.setattr(
        diagnose_router,
        "diagnose_startup_failure",
        lambda session, **kwargs: {"status": "ok", "summary": "startup details"},
    )

    result = diagnose_router.diagnose(session, symptom="Board does not boot")

    assert result["status"] == "ok"
    assert result["diagnose_route"] == "diagnose_startup_failure"


def test_diagnose_requires_non_empty_symptom() -> None:
    session = SimpleNamespace()

    result = diagnose_router.diagnose(session, symptom="  ")

    assert result["status"] == "error"
