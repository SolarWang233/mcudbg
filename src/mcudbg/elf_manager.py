from __future__ import annotations

import bisect
from pathlib import Path
from typing import Any

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection


class ElfManager:
    def __init__(self) -> None:
        self._path: Path | None = None
        self._func_symbols: list[dict[str, Any]] = []
        self._all_symbols: list[dict[str, Any]] = []
        self._line_addrs: list[int] = []
        self._line_entries: list[tuple[str, int]] = []

    def load(self, path: str) -> dict[str, Any]:
        file_path = Path(path)
        with file_path.open("rb") as handle:
            elf = ELFFile(handle)
            self._func_symbols, self._all_symbols = self._load_symbols(elf)
            self._line_addrs, self._line_entries = self._build_line_table(elf)
        self._path = file_path
        return {
            "status": "ok",
            "summary": f"Loaded ELF symbols from {file_path.name}.",
            "symbol_count": len(self._func_symbols),
            "line_entry_count": len(self._line_addrs),
        }

    def addr_to_source(self, address: int) -> dict[str, Any]:
        if not self._line_addrs:
            return {"file": None, "line": None}

        idx = bisect.bisect_right(self._line_addrs, address) - 1
        if idx < 0:
            return {"file": None, "line": None}

        filename, line = self._line_entries[idx]
        return {"file": filename, "line": line}

    def resolve_address(self, address: int) -> dict[str, Any]:
        best_match = None
        for symbol in self._func_symbols:
            start = symbol["address"]
            end = start + max(symbol["size"], 1)
            if start <= address < end:
                best_match = symbol
                break

        source_info = self.addr_to_source(address)
        filename = source_info["file"]
        line = source_info["line"]
        return {
            "address": hex(address),
            "symbol": None if best_match is None else best_match["name"],
            "source": f"{filename}:{line}" if filename is not None and line is not None else None,
        }

    def source_to_addrs(self, filename: str, line: int) -> list[int]:
        """Return all addresses in the line table matching the given file:line."""
        matches = []
        for addr, (file, ln) in zip(self._line_addrs, self._line_entries):
            if ln != line:
                continue
            if file == filename or file.endswith("/" + filename) or file.endswith("\\" + filename):
                matches.append(addr)
        return matches

    def resolve_symbol(self, name: str) -> dict[str, Any]:
        match = next((s for s in self._all_symbols if s["name"] == name), None)
        return {
            "symbol": name,
            "address": None if match is None else hex(match["address"]),
            "size": None if match is None else match["size"],
            "source": None,
        }

    @property
    def is_loaded(self) -> bool:
        return self._path is not None

    def _load_symbols(self, elf: ELFFile) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        func_symbols: list[dict[str, Any]] = []
        all_symbols: list[dict[str, Any]] = []
        for section in elf.iter_sections():
            if not isinstance(section, SymbolTableSection):
                continue
            for symbol in section.iter_symbols():
                if not symbol.name:
                    continue
                symbol_type = symbol["st_info"]["type"]
                symbol_info = {
                    "name": symbol.name,
                    "address": int(symbol["st_value"]),
                    "size": int(symbol["st_size"]),
                    "type": symbol_type,
                }
                all_symbols.append(symbol_info)
                if symbol_type != "STT_FUNC":
                    continue
                func_symbols.append(
                    {
                        **symbol_info,
                        "address": symbol_info["address"] & ~1,
                    }
                )
        return (
            sorted(func_symbols, key=lambda item: item["address"]),
            sorted(all_symbols, key=lambda item: item["address"]),
        )

    def _build_line_table(self, elf: ELFFile) -> tuple[list[int], list[tuple[str, int]]]:
        if not elf.has_dwarf_info():
            return [], []

        dwarf = elf.get_dwarf_info()
        rows: list[tuple[int, str, int]] = []
        for cu in dwarf.iter_CUs():
            try:
                lineprog = dwarf.line_program_for_CU(cu)
                if lineprog is None:
                    continue

                file_entries = lineprog["file_entry"]
                for entry in lineprog.get_entries():
                    state = entry.state
                    if state is None or state.end_sequence or state.line is None:
                        continue
                    if state.file < 1 or state.file > len(file_entries):
                        continue

                    raw_name = file_entries[state.file - 1].name
                    filename = (
                        raw_name.decode("utf-8", errors="replace")
                        if isinstance(raw_name, bytes)
                        else str(raw_name)
                    )
                    rows.append((int(state.address), filename, int(state.line)))
            except Exception:
                continue

        rows.sort(key=lambda row: row[0])
        return [row[0] for row in rows], [(row[1], row[2]) for row in rows]
