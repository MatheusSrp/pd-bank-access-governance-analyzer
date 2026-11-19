"""Motor determinístico das regras R01–R09 (v0.4.0, alinhado ao dataset oficial v2.0).

Princípios:
* Valor desconhecido nunca vira "violação" nem "conforme": gera achado ``insufficient_information``.
* Todo achado carrega ``source_sheet``/``source_row`` (rastreabilidade até a linha original),
  ``subject_id``/``related_id`` (para cruzar com exceções e casos de teste) e ``finding_type``
  (vocabulário de ``casos_teste_publicos.expected_category``).
* ``coverage`` informa, por regra, se foi avaliada e por que foi pulada (sem "limpo" falso).
* Data de referência: parâmetro explícito > ``dataset_info.data_referencia`` > data de hoje.
* Exceções (aba ``excecoes``) valem para (subject_id [+ resource_or_asset_id]) com status ativo,
  aprovador informado e vigência válida; não há curinga. A planilha não traz rule_id.

POLÍTICAS ASSUMIDAS (o dataset não as define; ver docs/v0.4.0-relatorio.md, "pendências"):
  A1 severidade de acesso fora do baseline por permissão/criticidade do recurso (``_access_severity``);
  A2 matriz de controles de IA exigidos por nível de impacto (``AI_REQUIRED``);
  A3 autonomia máxima de IA: ``Executar`` é excessivo em impacto Crítico, e em Alto sem revisão humana obrigatória;
  A4 "conflito funcional" de SoD: quem recebe permissão de escrita do baseline de um papel também exerce esse papel.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from .importer import ROW_META
from .schema import CLASSIFICATION_ORDER, SHEET_ALIASES, base_sheet_key, get
from .values import is_blank, normalize, parse_bool, parse_date, parse_number, today_local

RULE_IDS = ("R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09")
RULE_TITLES = {
    "R01": "Acesso fora do baseline RBAC", "R02": "Conflito de segregação de funções (SoD)",
    "R03": "Ativo sem classificação/proprietário", "R04": "Compartilhamento/retenção fora da política",
    "R05": "Caso de IA sem controles/fontes aprovadas", "R06": "Autonomia de IA acima do limite",
    "R07": "Acesso remanescente de usuário inativo/desligado", "R08": "Acesso temporário vencido",
    "R09": "Revisão de acesso pendente/vencida/reprovada",
}
SEV_ORDER = ("low", "medium", "high", "critical")
SOD_SEVERITY = {"critico": "critical", "alto": "high", "medio": "medium", "baixo": "low"}
IMPACT_SEVERITY = {"baixo": "low", "medio": "medium", "alto": "high", "critico": "critical"}
IMPACT_ORDER = {"baixo": 0, "medio": 1, "alto": 2, "critico": 3}
ACTION_LEVELS = {"recomendar", "executar"}
INACTIVE_STATES = {"desligado", "desligada", "inactive", "inativo", "inativa", "terminated", "demitido", "offboarded"}
LEAVE_STATES = {"licenca", "afastado", "afastada", "leave"}
WRITE_PERMS = {"create", "write", "admin", "approve", "execute"}
MODE_RANK = {"jit": 1, "temporario": 2, "permanente": 3}
TIMED_MODES = {"jit", "temporario"}
# A2 — controles exigidos por impacto (chave do campo -> rótulo). logging só a partir de impacto Médio.
AI_REQUIRED_ALWAYS = (("input_validation", "validação de entrada"), ("output_validation", "validação de saída"),
                      ("prompt_protection", "proteção contra prompt injection"))
AI_LOGGING_MIN_IMPACT = "medio"


@dataclass
class Row:
    sheet: str
    number: int
    d: dict


@dataclass
class AnalysisOutput:
    findings: list
    coverage: dict
    reference_date: str
    reference_source: str = "parametro"


def _fmt(row: Row) -> str:
    body = {k: v for k, v in row.d.items() if not k.startswith("__")}
    text = json.dumps(body, ensure_ascii=False, default=str)
    return f"[{row.sheet}, linha {row.number}] {text[:500]}{'…' if len(text) > 500 else ''}"


def _low(value) -> str:
    return str(value).strip().lower() if value is not None else ""


def _n(value) -> str:
    return normalize(value) if value is not None else ""


def _max_sev(*sevs: str) -> str:
    return max(sevs, key=SEV_ORDER.index)


def _bump(sev: str) -> str:
    return SEV_ORDER[min(SEV_ORDER.index(sev) + 1, len(SEV_ORDER) - 1)]


def _access_severity(perm: str, resource: Row | None) -> str:
    """A1 — Admin = crítico; escrita/aprovação = alto (crítico em recurso crítico); leitura = médio/baixo."""
    p = _n(perm)
    crit = _n(get(resource.d, "criticality", default="")) if resource else ""
    if p == "admin":
        return "critical"
    if p in WRITE_PERMS:
        return "critical" if crit == "critica" else "high"
    cls = _n(get(resource.d, "classification", default="")) if resource else ""
    return "medium" if crit in ("critica", "alta") or cls == "restrito" else "low"


class Engine:
    def __init__(self, data: dict, today: date | None = None):
        self.data = data if isinstance(data, dict) else {}
        self.reference_source = "parametro"
        if today is None:
            today = self._dataset_reference()
            self.reference_source = "dataset_info.data_referencia" if today else "data_atual"
            today = today or today_local()
        self.today = today
        self.findings: list = []
        self.coverage: dict = {}
        self._exceptions = self._load_exceptions()
        self._cache: dict = {}

    # ------------------------------------------------------------------ tabelas
    def rows(self, key: str) -> list:
        out: list = []
        for alias in SHEET_ALIASES.get(key, (key,)):
            for sheet, rows in self.data.items():
                if base_sheet_key(sheet) != alias or not isinstance(rows, list):
                    continue
                for i, r in enumerate(rows, 1):
                    if isinstance(r, dict):
                        n = r.get(ROW_META)
                        out.append(Row(sheet, n if isinstance(n, int) else i, r))
        return out

    def _dataset_reference(self) -> date | None:
        for r in self.rows("info"):
            if _n(r.d.get("campo")) == "data_referencia":
                return parse_date(r.d.get("valor"))
        return None

    def index(self, key: str, field: str) -> dict:
        """{id_minúsculo: Row} de uma tabela, pela coluna ``field`` (grupo de aliases)."""
        ck = (key, field)
        if ck not in self._cache:
            self._cache[ck] = {_low(get(r.d, field)): r for r in self.rows(key) if get(r.d, field) is not None}
        return self._cache[ck]

    def is_active(self, row: Row) -> bool:
        start, end = parse_date(get(row.d, "valid_from")), parse_date(get(row.d, "valid_until"))
        return (start is None or start <= self.today) and (end is None or end >= self.today)

    # ------------------------------------------------------------------ exceções
    def _load_exceptions(self) -> list:
        """Cada item: dict(subject, target, state, row). ``state``: valid | expired | future | invalid."""
        parsed = []
        for e in self.rows("exceptions"):
            subject = _low(get(e.d, "subject_id"))
            if not subject or subject == "*":
                continue
            target = _low(get(e.d, "exception_target"))
            if target == "*":
                continue
            status_raw, approver = get(e.d, "status"), get(e.d, "approved_by")
            active = parse_bool(status_raw)
            raw_end = get(e.d, "valid_until")
            end = parse_date(raw_end)
            start = parse_date(get(e.d, "valid_from"))
            if active is not True or approver is None or _low(approver) == subject or end is None:
                state = "invalid"   # inativa, sem aprovador, autoaprovada ou sem vigência legível: não suprime
            elif start and start > self.today:
                state = "future"
            elif end < self.today:
                state = "expired"
            else:
                state = "valid"
            parsed.append({"subject": subject, "target": target, "state": state, "row": e})
        return parsed

    def exception_for(self, subject: str, related: str | None):
        found = {}
        for ex in self._exceptions:
            if ex["subject"] != _low(subject):
                continue
            if ex["target"] and ex["target"] != _low(related):
                continue
            found.setdefault(ex["state"], ex)
        for state in ("valid", "expired", "future"):
            if state in found:
                return state, found[state]
        return "none", None

    # ------------------------------------------------------------------ utilidades
    def cover(self, rule: str, checked: int = 0, skipped_reason: str | None = None, **notes):
        entry = self.coverage.setdefault(rule, {"evaluated": False, "records_checked": 0, "reason": None, "notes": []})
        if skipped_reason:
            entry["reason"] = entry["reason"] or skipped_reason
        else:
            entry["evaluated"], entry["reason"] = True, None
            entry["records_checked"] += checked
        for k, v in notes.items():
            entry["notes"].append(f"{k}: {v}")

    def note(self, rule: str, text: str):
        self.coverage.setdefault(rule, {"evaluated": False, "records_checked": 0, "reason": None, "notes": []})["notes"].append(text)

    def add(self, rule, domain, ftype, severity, subject, related, row: Row, evidence, desc, impact, reco,
            status="non_compliant"):
        self.findings.append(dict(
            rule_id=rule, category=domain, finding_type=ftype, severity=severity, object_ref=str(subject),
            subject_id=str(subject), related_id=(str(related) if related is not None else None),
            evidence=f"{_fmt(row)} — {evidence}", description=desc, impact=impact, recommendation=reco,
            status=status, exception_status="none", source_sheet=row.sheet, source_row=row.number))

    def insufficient(self, rule, domain, ftype, subject, related, row, evidence, desc):
        self.add(rule, domain, ftype, "low", subject, related, row, evidence, desc,
                 "O estado real não pode ser confirmado com os dados fornecidos.",
                 "Completar/corrigir o dado de origem e reexecutar a análise; revisão humana necessária.",
                 status="insufficient_information")

    # ------------------------------------------------------------------ execução
    def run(self) -> AnalysisOutput:
        for step in (self.r01, self.r02, self.r03, self.r04, self.r05_r06, self.r07, self.r08, self.r09):
            step()
        counts = {"valid": 0, "expired": 0, "future": 0, "invalid": 0}
        for ex in self._exceptions:
            counts[ex["state"]] += 1
        used = set()
        for f in self.findings:
            state, ex = self.exception_for(f["subject_id"], f["related_id"])
            f["exception_status"] = state
            if ex:
                used.add(ex["row"].number)
            if state == "valid":
                f["status"] = "valid_exception" if f["status"] == "non_compliant" else f["status"]
                f["evidence"] += f" — coberto por exceção aprovada ({ex['row'].sheet}, linha {ex['row'].number})"
        unused = [f"{ex['row'].sheet} linha {ex['row'].number} ({ex['subject'].upper()}{'/' + ex['target'].upper() if ex['target'] else ''}, {ex['state']})"
                  for ex in self._exceptions if ex["row"].number not in used]
        order = {r: i for i, r in enumerate(RULE_IDS)}
        self.findings.sort(key=lambda f: (order[f["rule_id"]], f["source_sheet"], f["source_row"]))
        for r in RULE_IDS:
            self.coverage.setdefault(r, {"evaluated": False, "reason": "não executada", "records_checked": 0, "notes": []})
        self.coverage["EXCEPTIONS"] = {
            "evaluated": True, "reason": None, "records_checked": len(self._exceptions),
            "notes": [f"{k}: {v}" for k, v in counts.items()] +
                     ([f"exceções sem achado associado: {', '.join(unused)}"] if unused else [])}
        self.coverage["META"] = {"evaluated": True, "reason": None, "records_checked": 0,
                                 "notes": [f"reference_date: {self.today.isoformat()} (fonte: {self.reference_source})"]}
        return AnalysisOutput(self.findings, self.coverage, self.today.isoformat(), self.reference_source)

    # ------------------------------------------------------------------ helpers de domínio
    def _roles_by_user(self) -> dict:
        out: dict = {}
        for a in self.rows("role_assignments"):
            u, r = _low(get(a.d, "subject_id")), _low(get(a.d, "role_id"))
            if u and r and self.is_active(a):
                out.setdefault(u, {})[r] = a
        return out

    def _user_grants(self) -> list:
        return [g for g in self.rows("assignments") if _n(get(g.d, "principal_type", default="usuario")) == "usuario"]

    # R01 -------------------------------------------------------------------
    def r01(self):
        baseline, grants, ras = self.rows("baseline"), self.rows("assignments"), self.rows("role_assignments")
        if not baseline:
            return self.cover("R01", skipped_reason="aba de baseline (rbac_baseline) ausente ou vazia")
        if not grants:
            return self.cover("R01", skipped_reason="aba de permissões atuais ausente ou vazia")
        if not ras:
            return self.cover("R01", skipped_reason="aba atribuicoes_papeis ausente: sem papéis não há permissões esperadas")
        base: dict = {}
        for b in baseline:
            key = (_low(get(b.d, "role_id")), _low(get(b.d, "resource_id")), _n(get(b.d, "permission")))
            if all(key):
                base.setdefault(key, set()).add(_n(get(b.d, "expected_access_mode")))
        if not base:
            return self.cover("R01", skipped_reason="baseline sem colunas reconhecíveis (role_id + resource_id + allowed_permission)")
        roles = self._roles_by_user()
        users, resources = self.index("users", "subject_id"), self.index("resources", "resource_id")
        checked = skipped_apps = mode_findings = 0
        for g in grants:
            if _n(get(g.d, "principal_type", default="usuario")) != "usuario":
                skipped_apps += 1
                continue
            who, res, perm = get(g.d, "subject_id"), get(g.d, "resource_id"), get(g.d, "permission")
            if who is None or res is None or perm is None:
                self.insufficient("R01", "Identidade e acesso", "Dado_Incompleto", who or f"{g.sheet}#{g.number}", res, g,
                                  "concessão sem principal, recurso ou permissão", "Concessão incompleta não pode ser comparada ao baseline.")
                continue
            if users and _low(who) not in users:
                self.insufficient("R01", "Identidade e acesso", "Principal_Desconhecido", who, res, g,
                                  f"principal {who} não consta na aba usuarios", "Não há papéis conhecidos para comparar com o baseline.")
                continue
            checked += 1
            held = roles.get(_low(who), {})
            matches = {r: base[(r, _low(res), _n(perm))] for r in held if (r, _low(res), _n(perm)) in base}
            resource = resources.get(_low(res))
            if not matches:
                self.add("R01", "Identidade e acesso", "Excesso_de_Privilegio", _access_severity(perm, resource), who, res, g,
                         f"{perm} em {res} não consta no baseline dos papéis ativos do usuário "
                         f"({', '.join(sorted(r.upper() for r in held)) or 'nenhum papel ativo'}); origem {get(g.d, 'assignment_source')}, "
                         f"modo {get(g.d, 'access_mode')}.",
                         "A permissão efetiva excede o que o baseline RBAC prevê para os papéis atribuídos.",
                         "Acesso não previsto pode permitir alteração, consulta ou operação além da função.",
                         "Remover a concessão ou atualizar o baseline por processo formal; revisar acessos correlatos.")
                continue
            mode, expected = _n(get(g.d, "access_mode")), set().union(*matches.values()) - {""}
            if mode in MODE_RANK and expected and all(e in MODE_RANK for e in expected) and MODE_RANK[mode] > max(MODE_RANK[e] for e in expected):
                mode_findings += 1
                sev = "high" if _n(perm) in ("admin", "approve") else "medium"
                self.add("R01", "Identidade e acesso", "Modo_de_Acesso_Divergente", sev, who, res, g,
                         f"{perm} em {res} é {get(g.d, 'access_mode')}, mas o baseline prevê {', '.join(sorted(expected))}.",
                         "A permissão está dentro do baseline, porém com modo de acesso mais permanente que o previsto.",
                         "Acesso que deveria ser JIT/temporário permanece disponível continuamente.",
                         "Converter para o modo previsto (JIT/temporário) ou formalizar a mudança no baseline.")
        notes = {}
        if skipped_apps:
            notes["permissões de principals do tipo Aplicacao não comparadas (o baseline é por papel de usuário)"] = skipped_apps
        self.cover("R01", checked=checked, **notes)

    # R02 -------------------------------------------------------------------
    def r02(self):
        rules, ras, grants = self.rows("sod"), self.rows("role_assignments"), self._user_grants()
        if not rules:
            return self.cover("R02", skipped_reason="aba de regras SoD ausente ou vazia (conflitos não são inferidos)")
        if not ras and not grants:
            return self.cover("R02", skipped_reason="sem papéis/permissões atribuídos para avaliar")
        roles = self._roles_by_user()
        functional: dict = {}   # A4: papel -> {(recurso, permissão de escrita)} do baseline
        for b in self.rows("baseline"):
            perm = _n(get(b.d, "permission"))
            if perm in WRITE_PERMS and get(b.d, "role_id") and get(b.d, "resource_id"):
                functional.setdefault(_low(get(b.d, "role_id")), set()).add((_low(get(b.d, "resource_id")), perm))
        by_user: dict = {}
        for g in grants:
            by_user.setdefault(_low(get(g.d, "subject_id")), []).append(g)
        resources = self.index("resources", "resource_id")

        def exercises(user: str, role: str):
            if role in roles.get(user, {}):
                a = roles[user][role]
                return f"possui o papel {role.upper()} (atribuicoes_papeis, linha {a.number})", None
            for g in by_user.get(user, []):
                key = (_low(get(g.d, "resource_id")), _n(get(g.d, "permission")))
                if key in functional.get(role, set()):
                    return (f"possui {get(g.d, 'permission')} em {get(g.d, 'resource_id')} ({get(g.d, 'perm_record_id')}, "
                            f"permissoes_atuais linha {g.number}), que corresponde ao baseline funcional de {role.upper()}"), get(g.d, "resource_id")
            return None, None

        checked = 0
        for rule in rules:
            a, b = _low(get(rule.d, "role_a")), _low(get(rule.d, "role_b"))
            if not a or not b or a == b:
                continue
            checked += 1
            sev = SOD_SEVERITY.get(_n(get(rule.d, "severity")), "high")
            for user in sorted(set(roles) | set(by_user)):
                ea, ra_ = exercises(user, a)
                eb, rb_ = exercises(user, b)
                if ea and eb:
                    uid = next((str(get(g.d, "subject_id")) for g in by_user.get(user, [])), None) or \
                        next((str(get(x.d, "subject_id")) for x in roles[user].values()), user.upper())
                    derived = "papéis atribuídos" if not (ra_ or rb_) else "permissões efetivas (conflito funcional derivado do baseline)"
                    self.add("R02", "Segregação de funções", "Conflito_SoD", sev, uid, ra_ or rb_ or get(rule.d, "rule_id"), rule,
                             f"{get(rule.d, 'rule_id')} ({a.upper()} × {b.upper()}): {uid} {ea}; e {eb}. Base: {derived}. "
                             f"Justificativa da regra: {get(rule.d, 'rationale', default='—')}",
                             "Combinação de papéis/funções incompatível conforme regras_sod.",
                             "Uma mesma identidade pode iniciar e aprovar/auditar operações conflitantes.",
                             "Remover um dos acessos ou registrar exceção aprovada com prazo e controles compensatórios.")
        self.cover("R02", checked=checked) if checked else self.cover("R02", skipped_reason="nenhuma regra SoD com par de papéis reconhecível")

    # R03 -------------------------------------------------------------------
    def r03(self):
        assets = self.rows("assets")
        if not assets:
            return self.cover("R03", skipped_reason="aba de ativos de dados ausente ou vazia")
        users, resources = self.index("users", "subject_id"), self.index("resources", "resource_id")
        for a in assets:
            obj = get(a.d, "asset_id", default=f"{a.sheet}#{a.number}")
            res = get(a.d, "resource_id")
            cls, owner = get(a.d, "classification"), get(a.d, "owner")
            if owner is None:
                self.add("R03", "Governança de dados", "Proprietario_Ausente", "high", obj, res, a, "campo owner_id ausente.",
                         "Ativo sem proprietário definido.",
                         "Sem proprietário não há responsável por acesso, retenção e ciclo de vida do dado.",
                         "Atribuir proprietário no catálogo de ativos.")
            elif users and _low(owner) not in users:
                self.insufficient("R03", "Governança de dados", "Proprietario_Desconhecido", obj, res, a,
                                  f"owner_id {owner} não consta em usuarios", "Proprietário informado não existe no cadastro de usuários.")
            elif users and _n(get(users[_low(owner)].d, "status")) in INACTIVE_STATES:
                self.add("R03", "Governança de dados", "Proprietario_Inativo", "high", obj, res, a, f"proprietário {owner} está desligado.",
                         "Ativo cujo proprietário não está mais ativo.", "Ninguém responde pelo ativo.", "Reatribuir o proprietário.")
            if cls is None:
                self.add("R03", "Governança de dados", "Classificacao_Ausente", "high", obj, res, a, "campo classification ausente.",
                         "Ativo sem classificação.", "Sem classificação, controles de proteção e acesso podem ser inadequados.",
                         "Classificar o ativo conforme a política de dados.")
            elif _n(cls) not in CLASSIFICATION_ORDER:
                self.insufficient("R03", "Governança de dados", "Classificacao_Desconhecida", obj, res, a,
                                  f"classificação {cls!r} fora da taxonomia (Publico/Interno/Confidencial/Restrito)", "Classificação não reconhecida.")
            else:
                rc = _n(get(resources[_low(res)].d, "classification")) if res and _low(res) in resources else ""
                if rc in CLASSIFICATION_ORDER and CLASSIFICATION_ORDER[_n(cls)] < CLASSIFICATION_ORDER[rc]:
                    self.add("R03", "Governança de dados", "Classificacao_Divergente", "medium", obj, res, a,
                             f"ativo classificado como {cls}, mas o recurso {res} é {resources[_low(res)].d.get('classification')}.",
                             "Classificação do ativo menos restritiva que a do recurso que o hospeda.",
                             "Controles aplicados ao ativo podem ser mais frouxos que os do recurso.",
                             "Revisar a classificação do ativo ou do recurso.")
                if _n(get(a.d, "has_credentials")) == "sim" and CLASSIFICATION_ORDER[_n(cls)] < CLASSIFICATION_ORDER["restrito"]:
                    self.add("R03", "Governança de dados", "Classificacao_Divergente", "high", obj, res, a,
                             f"ativo contém credenciais e está classificado como {cls}.",
                             "Ativo com credenciais abaixo da classificação Restrito.", "Segredos tratados como dado comum.",
                             "Reclassificar como Restrito.")
        self.cover("R03", checked=len(assets))

    # R04 -------------------------------------------------------------------
    def r04(self):
        sharing, retention, assets = self.rows("sharing"), self.rows("retention"), self.index("assets", "asset_id")
        if not sharing and not retention:
            return self.cover("R04", skipped_reason="abas de compartilhamento e retenção ausentes ou vazias")
        base_sev = {"restrito": "critical", "confidencial": "high", "interno": "medium", "publico": "low"}
        for e in sharing:
            sid, aid = get(e.d, "sharing_id", default=f"{e.sheet}#{e.number}"), get(e.d, "asset_id")
            asset = assets.get(_low(aid))
            if asset is None:
                self.insufficient("R04", "Compartilhamento", "Ativo_Desconhecido", sid, aid, e,
                                  f"ativo {aid} não consta em ativos_dados", "Não é possível classificar o dado compartilhado.")
                continue
            cls = _n(get(asset.d, "classification"))
            approved = parse_bool(get(e.d, "destination_approved"))
            minimal, protected = parse_bool(get(e.d, "minimum_data_only")), parse_bool(get(e.d, "protected"))
            if approved is None:
                self.insufficient("R04", "Compartilhamento", "Destino_Indefinido", sid, aid, e,
                                  f"destination_approved não interpretável: {get(e.d, 'destination_approved')!r}", "Aprovação do destino desconhecida.")
                continue
            weak = [x for x, v in (("sem minimização", minimal), ("sem proteção", protected)) if v is False]
            ctx = f"ativo {aid} ({get(asset.d, 'classification', default='sem classificação')}); destino {get(e.d, 'destination')}; destinatário {get(e.d, 'recipient_type')}"
            if approved is False:
                sev = base_sev.get(cls, "high")
                if weak or _n(get(asset.d, "has_credentials")) == "sim":
                    sev = _bump(sev)
                self.add("R04", "Compartilhamento", "Destino_Nao_Aprovado", sev, sid, aid, e,
                         f"{ctx}: destino NÃO aprovado" + (f"; {', '.join(weak)}" if weak else "") + ".",
                         "Compartilhamento para destino não aprovado.",
                         "Exposição indevida de dados e violação de política interna.",
                         "Validar necessidade e base autorizadora; revogar o compartilhamento e tratar o destino.")
            elif weak:
                self.add("R04", "Compartilhamento", "Protecao_Insuficiente", "high" if cls == "restrito" else "medium", sid, aid, e,
                         f"{ctx}: destino aprovado, porém {', '.join(weak)}.",
                         "Compartilhamento em destino aprovado sem minimização e/ou proteção.",
                         "Mais dados que o necessário ou dados desprotegidos podem ser expostos ao destinatário.",
                         "Aplicar minimização e proteção (criptografia/mascaramento) antes do envio.")
        covered = set()
        for p in retention:
            aid = get(p.d, "asset_id", default=f"{p.sheet}#{p.number}")
            covered.add(_low(aid))
            days = parse_number(get(p.d, "retention_days"))
            missing = [lbl for lbl, k in (("start_event", "start_event"), ("final_action", "final_action"),
                                          ("evidence_required", "evidence_required")) if get(p.d, k) is None]
            if days is None or days <= 0:
                missing.append("retention_days")
            if "incompleta" in _n(get(p.d, "policy_status", default="")) or missing:
                self.add("R04", "Retenção", "Retencao_Ausente", "high", aid, get(p.d, "policy_id"), p,
                         "política incompleta: " + (", ".join(missing) or "policy_status indica incompleta") + ".",
                         "Política de retenção incompleta (sem prazo, evento inicial, ação final ou evidência).",
                         "Sem retenção definida o dado pode ser mantido indefinidamente ou descartado sem evidência.",
                         "Definir prazo, evento inicial, ação final e evidência exigida.")
        for key, a in assets.items():
            if retention and key not in covered:
                self.add("R04", "Retenção", "Retencao_Ausente", "high", get(a.d, "asset_id"), None, a, "ativo sem linha em politicas_retencao.",
                         "Ativo sem política de retenção.", "Dado sem prazo de guarda/descarte definido.", "Criar a política de retenção.")
        self.cover("R04", checked=len(sharing) + len(retention))

    # R05 / R06 -------------------------------------------------------------
    def r05_r06(self):
        cases, sources, controls = self.rows("ai"), self.rows("ai_sources"), self.rows("ai_controls")
        if not cases:
            self.cover("R05", skipped_reason="aba de casos de IA ausente ou vazia")
            return self.cover("R06", skipped_reason="aba de casos de IA ausente ou vazia")
        assets = self.index("assets", "asset_id")
        ctrl_by_case, src_by_case = {}, {}
        for c in controls:
            ctrl_by_case.setdefault(_low(get(c.d, "case_id")), []).append(c)
        for s in sources:
            src_by_case.setdefault(_low(get(s.d, "case_id")), []).append(s)
        grants_by_res = {}
        for f in self.findings:      # R01 já executou: usado só como evidência do risco integrado
            if f["rule_id"] == "R01" and f["finding_type"] == "Excesso_de_Privilegio":
                grants_by_res[_low(f["related_id"])] = grants_by_res.get(_low(f["related_id"]), 0) + 1
        for r in cases:
            cid = get(r.d, "case_id", default=f"{r.sheet}#{r.number}")
            action, impact = _n(get(r.d, "action_level")), _n(get(r.d, "impact_level"))
            if action not in ACTION_LEVELS or impact not in IMPACT_ORDER:
                ev = (f"action_level={get(r.d, 'action_level')!r}, impact_level={get(r.d, 'impact_level')!r} fora dos valores esperados "
                      f"(Recomendar/Executar; Baixo/Medio/Alto/Critico); possível deslocamento de colunas na linha de origem.")
                self.insufficient("R06", "Governança de IA", "Dado_Inconsistente", cid, None, r, ev,
                                  "Não foi possível avaliar autonomia e impacto porque os campos não estão nos valores esperados.")
            ctrl = ctrl_by_case.get(_low(cid), [])
            srcs = src_by_case.get(_low(cid), [])
            sev_impact = IMPACT_SEVERITY.get(impact, "medium")
            # --- controles (controles_ia)
            if not ctrl:
                self.insufficient("R05", "Governança de IA", "Controles_Sem_Registro", cid, None, r,
                                  "nenhuma linha em controles_ia para este caso", "Sem registro de controles do caso de IA.")
            for c in ctrl:
                missing, unknown = [], []
                for key, label in AI_REQUIRED_ALWAYS + ((("logging", "logging"),) if IMPACT_ORDER.get(impact, 1) >= IMPACT_ORDER[AI_LOGGING_MIN_IMPACT] else ()):
                    v = parse_bool(get(c.d, key))
                    (missing if v is False else unknown if v is None else []).append(label)
                hr = _n(get(c.d, "human_review"))
                needs_hr = action == "executar" or IMPACT_ORDER.get(impact, 0) >= IMPACT_ORDER["alto"]
                if hr in ("nao", "ausente"):
                    if needs_hr:
                        missing.append("revisão humana")
                elif hr == "amostral":
                    if needs_hr:
                        missing.append("revisão humana obrigatória (hoje apenas amostral)")
                elif hr != "obrigatoria":
                    unknown.append(f"revisão humana ({get(c.d, 'human_review')!r})")
                if missing:
                    self.add("R05", "Governança de IA", "Guardrail_Ausente", sev_impact, cid, None, c,
                             f"impacto {get(r.d, 'impact_level')}, ação {get(r.d, 'action_level')}; controles ausentes/insuficientes: {', '.join(missing)}.",
                             "Caso de IA sem os controles exigidos para o seu nível de impacto.",
                             "Entradas/saídas e ações do modelo podem não ser validadas ou supervisionadas.",
                             "Implementar os controles ausentes antes de ampliar o uso do caso.")
                if unknown:
                    self.insufficient("R05", "Governança de IA", "Controle_Indefinido", cid, None, c,
                                      f"valores não interpretáveis: {', '.join(unknown)}", "Estado de controles de IA desconhecido.")
                priv = _n(get(c.d, "privilege_model"))
                if priv and priv != "privilegio_minimo":
                    self.add("R05", "Governança de IA", "Acesso_Excessivo", _max_sev(sev_impact, "high"), cid, None, c,
                             f"privilege_model = {get(c.d, 'privilege_model')}.", "Caso de IA opera com privilégios acima do mínimo necessário.",
                             "Um comprometimento do modelo herda privilégios excessivos.", "Aplicar privilégio mínimo ao caso de IA.")
            # --- fontes (fontes_dados_ia)
            write_assets, cred_assets, fin_assets = [], [], []
            for s in srcs:
                aid = get(s.d, "asset_id")
                asset = assets.get(_low(aid))
                sens = [lbl for lbl, k in (("pessoais", "has_personal"), ("financeiros", "has_financial"), ("credenciais", "has_credentials"))
                        if asset is not None and _n(get(asset.d, k)) == "sim"]
                if asset is not None and _n(get(asset.d, "has_credentials")) == "sim":
                    cred_assets.append(aid)
                if asset is not None and _n(get(asset.d, "has_financial")) == "sim":
                    fin_assets.append(aid)
                if _n(get(s.d, "access_level")) == "write":
                    write_assets.append(aid)
                approved, minimized = parse_bool(get(s.d, "source_approved")), parse_bool(get(s.d, "minimized"))
                cls = _n(get(asset.d, "classification")) if asset else ""
                label = f"fonte {aid} ({get(asset.d, 'classification', default='?') if asset else 'ativo desconhecido'}; dados {', '.join(sens) or 'sem dado sensível declarado'})"
                if approved is False:
                    self.add("R05", "Governança de IA", "Fonte_Nao_Aprovada", "critical" if cls == "restrito" or "credenciais" in sens else "high",
                             cid, aid, s, f"{label} não aprovada.", "Caso de IA usa fonte de dados sem aprovação.",
                             "Dados sem aprovação podem ser inadequados ou não autorizados para a finalidade.",
                             "Validar e aprovar a fonte, ou removê-la do caso de IA.")
                elif approved is None:
                    self.insufficient("R05", "Governança de IA", "Fonte_Indefinida", cid, aid, s, f"source_approved não interpretável: {get(s.d, 'source_approved')!r}", "Aprovação da fonte desconhecida.")
                if minimized is False:
                    self.add("R05", "Governança de IA", "Fonte_Sem_Minimizacao", "high" if sens and IMPACT_ORDER.get(impact, 0) >= 2 else "medium",
                             cid, aid, s, f"{label} sem minimização.", "Fonte de dados não minimizada para o caso de IA.",
                             "O modelo recebe mais dados do que o necessário.", "Minimizar os campos entregues ao caso de IA.")
            # --- autonomia (R06)
            if action in ACTION_LEVELS and impact in IMPACT_ORDER:
                hr_values = {_n(get(c.d, "human_review")) for c in ctrl}
                extra = (f" Escreve em fontes: {', '.join(write_assets)}." if write_assets else "") + \
                        (f" Dados financeiros: {', '.join(fin_assets)}." if fin_assets else "")
                if action == "executar" and impact == "critico":
                    self.add("R06", "Governança de IA", "Agencia_Excessiva", "critical", cid, None, r,
                             f"ação {get(r.d, 'action_level')} com impacto {get(r.d, 'impact_level')}.{extra}",
                             "Caso de IA executa ações de impacto crítico automaticamente.",
                             "Ações automáticas de alto dano sem limite de autonomia.", "Reduzir a autonomia para recomendação com aprovação humana.")
                elif action == "executar" and impact == "alto" and "obrigatoria" not in hr_values:
                    self.add("R06", "Governança de IA", "Agencia_Excessiva", "high", cid, None, r,
                             f"ação Executar com impacto Alto sem revisão humana obrigatória.{extra}",
                             "Execução automática de alto impacto sem supervisão obrigatória.", "Ações indevidas sem barreira humana.",
                             "Exigir revisão humana obrigatória ou reduzir a autonomia.")
                elif action == "recomendar" and write_assets:
                    self.add("R06", "Governança de IA", "Agencia_Excessiva", "medium", cid, None, r,
                             f"caso apenas recomenda, mas tem escrita em fontes: {', '.join(write_assets)}.",
                             "Permissão de escrita incompatível com o nível de ação declarado.", "O modelo pode alterar dados sem declarar essa autonomia.",
                             "Reduzir o acesso das fontes para leitura.")
            # --- risco integrado (agrega sinais já avaliados, sem criar fato novo)
            excess = any(_n(get(c.d, "privilege_model")) not in ("", "privilegio_minimo") for c in ctrl)
            if impact == "critico" and cred_assets and (excess or write_assets):
                res_ids = [get(assets[_low(a)].d, "resource_id") for a in cred_assets if _low(a) in assets]
                priv = sum(grants_by_res.get(_low(x), 0) for x in res_ids)
                self.add("R05", "Integrado", "Risco_Integrado", "critical", cid, cred_assets[0], r,
                         f"impacto Crítico + fonte com credenciais ({', '.join(cred_assets)}) + "
                         f"{'privilege_model excessivo' if excess else ''}{' e ' if excess and write_assets else ''}{'escrita nas fontes' if write_assets else ''}"
                         + (f"; {priv} concessão(ões) fora do baseline (R01) nos recursos dessas fontes" if priv else "") + ".",
                         "Combinação de IA crítica, credenciais e acesso excessivo.",
                         "Um único comprometimento pode expor segredos e executar ações críticas.",
                         "Bloquear o caso até remover credenciais das fontes e aplicar privilégio mínimo.")
        self.cover("R05", checked=len(cases) + len(sources) + len(controls))
        self.cover("R06", checked=len(cases))

    # R07 -------------------------------------------------------------------
    def r07(self):
        users = self.rows("users")
        if not users:
            return self.cover("R07", skipped_reason="aba de usuários ausente ou vazia")
        grants, ras = self._user_grants(), self.rows("role_assignments")
        if not grants and not ras:
            return self.cover("R07", skipped_reason="sem concessões/atribuições para avaliar")
        inactive, leave = {}, {}
        for u in users:
            uid, st = get(u.d, "subject_id"), _n(get(u.d, "status"))
            if uid is None:
                continue
            (inactive if st in INACTIVE_STATES else leave if st in LEAVE_STATES else {})[_low(uid)] = (str(uid), get(u.d, "status"))
        with_perm = set()
        for g in grants:
            uid = _low(get(g.d, "subject_id"))
            if uid in inactive:
                who, st = inactive[uid]
                perm, res = get(g.d, "permission"), get(g.d, "resource_id")
                with_perm.add(uid)
                self.add("R07", "Identidade e acesso", "Conta_Desligada", "critical" if _n(perm) in WRITE_PERMS else "high", who, res, g,
                         f"usuário {who} com status {st} ainda possui {perm} em {res} ({get(g.d, 'access_mode')}).",
                         "Usuário desligado ainda possui permissão ativa.",
                         "A credencial ou permissão remanescente pode permitir acesso após o encerramento do vínculo.",
                         "Revogar a permissão pelo processo de gestão de identidade e investigar o uso após o desligamento.")
        for a in ras:
            uid = _low(get(a.d, "subject_id"))
            if uid in inactive and uid not in with_perm and self.is_active(a):
                who, st = inactive[uid]
                self.add("R07", "Identidade e acesso", "Conta_Desligada", "high", who, get(a.d, "role_id"), a,
                         f"usuário {who} com status {st} mantém o papel {get(a.d, 'role_id')}.",
                         "Usuário desligado mantém atribuição de papel.", "Papel pode ser reativado ou herdado.", "Remover a atribuição de papel.")
        leave_with = sorted({u for u in leave if any(_low(get(g.d, "subject_id")) == u for g in grants)})
        self.cover("R07", checked=len(grants) + len(ras),
                   **({"usuários em licença com acesso (não tratados como violação por R07; permissões fora do baseline aparecem em R01)":
                       f"{len(leave_with)} ({', '.join(leave[u][0] for u in leave_with)})"} if leave_with else {}))

    # R08 -------------------------------------------------------------------
    def r08(self):
        grants = self.rows("assignments")
        if not grants:
            return self.cover("R08", skipped_reason="aba de permissões atuais ausente ou vazia")
        for g in grants:
            mode = _n(get(g.d, "access_mode"))
            if mode not in TIMED_MODES:
                continue
            who, res, perm = get(g.d, "subject_id", default=f"{g.sheet}#{g.number}"), get(g.d, "resource_id"), get(g.d, "permission")
            raw = get(g.d, "valid_until")
            end = parse_date(raw)
            if raw is None or end is None:
                self.insufficient("R08", "Identidade e acesso", "Expiracao_Indefinida", who, res, g,
                                  f"acesso {get(g.d, 'access_mode')} sem data de expiração legível ({raw!r})",
                                  "Acesso temporário/JIT sem data de término utilizável.")
            elif end < self.today:
                self.add("R08", "Identidade e acesso", "Acesso_Expirado", "high", who, res, g,
                         f"acesso {get(g.d, 'access_mode')} {perm} em {res} expirou em {end.isoformat()} (referência {self.today.isoformat()}); "
                         f"justificativa: {get(g.d, 'justification', default='—')}.",
                         "Acesso temporário permanece registrado após a data de expiração.",
                         "Privilégio temporário pode continuar utilizável além do período autorizado.",
                         "Revogar o acesso ou renová-lo por processo formal.")
        for a in self.rows("role_assignments"):
            if _n(get(a.d, "assignment_type")) == "temporario":
                end = parse_date(get(a.d, "valid_until"))
                if end and end < self.today:
                    self.add("R08", "Identidade e acesso", "Acesso_Expirado", "high", get(a.d, "subject_id"), get(a.d, "role_id"), a,
                             f"atribuição temporária do papel {get(a.d, 'role_id')} terminou em {end.isoformat()}.",
                             "Papel temporário com término vencido.", "Papel temporário pode continuar concedendo acessos.", "Revogar o papel.")
        self.cover("R08", checked=len(grants))

    # R09 -------------------------------------------------------------------
    def r09(self):
        reviews = self.rows("reviews")
        if not reviews:
            return self.cover("R09", skipped_reason="aba de revisões de acesso ausente ou vazia")
        held = {(_low(get(g.d, "subject_id")), _low(get(g.d, "resource_id"))) for g in self.rows("assignments")}
        resources = self.index("resources", "resource_id")
        for rv in reviews:
            who, res = get(rv.d, "subject_id", default=f"{rv.sheet}#{rv.number}"), get(rv.d, "resource_id")
            decision = _n(get(rv.d, "decision"))
            nxt = parse_date(get(rv.d, "next_review"))
            overdue = nxt is not None and nxt < self.today
            crit = _n(get(resources[_low(res)].d, "criticality")) if res and _low(res) in resources else ""
            if decision == "remover" and (_low(who), _low(res)) in held:
                self.add("R09", "Revisão de acesso", "Remocao_Nao_Executada", "high", who, res, rv,
                         f"revisão {get(rv.d, 'review_id')} decidiu Remover ({get(rv.d, 'comment')}), mas a permissão de {who} em {res} continua em permissoes_atuais.",
                         "Decisão de remoção da revisão não foi executada.", "Acesso reprovado pelo revisor continua ativo.", "Executar a remoção e registrar evidência.")
            elif decision == "pendente":
                if overdue:
                    self.add("R09", "Revisão de acesso", "Revisao_Vencida", "high" if crit == "critica" else "medium", who, res, rv,
                             f"revisão {get(rv.d, 'review_id')} pendente; próxima revisão devida em {nxt.isoformat()} (referência {self.today.isoformat()}).",
                             "Revisão de acesso pendente e vencida.", "Acesso sem recertificação no prazo.", "Concluir a revisão com decisão e evidência.")
            elif decision == "manter":
                if overdue:
                    self.add("R09", "Revisão de acesso", "Recertificacao_Vencida", "low", who, res, rv,
                             f"decisão Manter em {get(rv.d, 'review_date')}; a recertificação seguinte venceu em {nxt.isoformat()}.",
                             "Acesso mantido cuja próxima recertificação já venceu.", "Necessidade do acesso não reconfirmada no prazo.",
                             "Agendar e executar a nova recertificação.")
            elif decision != "remover":
                self.insufficient("R09", "Revisão de acesso", "Decisao_Indefinida", who, res, rv,
                                  f"decisão não reconhecida: {get(rv.d, 'decision')!r}", "Decisão da revisão não interpretável.")
        self.cover("R09", checked=len(reviews))


def analyze_full(data: dict, today: date | None = None) -> AnalysisOutput:
    return Engine(data, today).run()


def analyze(data: dict, today: date | None = None) -> list:
    return analyze_full(data, today).findings
