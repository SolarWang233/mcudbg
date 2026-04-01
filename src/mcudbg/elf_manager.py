from __future__ import annotations

from pathlib import Path
from typing import Any

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection


class ElfManager:
    def __init__(self) -> None:
        self._path: Path | None = None
        self._symbols: list[dict[str, Any]] = []

    def load(self, path: str) -> dict[str, Any]:
        file_path = Path(path)
        with file_path.open("rb") as handle:
            elf = ELFFile(handle)
            self._symbols = self._load_symbols(elf)
        self._path = file_path
        return {
            "status": "ok",
            "summary": f"Loaded ELF symbols from {file_path.name}.",
            "symbol_count": len(self._symbols),
        }

    def resolve_address(self, address: int) -> dict[str, Any]:
        best_match = None
        for symbol in self._symbols:
            start = symbol["address"]
            end = start + max(symbol["size"], 1)
            if start <= address < end:
                best_match = symbol
                break
        return {
            "address": hex(address),
            "symbol": None if best_match is None else best_match["name"],
            "source": None,
        }

    def resolve_symbol(self, name: str) -> dict[str, Any]:
        match = next((symbol for symbol in self._symbols if symbol["name"] == name), None)
        return {
            "symbol": name,
            "address": None if match is None else hex(match["address"]),
            "source": None,
        }

    @property
    def is_loaded(self) -> bool:
        return self._path is not None

    def _load_symbols(self, elf: ELFFile) -> list[dict[str, Any]]:
        symbols: list[dict[str, Any]] = []
        for section in elf.iter_sections():
            if not isinstance(section, SymbolTableSection):
                continue
            for symbol in section.iter_symbols():
                if symbol["st_info"]["type"] != "STT_FUNC":
                    continue
                symbols.append(
                    {
                        "name": symbol.name,
                        "address": int(symbol["st_value"]) & ~1,
                        "size": int(symbol["st_size"]),
                    }
                )
        return sorted(symbols, key=lambda item: item["address"])
