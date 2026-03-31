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


class BuildConfig(BaseModel):
    backend: str = "keil_uv4"
    uv4_path: str | None = None
    project_path: str | None = None
    target_name: str | None = None
    build_log_path: str | None = None
    flash_log_path: str | None = None


class DemoProfile(BaseModel):
    name: str
    description: str
    probe: ProbeConfig
    log: LogConfig
    elf: ElfConfig
    build: BuildConfig = Field(default_factory=BuildConfig)
    suspected_stage: str | None = None


class RuntimeConfig(BaseModel):
    active_profile: str | None = None
    probe: ProbeConfig = Field(default_factory=ProbeConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    elf: ElfConfig = Field(default_factory=ElfConfig)
    build: BuildConfig = Field(default_factory=BuildConfig)
    suspected_stage: str | None = None

    def apply_profile(self, profile: DemoProfile) -> None:
        self.active_profile = profile.name
        self.probe = profile.probe.model_copy(deep=True)
        self.log = profile.log.model_copy(deep=True)
        self.elf = profile.elf.model_copy(deep=True)
        self.build = profile.build.model_copy(deep=True)
        self.suspected_stage = profile.suspected_stage


def get_builtin_profiles() -> dict[str, DemoProfile]:
    stm32l4_root = Path(r"d:\embed-mcp\实验1 跑马灯(RGB)实验")
    return {
        "stm32l4_atk_led_demo": DemoProfile(
            name="stm32l4_atk_led_demo",
            description=(
                "STM32L496VETx startup-failure demo using a pyOCD-supported probe "
                "(currently validated with ST-Link), UART, and the generic "
                "cortex_m target for first MVP validation, "
                "and the modified ATK_LED sample."
            ),
            probe=ProbeConfig(
                backend="pyocd",
                target="cortex_m",
            ),
            log=LogConfig(
                backend="uart",
                port="COM3",
                baudrate=115200,
            ),
            elf=ElfConfig(
                path=str(stm32l4_root / "OBJ" / "ATK_LED.axf"),
            ),
            build=BuildConfig(
                backend="keil_uv4",
                uv4_path=r"E:\software\MDK\UV4\UV4.exe",
                project_path=str(stm32l4_root / "USER" / "ATK_LED.uvprojx"),
                target_name="ATK_LED",
                build_log_path=str(stm32l4_root / "OBJ" / "mcudbg_build.log"),
                flash_log_path=str(stm32l4_root / "OBJ" / "mcudbg_flash.log"),
            ),
            suspected_stage="sensor init",
        )
    }
