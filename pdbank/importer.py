"""Importação segura de XLSX, CSV e ZIP (com XLSX/CSV).

Todas as rejeições levantam ``ImportFailure`` (mensagem própria para o usuário, HTTP 400).
Cada linha importada recebe ``__row`` (número da linha na origem) para rastreabilidade.
"""
from __future__ import annotations

import csv
import io
import posixpath
import stat
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from .values import normalize

ROW_META = "__row"


class ImportFailure(ValueError):
    """Arquivo rejeitado (inválido, malicioso ou acima dos limites)."""


@dataclass(frozen=True)
class Limits:
    max_zip_entries: int = 50
    max_entry_bytes: int = 100 * 1024 * 1024
    max_total_bytes: int = 200 * 1024 * 1024
    max_ratio: int = 200            # descompactado/compactado, aplicado a entradas > 1 MB
    max_sheets: int = 100
    max_rows_per_sheet: int = 200_000
    max_total_rows: int = 500_000
    max_columns: int = 200
    max_cell_chars: int = 32_767    # limite de célula do Excel


@dataclass
class ImportResult:
    tables: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    sources: list = field(default_factory=list)  # [{file, sheet, rows}]

    def total_rows(self) -> int:
        return sum(len(v) for v in self.tables.values())


# ----------------------------------------------------------------------------- helpers
def safe_filename(name: str) -> str:
    base = posixpath.basename(str(name or "").replace("\\", "/")).strip()
    base = "".join(ch for ch in base if ch.isprintable())
    return (base or "arquivo")[:255]


def _unique_key(tables: dict, key: str, warnings: list, origin: str) -> str:
    if key not in tables:
        return key
    n = 2
    while f"{key}__{n}" in tables:
        n += 1
    new = f"{key}__{n}"
    warnings.append(f"Nome de aba/tabela duplicado '{key}' em {origin}; armazenado como '{new}'.")
    return new


def _clean_cell(value, limits: Limits, warnings: list, ctx: str):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(sep=" ") if value.time() != datetime.min.time() else value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        if len(value) > limits.max_cell_chars:
            warnings.append(f"{ctx}: célula com mais de {limits.max_cell_chars} caracteres foi truncada.")
            return value[: limits.max_cell_chars]
    return value


def _build_header(raw_header, warnings: list, ctx: str, limits: Limits):
    if len(raw_header) > limits.max_columns:
        raise ImportFailure(f"{ctx}: mais de {limits.max_columns} colunas.")
    keys, seen, unnamed = [], {}, 0
    for h in raw_header:
        k = normalize(h)
        if not k:
            keys.append(None)
            if h is not None and str(h).strip():
                unnamed += 1
            continue
        if k in seen:
            seen[k] += 1
            warnings.append(f"{ctx}: cabeçalho duplicado '{k}'; a repetição foi renomeada para '{k}_{seen[k]}'.")
            k = f"{k}_{seen[k]}"
            seen[k] = 1
        else:
            seen[k] = 1
        keys.append(k)
    return keys


def _rows_to_dicts(rows_iter, ctx: str, limits: Limits, warnings: list, start_row: int = 1):
    """Primeira linha não vazia = cabeçalho. Devolve lista de dicts com __row."""
    header, out, extra_warned = None, [], False
    for number, row in enumerate(rows_iter, start_row):
        if header is None:
            if row is None or all(v is None or str(v).strip() == "" for v in row):
                continue
            header = _build_header(row, warnings, ctx, limits)
            if not any(header):
                raise ImportFailure(f"{ctx}: cabeçalho sem nomes de coluna válidos.")
            continue
        if row is None or all(v is None or (isinstance(v, str) and v.strip() == "") for v in row):
            continue
        if len(out) >= limits.max_rows_per_sheet:
            raise ImportFailure(f"{ctx}: mais de {limits.max_rows_per_sheet} linhas de dados.")
        if len(row) > len(header) and not extra_warned and any(v not in (None, "") for v in row[len(header):]):
            warnings.append(f"{ctx}: há linhas com mais células que colunas no cabeçalho; o excedente foi ignorado.")
            extra_warned = True
        rec = {k: _clean_cell(v, limits, warnings, ctx) for k, v in zip(header, row) if k}
        for k in header:
            if k and k not in rec:
                rec[k] = None
        rec[ROW_META] = number
        out.append(rec)
    if header is None:
        warnings.append(f"{ctx}: sem cabeçalho/dados.")
    return out


# ----------------------------------------------------------------------------- CSV
def _decode_csv(data: bytes) -> str:
    if b"\x00" in data[:4096] and not data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise ImportFailure("O arquivo CSV parece binário (contém bytes nulos).")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError as exc:
            raise ImportFailure("CSV UTF-16 inválido.") from exc
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def _detect_delimiter(text: str) -> str:
    lines = [ln for ln in text.splitlines()[:5] if ln.strip() and not ln.lower().startswith("sep=")]
    if not lines:
        return ","
    sample = lines[0]
    counts = {d: sample.count(d) for d in (",", ";", "\t", "|")}
    best = max(counts, key=counts.get)
    return best if counts[best] else ","


def parse_csv(data: bytes, limits: Limits, warnings: list, ctx: str) -> list:
    text = _decode_csv(data)
    if text.lower().startswith("sep=") and "\n" in text:
        text = text.split("\n", 1)[1]
    delimiter = _detect_delimiter(text)
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
        return _rows_to_dicts(reader, ctx, limits, warnings)
    except csv.Error as exc:
        raise ImportFailure(f"{ctx}: CSV malformado ({exc}).") from exc


# ----------------------------------------------------------------------------- ZIP / XLSX
def check_zip_entry(info: zipfile.ZipInfo, limits: Limits) -> str | None:
    """Valida uma entrada. Levanta ImportFailure para perigosas; devolve motivo p/ ignorar."""
    name = info.filename
    norm = name.replace("\\", "/")
    parts = [p for p in norm.split("/") if p]
    if norm.startswith("/") or ".." in parts or (len(norm) > 1 and norm[1] == ":") or "\x00" in name:
        raise ImportFailure(f"Entrada de ZIP com caminho inseguro: {name!r}.")
    if info.flag_bits & 0x1:
        raise ImportFailure(f"Entrada de ZIP criptografada não é suportada: {name!r}.")
    if info.is_dir() or parts[:1] == ["__MACOSX"] or (parts and parts[-1].startswith("._")):
        return "metadado/diretório"
    mode = info.external_attr >> 16
    if mode and stat.S_ISLNK(mode):
        return "link simbólico"
    if info.file_size > limits.max_entry_bytes:
        raise ImportFailure(f"Entrada {name!r} excede {limits.max_entry_bytes // (1024 * 1024)} MB descompactada.")
    if info.file_size > 1024 * 1024 and info.compress_size and info.file_size / info.compress_size > limits.max_ratio:
        raise ImportFailure(f"Entrada {name!r} tem taxa de compressão suspeita (possível zip bomb).")
    return None


def _read_capped(zf: zipfile.ZipFile, info: zipfile.ZipInfo, cap: int) -> bytes:
    with zf.open(info) as fh:
        data = fh.read(cap + 1)  # cabeçalho pode mentir sobre file_size; limita a leitura real
    if len(data) > cap:
        raise ImportFailure(f"Entrada {info.filename!r} excede o limite ao descompactar.")
    return data


def _open_zip(data: bytes, what: str) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ImportFailure(f"{what} corrompido ou não é um arquivo ZIP/OOXML válido.") from exc


def _guard_xlsx(data: bytes, limits: Limits) -> None:
    zf = _open_zip(data, "Arquivo XLSX")
    with zf:
        infos = zf.infolist()
        if len(infos) > limits.max_zip_entries * 20:
            raise ImportFailure("XLSX com número de partes excessivo.")
        names = {i.filename for i in infos}
        if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
            raise ImportFailure("Arquivo não é um XLSX válido (estrutura OOXML ausente).")
        total = 0
        for i in infos:
            if i.flag_bits & 0x1:
                raise ImportFailure("XLSX criptografado/protegido por senha não é suportado.")
            if i.file_size > limits.max_entry_bytes:
                raise ImportFailure("XLSX contém parte descompactada acima do limite.")
            if i.file_size > 1024 * 1024 and i.compress_size and i.file_size / i.compress_size > limits.max_ratio:
                raise ImportFailure("XLSX com taxa de compressão suspeita (possível zip bomb).")
            total += i.file_size
        if total > limits.max_total_bytes:
            raise ImportFailure("XLSX excede o tamanho total descompactado permitido.")


def parse_xlsx(data: bytes, limits: Limits, warnings: list, ctx: str):
    """Devolve [(nome_da_aba, linhas)]."""
    from openpyxl import load_workbook
    _guard_xlsx(data, limits)
    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - openpyxl levanta tipos variados
        raise ImportFailure(f"Não foi possível ler o XLSX: {type(exc).__name__}.") from exc
    out = []
    try:
        if len(wb.worksheets) > limits.max_sheets:
            raise ImportFailure(f"Mais de {limits.max_sheets} abas.")
        for ws in wb.worksheets:
            sheet_ctx = f"{ctx}:{ws.title}"
            try:
                rows = _rows_to_dicts(ws.iter_rows(values_only=True), sheet_ctx, limits, warnings)
            except ImportFailure:
                raise
            except Exception as exc:  # noqa: BLE001
                raise ImportFailure(f"Falha ao ler a aba {ws.title!r}: {type(exc).__name__}.") from exc
            out.append((ws.title, rows))
    finally:
        wb.close()
    return out


def _add_table(result: ImportResult, title: str, rows: list, origin: str, limits: Limits):
    key = normalize(title) or f"sheet_{len(result.tables) + 1}"
    key = _unique_key(result.tables, key, result.warnings, origin)
    if len(result.tables) >= limits.max_sheets:
        raise ImportFailure(f"Mais de {limits.max_sheets} abas/tabelas no total.")
    result.tables[key] = rows
    result.sources.append({"file": origin, "sheet": title, "table": key, "rows": len(rows)})
    if result.total_rows() > limits.max_total_rows:
        raise ImportFailure(f"Mais de {limits.max_total_rows} linhas no total.")


def import_file(filename: str, data: bytes, limits: Limits | None = None) -> ImportResult:
    limits = limits or Limits()
    name = safe_filename(filename)
    ext = Path(name).suffix.lower()
    result = ImportResult()
    if not data:
        raise ImportFailure("Arquivo vazio.")
    if ext == ".xlsx":
        for title, rows in parse_xlsx(data, limits, result.warnings, name):
            _add_table(result, title, rows, name, limits)
    elif ext == ".csv":
        _add_table(result, Path(name).stem, parse_csv(data, limits, result.warnings, name), name, limits)
    elif ext == ".zip":
        _import_zip(name, data, limits, result)
    elif ext in (".xls", ".xlsm", ".ods"):
        raise ImportFailure(f"Formato {ext} não suportado; salve como .xlsx ou .csv.")
    else:
        raise ImportFailure("Formato não suportado. Envie XLSX, CSV ou ZIP com arquivos XLSX/CSV.")
    if not result.tables:
        raise ImportFailure("Nenhuma planilha ou tabela CSV legível foi encontrada.")
    return result


def _import_zip(name: str, data: bytes, limits: Limits, result: ImportResult):
    zf = _open_zip(data, "Arquivo ZIP")
    with zf:
        infos = zf.infolist()
        if len(infos) > limits.max_zip_entries:
            raise ImportFailure(f"ZIP com mais de {limits.max_zip_entries} entradas.")
        total, used = 0, 0
        for info in infos:
            skip = check_zip_entry(info, limits)
            if skip:
                continue
            total += info.file_size
            if total > limits.max_total_bytes:
                raise ImportFailure("ZIP excede o tamanho total descompactado permitido.")
            member = posixpath.basename(info.filename.replace("\\", "/"))
            ext = Path(member).suffix.lower()
            if ext not in (".csv", ".xlsx"):
                result.warnings.append(f"Entrada {info.filename!r} ignorada (tipo não suportado: {ext or 'sem extensão'}).")
                continue
            content = _read_capped(zf, info, limits.max_entry_bytes)
            origin = f"{name}/{info.filename}"
            used += 1
            if ext == ".csv":
                rows = parse_csv(content, limits, result.warnings, origin)
                _add_table(result, Path(member).stem, rows, origin, limits)
            else:
                for title, rows in parse_xlsx(content, limits, result.warnings, origin):
                    _add_table(result, title, rows, origin, limits)
        if used == 0:
            raise ImportFailure("O ZIP não contém arquivos .csv ou .xlsx.")
