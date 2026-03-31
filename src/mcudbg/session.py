from __future__ import annotations

from dataclasses import dataclass, field

from .backends.log.uart_backend import UartLogBackend
from .backends.probe.pyocd_backend import PyOcdProbeBackend
from .config import RuntimeConfig
from .elf_manager import ElfManager


@dataclass
class SessionState:
    probe: PyOcdProbeBackend = field(default_factory=PyOcdProbeBackend)
    log: UartLogBackend = field(default_factory=UartLogBackend)
    elf: ElfManager = field(default_factory=ElfManager)
    config: RuntimeConfig = field(default_factory=RuntimeConfig)
