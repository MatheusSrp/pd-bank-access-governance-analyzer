"""Conversões tolerantes e explícitas de valores vindos de planilhas.

Princípio: valor irreconhecível devolve ``None`` (desconhecido), nunca é tratado como
"falso". As regras decidem o que fazer com o desconhecido (achado de informação insuficiente).
"""
from __future__ import annotations

import math
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

_TRUE = {
    "1", "1.0", "true", "t", "yes", "y", "sim", "s", "x", "ok", "verdadeiro",
    "approved", "aprovado", "aprovada", "ativo", "ativa", "active", "implemented", "implementado",
    "implementada", "compliant", "conforme", "enabled", "habilitado", "habilitada", "vigente",
    "valid", "valido", "valida", "present", "presente", "em_vigor",
}
_FALSE = {
    "0", "0.0", "false", "f", "no", "n", "nao", "falso", "pending", "pendente", "rejected",
    "rejeitado", "rejeitada", "reprovado", "reprovada", "denied", "negado", "negada", "inactive",
    "inativo", "inativa", "not_implemented", "nao_implementado", "nao_implementada", "disabled",
    "desabilitado", "desabilitada", "non_compliant", "nao_conforme", "absent", "ausente",
    "missing", "not_approved", "nao_aprovado", "nao_aprovada", "planned", "planejado",
    "planejada", "in_progress", "em_andamento", "revoked", "revogado", "revogada",
    "blocked", "bloqueado", "bloqueada", "unapproved",
}
_PLACEHOLDERS = {"", "-", "--", "n/a", "na", "n_a", "null", "none", "nulo", "tbd", "a_definir", "nan"}


def normalize(value: object) -> str:
    """minúsculas, sem acentos, não alfanumérico -> '_' (usado em abas, cabeçalhos e comparações)."""
    text = unicodedata.normalize("NFKD", str(value if value is not None else "")).lower().strip()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def is_blank(value: object) -> bool:
    """Vazio ou marcador de ausência ('N/A', '-', 'null'...)."""
    if value is None:
        return True
    return str(value).strip().lower().replace(" ", "_") in _PLACEHOLDERS


def parse_bool(value: object) -> bool | None:
    """True/False quando o valor é reconhecido; None quando ausente ou desconhecido."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return True if value == 1 else False if value == 0 else None
    if is_blank(value):
        return None
    for key in (str(value).strip().lower(), normalize(value)):
        if key in _TRUE:
            return True
        if key in _FALSE:
            return False
    return None


def parse_number(value: object) -> float | None:
    """Número finito; aceita '12', '12.5', '12,5'. Rejeita texto com unidade, NaN e inf."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    text = str(value).strip()
    if not re.fullmatch(r"[-+]?\d+(?:[.,]\d+)?", text):
        return None
    return float(text.replace(",", "."))


def parse_date(value: object) -> date | None:
    """date/datetime, ISO 'AAAA-MM-DD[...]' ou brasileiro 'DD/MM/AAAA'. Inválido -> None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None
    text = str(value).strip()
    for pattern, order in ((r"(\d{4})-(\d{2})-(\d{2})(?:[T ].*)?", "ymd"), (r"(\d{2})/(\d{2})/(\d{4})(?:\s.*)?", "dmy")):
        m = re.fullmatch(pattern, text)
        if m:
            a, b, c = (int(g) for g in m.groups())
            y, mth, d = (a, b, c) if order == "ymd" else (c, b, a)
            try:
                return date(y, mth, d)
            except ValueError:
                return None
    return None


def today_local(tz_name: str = "America/Sao_Paulo") -> date:
    """Data de referência. Usa o fuso de Brasília (fallback UTC-3 se tzdata ausente)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz_name)).date()
    except Exception:  # noqa: BLE001 - tzdata pode não existir em imagens slim
        return datetime.now(timezone(timedelta(hours=-3))).date()
