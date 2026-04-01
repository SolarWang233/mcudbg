from __future__ import annotations

from dataclasses import dataclass, field

from .backends.log.uart_backend import UartLogBackend
from .backends.probe.pyocd_backend import PyOcdProbeBackend
from .build_runtime import KeilBuildRuntime
from .config import RuntimeConfig
from .elf_manager import ElfManager
from .svd_manager import SvdManager


@dataclass
class SessionState:
    probe: PyOcdProbeBackend = field(default_factory=PyOcdProbeBackend)
    log: UartLogBackend = field(default_factory=UartLogBackend)
    elf: ElfManager = field(default_factory=ElfManager)
    svd: SvdManager = field(default_factory=SvdManager)
    build: KeilBuildRuntime = field(default_factory=KeilBuildRuntime)
    config: RuntimeConfig = field(default_factory=RuntimeConfig)
