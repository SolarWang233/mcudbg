from __future__ import annotations

from dataclasses import dataclass, field

from .mock_backends import MockProbeBackend
from .mock_elf import MockElfManager
from .mock_logs import MockLogBackend


@dataclass
class MockSessionState:
    probe: MockProbeBackend = field(default_factory=MockProbeBackend)
    log: MockLogBackend = field(default_factory=MockLogBackend)
    elf: MockElfManager = field(default_factory=MockElfManager)
