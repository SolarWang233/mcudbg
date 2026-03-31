from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ProbeConfig(BaseModel):
    backend: str = "pyocd"
    target: str | None = None
    unique_id: str | None = None


class LogConfig(BaseModel):
    backend: str = "uart"
    port: str | None = None
    baudrate: int = 115200


class ElfConfig(BaseModel):
    path: str | None = None


class DemoProfile(BaseModel):
    name: str
    description: str
    probe: ProbeConfig
    log: LogConfig
    elf: ElfConfig
    suspected_stage: str | None = None


class RuntimeConfig(BaseModel):
    active_profile: str | None = None
    probe: ProbeConfig = Field(default_factory=ProbeConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    elf: ElfConfig = Field(default_factory=ElfConfig)
    suspected_stage: str | None = None

    def apply_profile(self, profile: DemoProfile) -> None:
        self.active_profile = profile.name
        self.probe = profile.probe.model_copy(deep=True)
        self.log = profile.log.model_copy(deep=True)
        self.elf = profile.elf.model_copy(deep=True)
        self.suspected_stage = profile.suspected_stage


def get_builtin_profiles() -> dict[str, DemoProfile]:
    stm32l4_root = Path(r"d:\embed-mcp\实验1 跑马灯(RGB)实验")
    return {
        "stm32l4_atk_led_demo": DemoProfile(
            name="stm32l4_atk_led_demo",
            description=(
                "STM32L496VETx startup-failure demo using a pyOCD-supported probe "
                "(currently validated with ST-Link), UART, "
                "and the modified ATK_LED sample."
            ),
            probe=ProbeConfig(
                backend="pyocd",
                target="stm32l496ve",
            ),
            log=LogConfig(
                backend="uart",
                port="COM3",
                baudrate=115200,
            ),
            elf=ElfConfig(
                path=str(stm32l4_root / "OBJ" / "ATK_LED.axf"),
            ),
            suspected_stage="sensor init",
        )
    }
