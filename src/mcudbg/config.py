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
    return {
        "stm32l4_atk_led_demo": DemoProfile(
            name="stm32l4_atk_led_demo",
            description=(
                "STM32L496VETx startup-failure demo. "
                "Uses pyOCD + ST-Link, UART at 115200, and a Keil UV4 project. "
                "Override paths to match your local setup before use."
            ),
            probe=ProbeConfig(
                backend="pyocd",
                target="stm32l496vetx",
            ),
            log=LogConfig(
                backend="uart",
                port="COM3",           # override with your actual COM port
                baudrate=115200,
            ),
            elf=ElfConfig(
                path=None,             # set to your .axf/.elf path, e.g. "C:/project/OBJ/firmware.axf"
            ),
            build=BuildConfig(
                backend="keil_uv4",
                uv4_path=None,         # e.g. "C:/Keil_v5/UV4/UV4.exe"
                project_path=None,     # e.g. "C:/project/USER/firmware.uvprojx"
                target_name=None,      # Keil target name as shown in the project
            ),
            suspected_stage="sensor init",
        )
    }
